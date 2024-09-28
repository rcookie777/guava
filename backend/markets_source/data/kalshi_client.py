import requests
import json
import os
from dotenv import load_dotenv
from .event_models import StandardizedEvent
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import math

class KalshiClient:
    def __init__(self):
        self.api_url = "https://trading-api.kalshi.com/trade-api/v2/events"
        self.params = {"limit": 200, "status": "open", "with_nested_markets": "true"}
        self.headers = {'Accept': 'application/json'}
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def login(self, email, password):
        response = requests.post(
            'https://trading-api.kalshi.com/trade-api/v2/login',
            headers={'accept': 'application/json', 'content-type': 'application/json'},
            json={"email": email, "password": password}
        )
        return response.json()["token"]

    def fetch_markets(self):
        all_data = []
        next_cursor = None
        while True:
            if next_cursor:
                self.params["cursor"] = next_cursor
            response = self.session.get(self.api_url, params=self.params)
            if response.status_code != 200:
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
            # Assuming event is always a dictionary
            title = event.get('title', '')
            for market in event.get('markets', []):
                market_id = market['ticker']
                status = 'Active' if market['status'] == 'active' else 'Inactive'
                subtitle = market.get('subtitle', '')
                headline = f"{title} {subtitle}".strip()
                description = market.get('rules_primary')
                end_date = market.get('close_time')
                yes_ask = market.get('yes_ask') / 100  # Convert to percentage
                no_ask = 1 - (market.get('yes_bid', 0) / 100)  # Convert to percentage
                liquidity = market.get('liquidity', 0)
                
                standardized_event = StandardizedEvent(
                    "Kalshi", market_id, status, headline, description, end_date, yes_ask, no_ask, liquidity
                )
                standardized_events.append(standardized_event)
        return standardized_events


    def save_data(self, events, filename='KalshiLines.json'):
        folder_path = os.path.join(os.getcwd(), 'storage')
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump([event.to_dict() for event in events], jsonfile, ensure_ascii=False, indent=4)
        print(f"Data saved: {len(events)} events to {file_path}")

        
    def get_event_by_ticker(self, event_ticker):
        try:
            url = f"https://trading-api.kalshi.com/trade-api/v2/events/{event_ticker}"
            headers = {"accept": "application/json"}
            response = requests.get(url, headers=headers).json()
            #print(json.dumps(response, indent=4))
            markets = response.get('markets', [])
            tickers = [market['ticker'] for market in markets if 'ticker' in market]
            return tickers
        
        except Exception as e:
            print("Ticker does not exist.")

    def get_btc_tickers(self):
        months = {1: "JAN", 2: "FEB", 3: "MAR", 4: "APR", 5: "MAY", 6: "JUN", 7: "JUL", 8: "AUG", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC"}
        today = datetime.now()
        ticker = f"BTCD-{today.strftime('%y')}{months[today.month]}{today.strftime('%d')}17"
        print("Generated BTC Ticker:", ticker)
        return self.get_event_by_ticker(ticker)
        
    # Get the BTC market history for the last 6 months, for each day.
    def get_btc_market_history(self):
        months = { 1: "JAN", 2: "FEB", 3: "MAR", 4: "APR", 5: "MAY", 6: "JUN", 7: "JUL", 8: "AUG", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC"}
        tickers = []
        today = datetime.now()
        # Generate tickers for each day in the past 6 months
        for i in range(30):
            day = today - timedelta(days=i)
            ticker = f"BTCD-{day.strftime('%y')}{months[day.month]}{day.strftime('%d')}17"
            tickers.append(ticker)
            print(ticker)
        
        # Make a call to the API for each ticker
        history = {}
        for ticker in tickers:
            print(ticker)
            # Make the param include nested markets false
            params = {"with_nested_markets": False}
            url = f"https://trading-api.kalshi.com/trade-api/v2/events/{ticker}"
            headers = {"accept": "application/json"}
            response = requests.get(url, headers=headers, params=params).json()
            #print(response)
            if 'error' not in response:
                # Pretty print the response
                total_volume = 0
                # Iterate through each market in the 'markets' list of the event
                for market in response['markets']:
                    # Add the volume of each market to the total volume
                    total_volume += market.get('volume', 0)
                #print(total_volume)

                history[ticker] = {"time" : response['markets'][0]["close_time"], "volume": total_volume}
            #print(json.dumps(response, indent=4))
    # Pretty print the history
        #print(json.dumps(history, indent=4))

        # Use matplot lib to graph volume over time for each ticker, using the history dictionary
        

        # Define the x and y values for the plot
        x = [datetime.strptime(history[ticker]["time"], "%Y-%m-%dT%H:%M:%SZ") for ticker in history]
        y = [history[ticker]["volume"] for ticker in history]


        # Create the plot
        plt.figure(figsize=(12, 8))
        plt.plot(x, y, label='Volume', color='blue')
        plt.title('Kalshi 5pm BTC Contracts Volume over the last 30 days')
        plt.xlabel('Time')
        plt.ylabel('Volume')

        # Set the grid for better visibility
        plt.grid(True)

        # Show the legend and plot
        plt.legend()
        plt.show()



        return history
    
    def calculate_fee(self, standard_fee, price, count):
        fees = math.ceil((standard_fee * count * price * (1 - price))*100)/100
        return fees
    
if __name__ == "__main__":
    load_dotenv()
    kalshi_api = KalshiClient()
    kalshi_api.login(os.getenv('KALSHI_EMAIL'), os.getenv('KALSHI_PASSWORD'))
    events = kalshi_api.fetch_markets()
    kalshi_api.save_data(events)
    #kalshi_api.get_btc_tickers()
    #kalshi_api.get_btc_market_history()