import asyncio
from data.kalshi_client import KalshiClient
from data.polymarket_api import PolymarketAPI
from data.predictit_api import PredictItAPI
from arbitrage.arbitrager import Arbitrager
from embeddings.similarity import EventMatcher


async def main():
    kalshicollector = KalshiClient()
    all_data = kalshicollector.fetch_markets()
    # No need to call process_markets_to_events again
    kalshicollector.save_data(all_data)

    pollycollector = PolymarketAPI()
    all_data = pollycollector.fetch_markets()
    pollycollector.save_data(all_data)

    predictitcollector = PredictItAPI()
    all_data = predictitcollector.fetch_markets()
    predictitcollector.save_data(all_data)

    matcher = EventMatcher()
    await matcher.match_events()



if __name__ == "__main__":
    asyncio.run(main())
