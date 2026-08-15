"""
services/morning_brief_service.py

Morning Brief Service.

Author : Market Sentinel
Version : 1.2.0
"""

from market_sentinel.briefs.morning import (
    MorningBriefBuilder,
)

from market_sentinel.config.telegram_stickers import (
    MARKET_STICKERS,
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

        messages = MorningFormatter.format(
            brief
        )

        logger.info(
            "Sending Morning Brief..."
        )

        # ==================================================
        # DETERMINE SENTIMENT
        # ==================================================

        sentiment = (
            brief.market_sentiment
            .strip()
            .lower()
        )

        sticker_id = MARKET_STICKERS.get(
            sentiment
        )

        if sticker_id:

            logger.info(
                f"Sending {sentiment} sentiment sticker..."
            )

        else:

            logger.warning(
                f"No sticker configured for sentiment: "
                f"{brief.market_sentiment}"
            )

        # ==================================================
        # SEND EVERYTHING IN ONE EVENT LOOP
        # ==================================================

        self.notifier.send_brief(
            messages=messages,
            sticker_id=sticker_id,
        )

        logger.success(
            "Morning Brief sent successfully."
        )