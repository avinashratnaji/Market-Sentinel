import yfinance as yf
from datetime import datetime
from market_sentinel.models.market_data import MarketData
from market_sentinel.utils import logger

class YahooCollector:

    def __init__(self):
        self.symbols = {
            "^NSEI": ("NIFTY 50", "NSE", "INDEX"),
            "GC=F": ("Gold", "COMEX", "COMMODITY"),
            "SI=F": ("Silver", "COMEX", "COMMODITY"),
            "CL=F": ("Crude Oil", "NYMEX", "COMMODITY"),
            "BTC-USD": ("Bitcoin", "CRYPTO", "CRYPTO"),
            "ETH-USD": ("Ethereum", "CRYPTO", "CRYPTO"),
            "INR=X": ("USD/INR", "FOREX", "FOREX"),
        }

    def collect(self):

        quotes = []

        logger.info("Collecting Yahoo Finance data...")

        for symbol, (name, exchange, asset_type) in self.symbols.items():

            try:

                ticker = yf.Ticker(symbol)

                info = ticker.fast_info

                record = MarketData(
                    symbol=symbol,
                    name=name,
                    exchange=exchange,
                    asset_type=asset_type,
                    price=float(info["lastPrice"]),
                    currency=info.get("currency", ""),
                    collected_at=datetime.utcnow(),
                )

                quotes.append(record)

                logger.success(f"{name:<15} {record.price}")

            except Exception as ex:

                logger.error(f"{name} -> {ex}")

        return quotes