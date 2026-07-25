from market_sentinel.collectors.yahoo.collector import YahooCollector
from market_sentinel.repositories.market_data_repository import MarketDataRepository
from market_sentinel.utils.logger import logger
from market_sentinel.database.models.market_data import MarketData as ORMMarketData

class MarketService:

    def __init__(self):

        self.collector = YahooCollector()
        self.repository = MarketDataRepository()

    def collect(self):

        logger.info("Starting market data collection...")

        records = self.collector.collect()

        logger.info(f"Collected {len(records)} market records.")

        saved = self.repository.save_many(records)

        logger.success(f"Saved {saved} records.")

        logger.success("Market collection completed.")