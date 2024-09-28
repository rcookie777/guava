import json
from .event_models import StandardizedEvent
import requests
import os

class PolymarketAPI:
    def __init__(self):
        self.api_url = "https://gamma-api.polymarket.com/"
        self.headers = {'Accept': 'application/json'}

    def process_markets_to_events(self, markets):
        standardized_events = []
        for data in markets:  # Iterate over each market
            source = "Polymarket"
            market_id = data.get('conditionId', None)
            status = 'Active' if data.get('active', False) else 'Inactive'
            headline = data.get('question', None)
            description = data.get('description', None)
            end_date = data.get('endDate', None)
            outcomes = json.loads(data.get('outcomes', '[]'))
            outcome_prices = json.loads(data.get('outcomePrices', '[]'))
            yes_ask = no_ask = None
            for i, outcome in enumerate(outcomes):
                if outcome == "Yes" and i < len(outcome_prices):
                    yes_ask = float(outcome_prices[i]) if outcome_prices[i] else None
                elif outcome == "No" and i < len(outcome_prices):
                    no_ask = float(outcome_prices[i]) if outcome_prices[i] else None
            liquidity = data.get('liquidityNum', None)  # Default to None

            standardized_event = StandardizedEvent(
                        source, market_id, status, headline, description, end_date, yes_ask, no_ask, liquidity
                    )
            standardized_events.append(standardized_event)

        return standardized_events
    
    def fetch_markets(self):
        url = f"{self.api_url}markets?active=true&closed=false"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                print(f"Error fetching data: {response.status_code}")
                
                return
            data = response.json()
            return self.process_markets_to_events(data)
        except Exception as e:
            print(f"Failed to fetch data from {url}: {e}")

    def save_data(self, events, filename='PolyLines.json'):
        storage_folder = os.path.join(os.getcwd(), 'storage')
        os.makedirs(storage_folder, exist_ok=True)
        data_to_save = [event.to_dict() for event in events]
        path = os.path.join(storage_folder, filename)
        with open(path, 'w', encoding='utf-8') as jsonfile:
            json.dump(data_to_save, jsonfile, ensure_ascii=False, indent=4)
        print(f"Saved {len(data_to_save)} events to {path}")

if __name__ == "__main__":
    pollycollector = PolymarketAPI()
    all_data = pollycollector.fetch_markets()
    processed_events = pollycollector.process_markets_to_events(all_data)
    pollycollector.save_data(processed_events)



