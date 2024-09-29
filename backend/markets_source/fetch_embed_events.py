import asyncio
import os
import json
from data.kalshi_client import KalshiClient
from data.polymarket_api import PolymarketAPI
from data.predictit_api import PredictItAPI
from embeddings.similarity import EventMatcher

async def main():
    # Initialize API clients
    kalshi_client = KalshiClient()
    polymarket_client = PolymarketAPI()
    predictit_client = PredictItAPI()
    
    # Fetch events from each API
    print("Fetching Kalshi events...")
    kalshi_events = kalshi_client.fetch_markets()
    print(f"Fetched {len(kalshi_events)} Kalshi events.")

    print("Fetching Polymarket events...")
    polymarket_events = polymarket_client.fetch_markets()
    print(f"Fetched {len(polymarket_events)} Polymarket events.")

    print("Fetching PredictIt events...")
    predictit_events = predictit_client.fetch_markets()
    print(f"Fetched {len(predictit_events)} PredictIt events.")

    # Combine all events into one list
    all_events = kalshi_events + polymarket_events + predictit_events
    print(f"Total events collected: {len(all_events)}")

    # Define the storage path
    storage_folder = os.path.join(os.getcwd(), 'backend\markets_source\storage')
    os.makedirs(storage_folder, exist_ok=True)
    combined_filename = 'AllMarketsEvents.json'
    combined_filepath = os.path.join(storage_folder, combined_filename)

    # Convert all events to dictionaries
    try:
        data_to_save = [event.to_dict() for event in all_events]
    except AttributeError as e:
        print(f"Error converting events to dict: {e}")
        return

    # Save the combined events to a single JSON file
    try:
        with open(combined_filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(data_to_save, jsonfile, ensure_ascii=False, indent=4)
        print(f"Successfully saved {len(data_to_save)} events to {combined_filepath}")
    except Exception as e:
        print(f"Failed to save events: {e}")
        return

''' # Proceed with event matching if necessary
    matcher = EventMatcher()
    await matcher.match_events()'''

if __name__ == "__main__":
    asyncio.run(main())
