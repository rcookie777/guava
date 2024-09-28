import asyncio
import json
import websockets
import os
from dotenv import load_dotenv
from .kalshi_client import KalshiClient
import re


class KalshiDataFeed:
    def __init__(self, kalshi_client, token, market_tickers):
        self.kalshi_client = kalshi_client
        self.token = token
        self.market_tickers = market_tickers
        self.books = {}
        self.lock = asyncio.Lock()

    async def update_or_set_book(self, market_ticker, snapshot):
        async with self.lock:
            print(f"Snapshot: {snapshot}")

            # Extract 'yes bids' and 'no bids' from the snapshot
            yes_bids = {level[0]: level[1] for level in snapshot.get('yes', [])}
            no_bids = {level[0]: level[1] for level in snapshot.get('no', [])}

            # Calculate 'yes asks' from 'no bids'
            yes_asks = {100 - price: qty for price, qty in no_bids.items()}
            #print(f"Yes Asks: {yes_asks}")

            # Calculate 'no asks' from 'yes bids'
            no_asks = {100 - price: qty for price, qty in yes_bids.items()}
            #print(f"No Asks: {no_asks}")

            # Extract the strike price from the market ticker
            parts = market_ticker.split('-')
            # Select the last part of the market ticker as the strike price remove any non-numeric characters other than the decimal point
            strike_price = re.sub(r'[^\d.]', '', parts[-1])

            # Convert the strike price to an integer
            strike_price = float(strike_price)

            # Update the book dictionary for the market ticker
            self.books[market_ticker] = {
                "source": "Kalshi",
                "strike_price": strike_price,
                "yes_ask": yes_asks,
                "no_ask": no_asks
            }



    async def apply_delta(self, market_ticker, price, delta, side):
        async with self.lock:
            book = self.books.get(market_ticker, {})
            #print(f"Book: {book}")

            # Determine the appropriate side for the delta update
            if side == 'no':
                # Update 'yes ask' (inverse of 'no bid')
                yes_ask_price = 100 - price
                current_yes_ask_qty = book.get('yes_ask', {}).get(yes_ask_price, 0)
                new_yes_ask_qty = current_yes_ask_qty + delta
                if new_yes_ask_qty > 0:
                    book['yes_ask'][yes_ask_price] = new_yes_ask_qty
                else:
                    book['yes_ask'].pop(yes_ask_price, None)
            
            elif side == 'yes':
                # Update 'no ask' (inverse of 'yes bid')
                no_ask_price = 100 - price
                current_no_ask_qty = book.get('no_ask', {}).get(no_ask_price, 0)
                new_no_ask_qty = current_no_ask_qty + delta
                if new_no_ask_qty > 0:
                    book['no_ask'][no_ask_price] = new_no_ask_qty
                else:
                    book['no_ask'].pop(no_ask_price, None)

            # Save the updated book back to the books dictionary
            self.books[market_ticker] = book
            #print(f"Updated book for {market_ticker}: Yes Asks - {book['yes_ask']}, No Asks - {book['no_ask']}")






    async def get_books(self):
        async with self.lock:
            return self.books.copy()

    async def manage_orderbook(self):
        uri = "wss://trading-api.kalshi.com/trade-api/ws/v2"
        while True:
            try:
                async with websockets.connect(uri, extra_headers={"Authorization": f"Bearer {self.token}"}) as websocket:
                    await websocket.send(json.dumps({
                        "id": 1,
                        "cmd": "subscribe",
                        "params": {
                            "channels": ["orderbook_delta"],
                            "market_tickers": self.market_tickers
                        }
                    }))
                    print("Subscription command sent for market tickers:", self.market_tickers)

                    async for message in websocket:
                        data = json.loads(message)
                        #print("Received message:", data)
                        if data['type'] in ('orderbook_snapshot', 'orderbook_delta'):
                            market_ticker = data['msg'].get('market_ticker')
                            if market_ticker:
                                if data['type'] == 'orderbook_snapshot':
                                    await self.update_or_set_book(market_ticker, data['msg'])
                                elif data['type'] == 'orderbook_delta':
                                    await self.apply_delta(market_ticker, data['msg']['price'], data['msg']['delta'], data['msg']['side'])
            except Exception as e:
                print(f"Error: {e}, attempting to reconnect...")
                await asyncio.sleep(10)
                
    # Create a book printing loop
    async def print_books(self):
        while True:
            books = await self.get_books()
            for market_ticker, book in books.items():
                print(f"Market Ticker: {market_ticker}")
                print(f"Source: {book['source']}")
                print(f"Strike Price: {book['strike_price']}")
                '''print("Yes Bid:")
                for level, qty in book['yes_bid'].items():
                    print(f"Level: {level}, Quantity: {qty}")
                print("No Bid:")
                for level, qty in book['no_bid'].items():
                    print(f"Level: {level}, Quantity: {qty}")'''
                print("Yes Ask:")
                for level, qty in book['yes_ask'].items():
                    print(f"Level: {level}, Quantity: {qty}")
                print("No Ask:")
                for level, qty in book['no_ask'].items():
                    print(f"Level: {level}, Quantity: {qty}")
                print()
            await asyncio.sleep(3)
        


async def main():
    load_dotenv()
    kalshi_client = KalshiClient()
    token = kalshi_client.login(os.getenv("KALSHI_EMAIL"), os.getenv("KALSHI_PASSWORD"))
    #market_tickers = kalshi_client.get_btc_tickers()
    market_tickers = kalshi_client.get_event_by_ticker("INX-24JUN28")
    #market_tickers += market_tickers2
    data_feed = KalshiDataFeed(kalshi_client, token, market_tickers)

    # Start both the orderbook management and the book printing tasks concurrently
    orderbook_task = asyncio.create_task(data_feed.manage_orderbook())
    print_books_task = asyncio.create_task(data_feed.print_books())

    # Await both tasks - they will run indefinitely
    await asyncio.gather(orderbook_task, print_books_task)

if __name__ == "__main__":
    asyncio.run(main())