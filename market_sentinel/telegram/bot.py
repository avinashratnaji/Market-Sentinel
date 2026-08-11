from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError, TimedOut
from telegram.request import HTTPXRequest

from market_sentinel.config.settings import settings
from market_sentinel.utils.logger import logger

import asyncio


class TelegramBot:

    def __init__(self):

        request = HTTPXRequest(

            connect_timeout=30.0,
            read_timeout=30.0,
            write_timeout=30.0,
            pool_timeout=30.0,

        )

        self.bot = Bot(

            token=settings.TELEGRAM_BOT_TOKEN,
            request=request,

        )

        self.chat_id = settings.TELEGRAM_CHAT_ID

    async def send_message(self, message: str) -> None:

        for attempt in range(1, 4):

            try:

                await self.bot.send_message(

                    chat_id=self.chat_id,

                    text=message,

                    parse_mode=ParseMode.HTML,

                    disable_web_page_preview=True,

                )

                logger.success(
                    "Telegram message sent."
                )

                return

            except TimedOut:

                logger.warning(
                    "Telegram timeout. Retry {}/3",
                    attempt,
                )

                await asyncio.sleep(2)

            except TelegramError:

                raise

        raise RuntimeError(
            "Telegram failed after 3 retries."
        )