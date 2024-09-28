import asyncio
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
import openai
import aioredis
import os
from dotenv import load_dotenv
import re

load_dotenv()

class EventMatcher:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))  # Go up one directory
        self.data_sources = {
            'kalshi': os.path.join(base_dir, 'storage', 'KalshiLines.json'),
            'polymarket': os.path.join(base_dir, 'storage', 'PolyLines.json'),
            'predictit': os.path.join(base_dir, 'storage', 'PredictItLines.json')
        }
        self.embeddings = {}
        self.data = {}
        self.redis_client = None

    async def initialize_redis(self):
        print("Initializing Redis client")
        self.redis_client = await aioredis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)

    def load_json(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def sanitize_sentence(self, sentence):
        return re.sub(r'\d+', '<num>', re.sub(r'[^\w\s]', '', re.sub(r'\s+', ' ', sentence.lower()))).strip()

    async def generate_embeddings(self, source_name, data):
        self.data[source_name] = data
        batch_size = 100
        embeddings = []
        descriptions = [self.sanitize_sentence(item['headline']) for item in data]
        market_ids = [item['market_id'] for item in data]
        cache_keys = [f"{source_name}:embedding:{market_id}" for market_id in market_ids]
        cached_embeddings = await self.redis_client.mget(*cache_keys)

        to_fetch = [i for i, emb in enumerate(cached_embeddings) if emb is None]
        fetched_embeddings = []

        for i in range(0, len(to_fetch), batch_size):
            print(f"Generating embeddings for {source_name} - {i + 1}/{len(to_fetch)}")
            batch_indices = to_fetch[i:i + batch_size]
            batch_texts = [descriptions[index] for index in batch_indices]
            response = openai.embeddings.create(model="text-embedding-3-large", input=batch_texts)
            batch_embeddings = [result.embedding for result in response.data]
            fetched_embeddings.extend(batch_embeddings)

            cache_dict = {cache_keys[index]: json.dumps(batch_embeddings[j]) for j, index in enumerate(batch_indices)}
            await self.redis_client.mset(cache_dict)

        for index, emb in zip(to_fetch, fetched_embeddings):
            cached_embeddings[index] = json.dumps(emb)

        self.embeddings[source_name] = np.array([json.loads(emb) for emb in cached_embeddings if isinstance(emb, str)])

    async def match_events(self):
        print("Matching events")
        await self.initialize_redis()
        for source_name, file_path in self.data_sources.items():
            data = self.load_json(file_path)
            await self.generate_embeddings(source_name, data)
        
        results = []
        source_names = list(self.embeddings.keys())
        
        # Compare each source with every other source
        for i in range(len(source_names)):
            for j in range(i + 1, len(source_names)):
                name1, name2 = source_names[i], source_names[j]
                embeddings1, embeddings2 = self.embeddings[name1], self.embeddings[name2]
                matches = self.find_nearest_neighbors(embeddings1, embeddings2)
                match_details = self.store_matches(name1, name2, matches)
                results.extend(match_details)

        # Save match results to a JSON file in a specific directory
        storage_folder = os.path.join(os.getcwd(), 'storage')
        os.makedirs(storage_folder, exist_ok=True)
        file_path = os.path.join(storage_folder, 'match_results.json')
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(results, jsonfile, ensure_ascii=False, indent=4)
        print(f"Saved match results to {file_path}")

        return results

    def store_matches(self, name1, name2, matches):
        match_results = []
        data1 = self.data[name1]
        data2 = self.data[name2]
        for i, match_index in enumerate(matches):
            similarity_score = cosine_similarity([self.embeddings[name1][i]], [self.embeddings[name2][match_index]])[0][0]
            match_results.append({
                f'{name1}_headline': data1[i]['headline'],
                f'{name1}_market_id': data1[i]['market_id'],
                f'{name2}_headline': data2[match_index]['headline'],
                f'{name2}_market_id': data2[match_index]['market_id'],
                'similarity_score': similarity_score
            })

        # Sort results by similarity score in descending order
        match_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return match_results

    def find_nearest_neighbors(self, embeddings1, embeddings2):
        print("Finding nearest neighbors")
        normalized1 = normalize(embeddings1)
        normalized2 = normalize(embeddings2)
        similarity_matrix = cosine_similarity(normalized1, normalized2)
        nearest_neighbors = np.argmax(similarity_matrix, axis=1)
        return nearest_neighbors  # Simplified for demonstration

async def main():
    matcher = EventMatcher()
    match_results = await matcher.match_events()
    if match_results:
        for match in match_results:
            # Process matches as needed
            pass

if __name__ == "__main__":
    asyncio.run(main())