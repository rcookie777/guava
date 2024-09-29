import requests
from .event_models import StandardizedEvent

class PredictItAPI:
    def __init__(self):
        self.api_url = "https://www.predictit.org/api/marketdata/all/"
        self.headers = {'Accept': 'application/json'}

    def process_markets_to_events(self, markets):
        standardized_events = []
        for market in markets:
            market_id = market.get('id')
            main_market_name = market.get('name')
            for contract in market.get('contracts', []):
                headline = f"{main_market_name} - {contract.get('name')}"
                description = contract.get('shortName')
                end_date = contract.get('dateEnd')
                status = contract.get('status')
                yes_ask = contract.get('bestBuyYesCost')
                no_ask = contract.get('bestBuyNoCost')
                liquidity = None  # Assuming liquidity is not provided

                standardized_event = StandardizedEvent(
                    source="PredictIt",
                    market_id=contract.get('id'),
                    status=status,
                    headline=headline,
                    description=description,
                    end_date=end_date,
                    yes_ask=yes_ask,
                    no_ask=no_ask,
                    liquidity=liquidity
                )
                standardized_events.append(standardized_event)
        return standardized_events

    def fetch_markets(self):
        try:
            response = requests.get(self.api_url, headers=self.headers)
            print(f"Fetching data from PredictIt: {response.url}, Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"Error fetching data from PredictIt: {response.status_code}")
                return []
            data = response.json()
            return self.process_markets_to_events(data.get('markets', []))
        except Exception as e:
            print(f"Failed to fetch data from PredictIt: {e}")
            return []

# Remove the standalone execution block
