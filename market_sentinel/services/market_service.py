from market_sentinel.collectors.yahoo.collector import YahooCollector
from market_sentinel.repositories.market_data_repository import MarketDataRepository
from market_sentinel.services.symbol_resolver import SymbolResolver
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

    def latest(self):
        logger.info("Fetching latest market data...")
        records = self.repository.get_latest_snapshot()
        return records

    def history(self, symbol: str, limit: int = 20):
        symbol = SymbolResolver.resolve(symbol)
        logger.info(f"Fetching history for {symbol}...")
        return self.repository.get_history(
            symbol=symbol,
            limit=limit,
        )

    def statistics(self, symbol: str):
        symbol = SymbolResolver.resolve(symbol)
        logger.info(f"Fetching statistics for {symbol}...")
        stats = self.repository.get_statistics(symbol)
        latest = self.repository.get_latest_by_symbol(symbol)
        return symbol, latest, stats