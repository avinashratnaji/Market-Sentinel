"""
telegram/bot.py

Low-level Telegram Bot wrapper.

Responsible only for communicating with Telegram.

Author : Market Sentinel
Version : 2.1.0
"""

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from market_sentinel.config.settings import settings
from market_sentinel.utils.logger import logger


class TelegramBot:
    """
    Low-level Telegram Bot wrapper.
    """

    def __init__(self):

        self.bot = Bot(
            token=settings.TELEGRAM_BOT_TOKEN
        )

        self.chat_id = settings.TELEGRAM_CHAT_ID

    async def send_message(
        self,
        message: str,
    ) -> None:
        """
        Send an HTML formatted Telegram message.
        """

        try:

            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )

            logger.success(
                "Telegram message sent successfully."
            )

        except TelegramError as ex:

            logger.exception(
                f"Telegram Error: {ex}"
            )

            raise

    async def send_sticker(
        self,
        sticker_id: str,
    ) -> None:
        """
        Send an animated Telegram sticker.
        """

        try:

            await self.bot.send_sticker(
                chat_id=self.chat_id,
                sticker=sticker_id,
            )

            logger.success(
                "Telegram sticker sent successfully."
            )

        except TelegramError as ex:

            logger.exception(
                f"Telegram Sticker Error: {ex}"
            )

            raise