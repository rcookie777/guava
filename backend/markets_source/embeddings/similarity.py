import asyncio
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
import redis.asyncio as redis  # Updated import
import os
from dotenv import load_dotenv
import re
from sentence_transformers import SentenceTransformer
import torch
import concurrent.futures
import gc

# Clear CUDA cache
torch.cuda.empty_cache()

# Check if GPU is available
device = torch.device('cpu') #torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

if torch.cuda.is_available():
    torch.cuda.set_per_process_memory_fraction(0.8, device=0)  # Limit to 80% of GPU memory

load_dotenv()

class EventMatcher:
    def __init__(self):
        # Garbage collection and CUDA cache clearing before model loading
        gc.collect()
        torch.cuda.empty_cache()

        # Determine the base directory dynamically
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Define a single data source for aggregated events
        self.data_sources = {
            'all_markets': os.path.join(base_dir, 'storage', 'AllMarketsEvents.json')
        }
        
        self.embeddings = {}
        self.data = {}
        self.redis_client = None

        # Load NV-Embed-v2 model with Sentence-Transformers
        model_name = 'nvidia/NV-Embed-v2'  # Ensure this is the correct model name
        try:
            self.model = SentenceTransformer(model_name, device=device, trust_remote_code=True)
            self.model.max_seq_length = 32768
            self.model.tokenizer.padding_side = "right"
            print(f"Loaded model '{model_name}' successfully.")
        except Exception as e:
            print(f"Failed to load model '{model_name}': {e}")
            raise e
        
        # Garbage collection and CUDA cache clearing after model loading
        gc.collect()
        torch.cuda.empty_cache()
        
        # Initialize ThreadPoolExecutor for asynchronous encoding
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)  # Adjust as needed

    async def initialize_redis(self):
        print("Initializing Redis client")
        # Updated to use redis.asyncio.from_url
        self.redis_client = redis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)
        try:
            await self.redis_client.ping()
            print("Connected to Redis successfully.")
        except Exception as e:
            print(f"Failed to connect to Redis: {e}")
            raise e

    def load_json(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            print(f"Loaded {len(data)} events from {file_path}")
            return data
        except Exception as e:
            print(f"Error loading JSON file {file_path}: {e}")
            return []

    def sanitize_sentence(self, sentence):
        # Remove non-word characters, replace digits with <num>, and strip whitespace
        sanitized = re.sub(r'\d+', '<num>', re.sub(r'[^\w\s]', '', re.sub(r'\s+', ' ', sentence.lower()))).strip()
        return sanitized

    async def generate_embeddings(self, source_name, data):
        self.data[source_name] = data
        batch_size = 8 # Adjust based on your GPU memory
        descriptions = [self.sanitize_sentence(item['headline']) for item in data]
        market_ids = [item['market_id'] for item in data]
        cache_keys = [f"{source_name}:embedding:{market_id}" for market_id in market_ids]
        cached_embeddings = await self.redis_client.mget(*cache_keys)

        to_fetch = [i for i, emb in enumerate(cached_embeddings) if emb is None]
        fetched_embeddings = []

        if not to_fetch:
            print(f"All embeddings for '{source_name}' are already cached.")
            self.embeddings[source_name] = np.array([json.loads(emb) for emb in cached_embeddings if isinstance(emb, str)])
            return

        # Prepare texts with EOS tokens
        texts_to_encode = [descriptions[i] for i in to_fetch]

        # Encode queries in batches using ThreadPoolExecutor to prevent blocking
        for batch_start in range(0, len(texts_to_encode), batch_size):
            batch_texts = texts_to_encode[batch_start:batch_start + batch_size]
            print(f"Encoding embeddings for '{source_name}' - Batch {batch_start // batch_size + 1}")
            loop = asyncio.get_event_loop()
            batch_embeddings = await loop.run_in_executor(
                self.executor,
                lambda texts: self.model.encode(
                    texts,
                    batch_size=batch_size,
                    normalize_embeddings=True
                ),
                batch_texts
            )
            fetched_embeddings.extend(batch_embeddings)

        # Cache embeddings in Redis
        cache_dict = {}
        for j, index in enumerate(to_fetch):
            cache_key = cache_keys[index]
            emb = fetched_embeddings[j]
            cache_dict[cache_key] = json.dumps(emb.tolist())

        if cache_dict:
            try:
                await self.redis_client.mset(cache_dict)
                print(f"Cached {len(cache_dict)} embeddings for '{source_name}'.")
            except Exception as e:
                print(f"Failed to cache embeddings in Redis: {e}")

        # Update cached_embeddings with newly fetched embeddings
        for idx, emb in zip(to_fetch, fetched_embeddings):
            cached_embeddings[idx] = json.dumps(emb.tolist())

        # Convert to numpy array
        self.embeddings[source_name] = np.array([
            json.loads(emb) for emb in cached_embeddings if isinstance(emb, str)
        ])
        print(f"Generated embeddings for '{source_name}'.")

    def find_similar_events(self, input_headline):
        # Sanitize and generate embedding for the input headline
        sanitized_headline = self.sanitize_sentence(input_headline)
        input_embedding = self.model.encode(sanitized_headline, normalize_embeddings=True)

        # Normalize stored embeddings for cosine similarity computation
        stored_embeddings = normalize(self.embeddings['all_markets'])
        
        # Compute cosine similarity between input and all stored events
        similarity_scores = cosine_similarity([input_embedding], stored_embeddings)[0]

        # Find top 3 most similar events with similarity score >= 0.4
        similar_events = []
        for i, score in enumerate(similarity_scores):
            if score >= 0.4:
                similar_events.append({
                    'headline': self.data['all_markets'][i]['headline'],
                    'market_id': self.data['all_markets'][i]['market_id'],
                    'similarity_score': score
                })

        # Sort the results by similarity score in descending order
        similar_events = sorted(similar_events, key=lambda x: x['similarity_score'], reverse=True)[:3]

        return similar_events

    async def match_events(self):
        print("Matching events")
        await self.initialize_redis()
        for source_name, file_path in self.data_sources.items():
            data = self.load_json(file_path)
            await self.generate_embeddings(source_name, data)

        print("Event embeddings generated and cached.")
        
async def main():
    matcher = EventMatcher()
    await matcher.match_events()

    # Input the headline for which we want to find related events
    headline = "Breaking news tim cook leaves apple"
    
    # Find similar events
    similar_events = matcher.find_similar_events(headline)
    if similar_events:
        print(f"Top 3 similar events for the headline '{headline}':")
        for event in similar_events:
            print(f"Event: {event['headline']}, Market ID: {event['market_id']}, Similarity Score: {event['similarity_score']}")
    else:
        print(f"No similar events found for the headline '{headline}' with a similarity score above 0.4.")

if __name__ == "__main__":
    asyncio.run(main())
