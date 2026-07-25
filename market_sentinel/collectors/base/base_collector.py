"""
Base Collector Interface
"""

from abc import ABC
from abc import abstractmethod

from market_sentinel.models.market_data import MarketData


class BaseCollector(ABC):
    """
    Base class for all collectors.
    """

    @abstractmethod
    def collect(self) -> list[MarketData]:
        """
        Collect data from a source.

        Returns:
            List[MarketData]
        """
        raise NotImplementedError