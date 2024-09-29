import json
from .event_models import StandardizedEvent
import requests

class PolymarketAPI:
    def __init__(self):
        self.api_url = "https://gamma-api.polymarket.com/"
        self.headers = {'Accept': 'application/json'}

    def process_markets_to_events(self, markets):
        standardized_events = []
        for data in markets:
            source = "Polymarket"
            market_id = data.get('conditionId')
            status = 'Active' if data.get('active', False) else 'Inactive'
            headline = data.get('question')
            description = data.get('description')
            end_date = data.get('endDate')
            outcomes = json.loads(data.get('outcomes', '[]'))
            outcome_prices = json.loads(data.get('outcomePrices', '[]'))
            yes_ask = no_ask = None

            for i, outcome in enumerate(outcomes):
                if outcome == "Yes" and i < len(outcome_prices):
                    yes_ask = float(outcome_prices[i]) if outcome_prices[i] else None
                elif outcome == "No" and i < len(outcome_prices):
                    no_ask = float(outcome_prices[i]) if outcome_prices[i] else None

            liquidity = data.get('liquidityNum')

            standardized_event = StandardizedEvent(
                source=source,
                market_id=market_id,
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
        url = f"{self.api_url}markets?active=true&closed=false"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                print(f"Error fetching data from Polymarket: {response.status_code}")
                return []
            data = response.json()
            return self.process_markets_to_events(data)
        except Exception as e:
            print(f"Failed to fetch data from Polymarket: {e}")
            return []

# Remove the standalone execution block
