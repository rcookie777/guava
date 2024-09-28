import requests
import json
import os
from .event_models import StandardizedEvent

class PredictItAPI:
    def __init__(self):
        self.api_url = "https://www.predictit.org/api/marketdata/all/"  
        self.headers = {'Accept': 'application/json'}

    def fetch_markets(self):  # Fetches events from the API - an event is a collection of markets
        response = requests.get(url=self.api_url, headers=self.headers)
        print(f"Fetching data from {response.url}, status code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error fetching data: {response.status_code}")
            return []

        data = response.json()
        all_data = self.process_markets_to_events(data['markets'])
        return all_data
    
    def process_markets_to_events(self, markets):
        standardized_events = []
        for market in markets:
            market_id = market['id']
            main_market_name = market['name']
            for contract in market['contracts']:
                headline = f"{main_market_name} - {contract['name']}"
                description = contract['shortName']
                end_date = contract['dateEnd']
                status = contract['status']
                yes_ask = contract['bestBuyYesCost']
                no_ask = contract['bestBuyNoCost']
                liquidity = None  # Not provided in your JSON snippet, assumed None
                
                standardized_event = StandardizedEvent(
                    source="PredictIt", market_id=contract['id'], status=status,
                    headline=headline, description=description, end_date=end_date,
                    yes_ask=yes_ask, no_ask=no_ask, liquidity=liquidity
                )
                standardized_events.append(standardized_event)
        return standardized_events

    def save_data(self, events, filename='PredictItLines.json'):
        storage_folder = os.path.join(os.getcwd(), 'storage')
        os.makedirs(storage_folder, exist_ok=True)
        
        data_to_save = [event.to_dict() for event in events]
        filepath = os.path.join(storage_folder, filename)
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(data_to_save, jsonfile, ensure_ascii=False, indent=4)
        print(f"PredictItAPIcollector: {len(data_to_save)} events saved to {filepath}")

if __name__ == "__main__":
    predictitcollector = PredictItAPI()
    all_data = predictitcollector.fetch_markets()
    predictitcollector.save_data(all_data)

