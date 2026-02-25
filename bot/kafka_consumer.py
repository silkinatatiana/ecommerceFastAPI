import asyncio
import json
import logging
from collections import defaultdict
from typing import Any

from aiogram import Bot
from aiogram.types import InputMediaPhoto
from aiokafka import AIOKafkaConsumer

from bot.keyboards import Keyboard
from config import Config

logger = logging.getLogger(__name__)

_goods_verify_messages: dict[int, list[tuple[int, int, str, int]]] = defaultdict(list)


def get_goods_verify_message_ids(product_id: int) -> list[tuple[int, int, str, int]]:
    """Возвращает и удаляет список (chat_id, media_msg_id, caption, keyboard_msg_id) для данного product_id."""
    return _goods_verify_messages.pop(product_id, [])


class KafkaEventConsumer:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.consumer_order_created = AIOKafkaConsumer(
            Config.ORDERS_TOPIC,
            bootstrap_servers=Config.KAFKA_HOST,
            group_id="bot-order-created",
            auto_offset_reset="earliest",
            value_deserializer=lambda v: v and v.decode("utf-8"),
        )
        self.consumer_verified = AIOKafkaConsumer(
            Config.VERIFIED_TOPIC,
            bootstrap_servers=Config.KAFKA_HOST,
            group_id="bot-verified",
            auto_offset_reset="earliest",
            value_deserializer=lambda v: v and v.decode("utf-8"),
        )
        self.consumer_change_status = AIOKafkaConsumer(
            Config.CHANGE_STATUS_TOPIC_TO_BOT,
            bootstrap_servers=Config.KAFKA_HOST,
            group_id="bot-change-status",
            auto_offset_reset="earliest",
            value_deserializer=lambda v: v and v.decode("utf-8"),
        )

        self.consumer_goods_verify = AIOKafkaConsumer(
            Config.GOODS_TO_BOT_TOPIC,
            bootstrap_servers=Config.KAFKA_HOST,
            group_id="bot-goods-verify",
            auto_offset_reset="earliest",
            value_deserializer=lambda v: v and v.decode("utf-8"),
        )

        self._task_order_created: asyncio.Task | None = None
        self._task_order_verified: asyncio.Task | None = None
        self._task_order_change_status: asyncio.Task | None = None
        self._order_messages: dict[int, list[dict[str, Any]]] = defaultdict(list)
        self._task_goods_verify: asyncio.Task | None = None

    async def start(self) -> None:
        await self.consumer_order_created.start()
        await self.consumer_verified.start()
        await self.consumer_change_status.start()
        await self.consumer_goods_verify.start()

        self._task_order_created = asyncio.create_task(
            self._consume_loop_order_created()
        )
        self._task_order_verified = asyncio.create_task(self._consume_loop_verified())
        self._task_order_change_status = asyncio.create_task(
            self._consume_loop_change_status()
        )
        self._task_goods_verify = asyncio.create_task(self._consume_loop_goods_verify())

    async def stop(self) -> None:
        for task, consumer in [
            (self._task_order_created, self.consumer_order_created),
            (self._task_order_verified, self.consumer_verified),
            (self._task_order_change_status, self.consumer_change_status),
            (self._task_goods_verify, self._consume_loop_goods_verify),
        ]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            await consumer.stop()

    async def _consume_loop_order_created(self) -> None:
        async for msg in self.consumer_order_created:
            try:
                if not msg.value:
                    continue

                event = json.loads(msg.value)
                await self._handle_order_created(event)

            except Exception:  # noqa: BLE001
                logger.exception("Failed to process kafka message: %s", msg.value)

    async def _consume_loop_verified(self) -> None:
        async for msg in self.consumer_verified:
            try:
                if not msg.value:
                    continue

                event = json.loads(msg.value)
                await self._handle_verification_prompt(event)

            except Exception:  # noqa: BLE001
                logger.exception("Failed to process kafka message: %s", msg.value)

    async def _consume_loop_change_status(self) -> None:
        async for msg in self.consumer_change_status:
            try:
                if not msg.value:
                    continue

                event = json.loads(msg.value)
                await self._handle_status_change_result(event)

            except Exception:  # noqa: BLE001
                logger.exception("Failed to process kafka message: %s", msg.value)

    async def _consume_loop_goods_verify(self) -> None:
        async for msg in self.consumer_goods_verify:
            try:
                if not msg.value:
                    continue

                event = json.loads(msg.value)
                await self._handle_goods_verify(event)

            except Exception:  # noqa: BLE001
                logger.exception("Failed to process kafka message: %s", msg.value)

    async def _handle_verification_prompt(self, event: dict[str, Any]) -> None:
        try:
            tg_id = event.get("tg_id")
            user_id = event.get("user_id")
            message = event.get("message") or "Подтвердите верификацию аккаунта."

            keyboard = Keyboard.build_keyboard_verify_account(user_id)

            await self.bot.send_message(
                chat_id=tg_id, text=message, reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Ошибка при попытке подтвердить аккаунт телеграм: {e}")

    async def _handle_order_created(self, event: dict[str, Any]) -> None:
        slug = event.get("slug")
        positions = event.get("positions") or []
        total_sum = event.get("total_sum", 0)
        total_count = event.get("total_count", 0)
        status_text = event.get("status_text") or ""
        chat_ids = event.get("chat_ids") or []

        if not chat_ids:
            logger.warning("No support chat_ids in order_created event: %s", event)
            return

        title = f"Новый заказ {slug}\n"
        lines = [
            title,
            f"Статус: {status_text or '—'}",
            f"Сумма: {total_sum} ₽",
            f"Позиции: {len(positions)}, Кол-во: {total_count}",
            "",
        ]

        for idx, pos in enumerate(positions, start=1):
            name = pos.get("name", "—")
            count = pos.get("count", 0)
            subtotal = pos.get("subtotal", 0)
            lines.append(f"{idx}) {name} x{count} = {subtotal} ₽")

        message_text = "\n".join(lines)

        keyboard_status = Keyboard.build_status_keyboard(slug, status_text)

        for chat_id in chat_ids:
            try:
                sent = await self.bot.send_message(
                    chat_id=chat_id, text=message_text, reply_markup=keyboard_status
                )
                if slug:
                    self._order_messages.setdefault(slug, []).append(
                        {
                            "chat_id": chat_id,
                            "message_id": sent.message_id,
                            "text": message_text,
                        }
                    )
            except Exception:
                logger.exception(
                    "Failed to send order notification to chat %s", chat_id
                )

    async def _handle_status_change_result(self, event: dict[str, Any]) -> None:
        slug = event.get("slug")
        current_status_text = event.get("current_status_text")
        keyboard = Keyboard.build_status_keyboard(slug, current_status_text)

        entries = self._order_messages.get(slug, [])
        if not entries:
            logger.warning(
                "No stored messages for slug %s (bot may have restarted after order created)",
                slug,
            )
        for entry in entries:
            updated_text = update_status_line(entry.get("text"), current_status_text)
            try:
                await self.bot.edit_message_text(
                    chat_id=entry["chat_id"],
                    message_id=entry["message_id"],
                    text=updated_text,
                    reply_markup=keyboard,
                )
                entry["text"] = updated_text
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    "Cannot edit order message for chat %s: %s", entry["chat_id"], e
                )

        if not keyboard:
            self._order_messages.pop(slug, None)

    async def _handle_goods_verify(self, event: dict[str, Any]) -> None:
        try:
            product_id = event.get("product_id")
            supplier_id = event.get("supplier_id")
            product_data = event.get("product_data")
            chat_ids = event.get("chat_ids") or []

            if not chat_ids:
                logger.warning("No support chat_ids in goods_verify event: %s", event)
                return
            if product_id is None:
                logger.warning("No product_id in goods_verify event: %s", event)
                return

            desc = product_data.get("description") or ""

            message = (
                f"Добавлен новый товар: {product_data['name']}\n"
                f"Описание: {desc or '—'}\n"
                f"Цена: {product_data['price']} руб.\n"
                f"Поставщик id: {supplier_id}"
            )

            image_urls = product_data.get("image_urls") or []
            message_id = None

            for chat_id in chat_ids:
                media = [InputMediaPhoto(media=url) for i, url in enumerate(image_urls)]

                if media:
                    media[0].caption = message
                    message_id = (
                        await self.bot.send_media_group(chat_id=chat_id, media=media)
                    )[0].message_id

                    keyboard = Keyboard.build_keyboard_verify_goods(
                        product_id=product_id, message_id=message_id
                    )

                    keyboard_msg = await self.bot.send_message(
                        chat_id=chat_id,
                        text="Принять или отклонить товар?",
                        reply_markup=keyboard,
                    )
                    _goods_verify_messages[product_id].append(
                        (chat_id, message_id, message, keyboard_msg.message_id)
                    )

        except Exception as e:
            logger.error(f"Ошибка при попытке подтвердить новый товар: {e}")


def update_status_line(message_text: str | None, status_text: str | None) -> str:
    """Подставляет новую строку «Статус: …» в текст сообщения."""
    if not message_text:
        return f"Статус: {status_text or '—'}"
    lines = message_text.splitlines()
    new_line = f"Статус: {status_text or '—'}"
    replaced = False
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("статус:"):
            lines[i] = new_line
            replaced = True
            break
    if not replaced and len(lines) > 2:
        lines[2] = new_line
    return "\n".join(lines)
