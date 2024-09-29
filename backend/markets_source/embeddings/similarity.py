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

# Check if GPU is available
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

if torch.cuda.is_available():
    torch.cuda.set_per_process_memory_fraction(0.8, device=0)  # Limit to 80% of GPU memory

load_dotenv()

class EventMatcher:
    def __init__(self):
        # Determine the base directory dynamically
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Define a single data source for aggregated events
        self.data_sources = {
            'all_markets': os.path.join(base_dir, 'backend', 'markets_source', 'storage', 'AllMarketsEvents.json')
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

    def add_eos(self, input_examples):
        eos_token = self.model.tokenizer.eos_token if self.model.tokenizer.eos_token else ""
        return [f"{text}{eos_token}" for text in input_examples]

    async def generate_embeddings(self, source_name, data):
        self.data[source_name] = data
        batch_size = 32  # Adjust based on your GPU memory
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
        texts_to_encode = [self.add_eos([descriptions[i]])[0] for i in to_fetch]

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

    def find_nearest_neighbors(self, embeddings1, embeddings2):
        print("Finding nearest neighbors")
        normalized1 = normalize(embeddings1)
        normalized2 = normalize(embeddings2)
        similarity_matrix = cosine_similarity(normalized1, normalized2)
        nearest_neighbors = np.argmax(similarity_matrix, axis=1)
        return nearest_neighbors  # Simplified for demonstration

    def store_matches(self, name1, matches):
        match_results = []
        data1 = self.data[name1]
        data2 = self.data[name1]  # Since there's only one source
        embeddings1 = self.embeddings[name1]
        embeddings2 = self.embeddings[name1]

        for i, match_index in enumerate(matches):
            if i == match_index:
                continue  # Skip self-match
            similarity_score = cosine_similarity([embeddings1[i]], [embeddings2[match_index]])[0][0]
            match_results.append({
                f'{name1}_headline': data1[i]['headline'],
                f'{name1}_market_id': data1[i]['market_id'],
                f'{name1}_matched_headline': data2[match_index]['headline'],
                f'{name1}_matched_market_id': data2[match_index]['market_id'],
                'similarity_score': similarity_score
            })

        # Sort results by similarity score in descending order
        match_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return match_results

    async def match_events(self):
        print("Matching events")
        await self.initialize_redis()
        for source_name, file_path in self.data_sources.items():
            data = self.load_json(file_path)
            await self.generate_embeddings(source_name, data)

        results = []
        source_names = list(self.embeddings.keys())

        # Since there's only one source, perform intra-source matching
        if len(source_names) == 1:
            name1 = source_names[0]
            embeddings1 = self.embeddings[name1]
            embeddings2 = self.embeddings[name1]
            matches = self.find_nearest_neighbors(embeddings1, embeddings2)
            match_details = self.store_matches(name1, matches)
            results.extend(match_details)
        else:
            print("Multiple sources detected. This should not happen with single source configuration.")

        # Save match results to a JSON file in the 'storage' directory
        storage_folder = os.path.join(os.getcwd(), 'storage')
        os.makedirs(storage_folder, exist_ok=True)
        file_path = os.path.join(storage_folder, 'match_results.json')
        try:
            with open(file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(results, jsonfile, ensure_ascii=False, indent=4)
            print(f"Saved match results to {file_path}")
        except Exception as e:
            print(f"Failed to save match results: {e}")

        return results

async def main():
    matcher = EventMatcher()
    match_results = await matcher.match_events()
    if match_results:
        # Example: Print top 10 most similar event pairs
        for match in match_results[:10]:
            print(match)

if __name__ == "__main__":
    asyncio.run(main())
