import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.bot_config import BotConfig

logger = logging.getLogger(__name__)


class KafkaEventConsumer:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.consumer = AIOKafkaConsumer(
            BotConfig.SUPPORT_TOPIC,
            bootstrap_servers=BotConfig.KAFKA_HOST,
            group_id="bot-support-events",
            auto_offset_reset="earliest",
            value_deserializer=lambda v: v and v.decode("utf-8"),
        )
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        await self.consumer.start()
        self._task = asyncio.create_task(self._consume_loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.consumer.stop()

    async def _consume_loop(self) -> None:
        async for msg in self.consumer:
            try:
                await self._handle_message(msg.value)
            except Exception:  # noqa: BLE001
                logger.exception("Failed to process kafka message: %s", msg.value)

    async def _handle_message(self, raw_value: str | None) -> None:
        if not raw_value:
            return

        try:
            event = json.loads(raw_value)
        except Exception:  # noqa: BLE001
            logger.warning("Skip malformed kafka payload: %s", raw_value)
            return

        event_type = event.get("event_type")
        if event_type != "telegram_verification_prompt":
            return

        chat_id = event.get("chat_id")
        user_id = event.get("user_id")
        message = event.get("message") or "Подтвердите верификацию аккаунта."

        if not chat_id or not user_id:
            logger.warning("Prompt without chat_id or user_id: %s", event)
            return

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Подтвердить",
                        callback_data=f"verify:{user_id}:approve"
                    ),
                    InlineKeyboardButton(
                        text="❌ Отклонить",
                        callback_data=f"verify:{user_id}:reject"
                    ),
                ]
            ]
        )

        await self.bot.send_message(
            chat_id=chat_id,
            text=message,
            reply_markup=keyboard
        )

