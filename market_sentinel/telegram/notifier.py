"""
telegram/notifier.py

Sends notifications through Telegram.

Author : Market Sentinel
Version : 2.1.0
"""

from __future__ import annotations

import asyncio

from market_sentinel.telegram.bot import TelegramBot
from market_sentinel.utils.logger import logger


class TelegramNotifier:
    """
    Sends Telegram notifications.
    """

    def __init__(self):
        self.bot = TelegramBot()

    async def _notify_async(self, message: str) -> None:
        await self.bot.send_message(message)

    async def _notify_all_async(self, messages: list[str]) -> None:

        for message in messages:
            await self.bot.send_message(message)

    def notify(self, message: str) -> None:
        """
        Send a single Telegram message.
        """

        try:

            asyncio.run(
                self._notify_async(message)
            )

            logger.success("Telegram notification sent.")

        except Exception as ex:
            logger.exception(
                f"Failed to send Telegram message: {ex}"
            )

    def notify_all(self, messages: list[str]) -> None:
        """
        Send multiple Telegram messages.
        """

        if not messages:
            logger.info("No Telegram messages to send.")
            return

        try:

            asyncio.run(
                self._notify_all_async(messages)
            )

            logger.success(
                "All Telegram notifications sent."
            )

        except Exception as ex:
            logger.exception(
                f"Failed to send Telegram messages: {ex}"
            )