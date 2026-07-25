from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from market_sentinel.database import Base


class MarketData(Base):
    """
    Database model for collected market data.
    """

    __tablename__ = "market_data"

    id: Mapped[int] = mapped_column(primary_key=True)

    symbol: Mapped[str] = mapped_column(String(30), index=True)

    name: Mapped[str] = mapped_column(String(100))

    exchange: Mapped[str] = mapped_column(String(20))

    asset_type: Mapped[str] = mapped_column(String(30))

    price: Mapped[Decimal] = mapped_column(Numeric(18, 4))

    currency: Mapped[str] = mapped_column(String(10))

    collected_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True,
    )