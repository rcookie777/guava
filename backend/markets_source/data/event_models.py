import re
class StandardizedEvent:
    def __init__(self, source, market_id, status, headline, description, end_date, yes_ask, no_ask, liquidity):
        self.source = source
        self.market_id = market_id
        self.status = status
        self.headline = headline
        self.description = description
        self.end_date = end_date
        self.yes_ask = yes_ask
        self.no_ask = no_ask
        self.liquidity = liquidity

    def to_dict(self):
        return {
            "source": self.source,
            "market_id": self.market_id,
            "status": self.status,
            "headline": self.headline,
            "description": self.description,
            "end_date": self.end_date,
            "yes_ask": self.yes_ask,
            "no_ask": self.no_ask,
            "liquidity": self.liquidity
        }

      