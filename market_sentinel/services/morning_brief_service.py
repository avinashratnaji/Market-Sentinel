"""
services/morning_brief_service.py

Morning Brief Service.

Author : Market Sentinel
Version : 1.0.0
"""

from market_sentinel.briefs.morning import (
    MorningBriefBuilder,
)

from market_sentinel.telegram.morning import (
    MorningFormatter,
)

from market_sentinel.telegram.notifier import (
    TelegramNotifier,
)

from market_sentinel.utils.logger import logger


class MorningBriefService:
    """
    Builds and sends the Morning Brief.
    """

    def __init__(self):

        self.builder = MorningBriefBuilder()

        self.notifier = TelegramNotifier()

    def send(self) -> None:

        logger.info(
            "Building Morning Brief..."
        )

        brief = self.builder.build()

        logger.success(
            "Morning Brief built."
        )

        message = MorningFormatter.format(
            brief,
        )

        logger.info(
            "Sending Morning Brief..."
        )

        self.notifier.notify(
            message,
        )

        logger.success(
            "Morning Brief sent successfully."
        )