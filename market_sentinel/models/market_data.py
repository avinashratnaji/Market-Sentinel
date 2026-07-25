from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class MarketData:
    symbol: str
    name: str
    exchange: str
    asset_type: str
    price: float
    currency: str
    collected_at: datetime