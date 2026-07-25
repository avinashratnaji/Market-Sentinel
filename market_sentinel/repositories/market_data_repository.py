from sqlalchemy.exc import SQLAlchemyError

from market_sentinel.database.models.market_data import MarketData as ORMMarketData
from market_sentinel.database.session import SessionLocal
from market_sentinel.models.market_data import MarketData
from market_sentinel.utils.logger import logger


class MarketDataRepository:
    """
    Repository for MarketData persistence.
    """

    def save_many(self, records: list[MarketData]) -> int:
        """
        Save multiple market records in a single transaction.
        """

        session = SessionLocal()

        try:

            orm_records = [
                ORMMarketData(
                    symbol=item.symbol,
                    name=item.name,
                    exchange=item.exchange,
                    asset_type=item.asset_type,
                    price=item.price,
                    currency=item.currency,
                    collected_at=item.collected_at,
                )
                for item in records
            ]

            session.add_all(orm_records)
            session.commit()

            logger.success(f"Saved {len(records)} records to PostgreSQL.")

            return len(records)

        except SQLAlchemyError as ex:

            session.rollback()

            logger.exception(ex)

            raise

        finally:

            session.close()