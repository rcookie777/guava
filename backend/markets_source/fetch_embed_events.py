import asyncio
from data.kalshi_client import KalshiClient
from data.polymarket_api import PolymarketAPI
from data.predictit_api import PredictItAPI
#from arbitrage.arbitrager import Arbitrager
from embeddings.similarity import EventMatcher


async def main():
    kalshicollector = KalshiClient()
    try:
        all_data = kalshicollector.fetch_markets()
        kalshicollector.save_data(all_data)
    except Exception as e:
        print(f"Error fetching or saving Kalshi markets: {e}")

    pollycollector = PolymarketAPI()
    try:
        all_data = pollycollector.fetch_markets()
        pollycollector.save_data(all_data)
    except Exception as e:
        print(f"Error fetching or saving Polymarket markets: {e}")

    predictitcollector = PredictItAPI()
    try:
        all_data = predictitcollector.fetch_markets()
        predictitcollector.save_data(all_data)
    except Exception as e:
        print(f"Error fetching or saving PredictIt markets: {e}")

    matcher = EventMatcher()
    try:
        await matcher.match_events()
    except Exception as e:
        print(f"Error matching events: {e}")



if __name__ == "__main__":
    asyncio.run(main())
