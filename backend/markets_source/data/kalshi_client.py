import requests
import json
import os
from dotenv import load_dotenv
from .event_models import StandardizedEvent
from datetime import datetime, timedelta
import math

class KalshiClient:
    def __init__(self):
        self.api_url = "https://trading-api.kalshi.com/trade-api/v2/events"
        self.params = {"limit": 200, "status": "open", "with_nested_markets": "true"}
        self.headers = {'Accept': 'application/json'}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.token = None  # To store the authentication token

    def login(self, email, password):
        response = requests.post(
            'https://trading-api.kalshi.com/trade-api/v2/login',
            headers={'accept': 'application/json', 'content-type': 'application/json'},
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            print("Successfully logged in to Kalshi.")
        else:
            raise Exception(f"Failed to login to Kalshi: {response.status_code} - {response.text}")

    def fetch_markets(self):
        all_data = []
        next_cursor = None
        while True:
            if next_cursor:
                self.params["cursor"] = next_cursor
            response = self.session.get(self.api_url, params=self.params)
            if response.status_code != 200:
                print(f"Error fetching data from Kalshi: {response.status_code}")
                break
            data = response.json()
            all_data.extend(data.get("events", []))
            next_cursor = data.get('cursor', None)
            if not next_cursor:
                break
        return self.process_markets_to_events(all_data)

    def process_markets_to_events(self, events):
        standardized_events = []
        for event in events:
            title = event.get('title', '')
            for market in event.get('markets', []):
                market_id = market.get('ticker', '')
                status = 'Active' if market.get('status', '').lower() == 'active' else 'Inactive'
                subtitle = market.get('subtitle', '')
                headline = f"{title} {subtitle}".strip()
                description = market.get('rules_primary', '')
                end_date = market.get('close_time', '')
                yes_ask = market.get('yes_ask', 0) / 100  # Convert to percentage
                no_ask = 1 - (market.get('yes_bid', 0) / 100)  # Convert to percentage
                liquidity = market.get('liquidity', 0)

                standardized_event = StandardizedEvent(
                    source="Kalshi",
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
