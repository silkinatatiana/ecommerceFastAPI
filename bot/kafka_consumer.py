import asyncio
import json
import logging
from collections import defaultdict
from typing import Any

from aiokafka import AIOKafkaConsumer
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.bot_config import BotConfig
from config import Statuses

logger = logging.getLogger(__name__)


class KafkaEventConsumer:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.consumer = AIOKafkaConsumer(
            BotConfig.VERIFICATED_TOPIC,
            BotConfig.SUPPORT_CHANGE_STATUS_TOPIC,
            bootstrap_servers=BotConfig.KAFKA_HOST,
            group_id="bot-support-events",
            auto_offset_reset="earliest",
            value_deserializer=lambda v: v and v.decode("utf-8"),
        )
        self._task: asyncio.Task | None = None
        self._order_messages: dict[int, list[dict[str, Any]]] = defaultdict(list)

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
        except Exception:
            logger.warning("Skip malformed kafka payload: %s", raw_value)
            return

        event_type = event.get("event_type")
        if event_type == "telegram_verification_prompt":
            await self._handle_verification_prompt(event)
        elif event_type == "order_created_support_enriched":
            await self._handle_order_created(event)
        elif event_type == "order_status_change_result":
            await self._handle_status_change_result(event)

    async def _handle_verification_prompt(self, event: dict[str, Any]) -> None:
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

    def _build_status_keyboard(self, order_id: int, current_status_text: str | None) -> InlineKeyboardMarkup | None:
        if not current_status_text:
            return None

        next_status_key = next(
            (status_key for status_key, prev_status in Statuses.changing_statuses.items()
             if prev_status == current_status_text),
            None
        )

        buttons_row = []

        if next_status_key:
            next_label = getattr(Statuses, next_status_key, next_status_key)
            buttons_row.append(
                InlineKeyboardButton(
                    text=f"🔄{next_label}",
                    callback_data=f"order_status:{order_id}:{next_status_key}"
                )
            )

        if current_status_text == Statuses.DESIGNED:
            buttons_row.append(
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data=f"order_status:{order_id}:CANCELLED"
                )
            )

        if not buttons_row:
            return None

        return InlineKeyboardMarkup(inline_keyboard=[buttons_row])

    @staticmethod
    def _update_status_line(message_text: str | None, status_text: str | None) -> str:
        lines = message_text.splitlines()
        lines[1] = f"Статус: {status_text or '—'}"
        return "\n".join(lines)

    async def _handle_order_created(self, event: dict[str, Any]) -> None:
        order_id = event.get("order_id")
        slug = event.get("slug")
        positions = event.get("positions") or []
        total_sum = event.get("total_sum", 0)
        total_count = event.get("total_count", 0)
        status_text = event.get("status_text") or ""
        chat_ids = event.get("chat_ids") or []

        if not chat_ids:
            logger.warning("No support chat_ids in order_created event: %s", event)
            return

        title = f"Новый заказ #{order_id}" if order_id else f"Новый заказ {slug}"
        lines = [
            title,
            f"Статус: {status_text or '—'}",
            f"Сумма: {total_sum} ₽",
            f"Позиции: {len(positions)}, Кол-во: {total_count}",
            "",
        ]

        for idx, pos in enumerate(positions, start=1):
            name = pos.get('name', '—')
            count = pos.get('count', 0)
            subtotal = pos.get('subtotal', 0)
            lines.append(f"{idx}) {name} x{count} = {subtotal} ₽")

        message_text = "\n".join(lines)

        keyboard_status = self._build_status_keyboard(order_id, status_text)

        for chat_id in chat_ids:
            try:
                sent = await self.bot.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    reply_markup=keyboard_status
                )
                if order_id is not None:
                    self._order_messages.setdefault(order_id, []).append({
                        "chat_id": chat_id,
                        "message_id": sent.message_id,
                        "text": message_text,
                    })
            except Exception:
                logger.exception("Failed to send order notification to chat %s", chat_id)

    async def _handle_status_change_result(self, event: dict[str, Any]) -> None:
        order_id = event.get("order_id")
        success = event.get("success")
        current_status_text = event.get("current_status_text")
        keyboard = self._build_status_keyboard(order_id, current_status_text)

        for entry in self._order_messages.get(order_id, []):
            updated_text = self._update_status_line(entry.get("text"), current_status_text)
            try:
                await self.bot.edit_message_text(
                    chat_id=entry["chat_id"],
                    message_id=entry["message_id"],
                    text=updated_text,
                    reply_markup=keyboard
                )
                entry["text"] = updated_text
            except Exception:  # noqa: BLE001
                logger.debug("Cannot edit order message for chat %s", entry["chat_id"])

        if success and not keyboard:
            self._order_messages.pop(order_id, None)

