import asyncio
import json
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from aiogram import Bot
from aiogram.types import InputMediaPhoto
from aiokafka import AIOKafkaConsumer

from bot.keyboards import Keyboard
from config import Config


logger = logging.getLogger(__name__)

_goods_verify_messages: dict[int, list[tuple[int, int, str, int]]] = defaultdict(list)


def get_goods_verify_message_ids(product_id: int) -> list[tuple[int, int, str, int]]:
    return _goods_verify_messages.pop(product_id, [])


class KafkaEventConsumer:
    TOPICS = {
        "order_created": (Config.ORDERS_TOPIC, "bot-order-created"),
        "verified": (Config.VERIFIED_TOPIC, "bot-verified"),
        "change_status": (Config.CHANGE_STATUS_TOPIC_TO_BOT, "bot-change-status"),
        "goods_verify": (Config.GOODS_TO_BOT_TOPIC, "bot-goods-verify"),
    }

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.consumers: dict[str, AIOKafkaConsumer] = {}
        self.tasks: dict[str, asyncio.Task | None] = dict.fromkeys(self.TOPICS)
        self._order_messages: dict[int, list[dict]] = defaultdict(list)

    @staticmethod
    def _create_consumer(topic: str, group_id: str) -> AIOKafkaConsumer:
        return AIOKafkaConsumer(
            topic,
            bootstrap_servers=Config.KAFKA_HOST,
            group_id=group_id,
            auto_offset_reset="earliest",
            value_deserializer=lambda v: v and v.decode("utf-8"),
        )

    async def start(self) -> None:
        handlers: dict[str, Callable] = {
            "order_created": self._handle_order_created,
            "verified": self._handle_verification_prompt,
            "change_status": self._handle_status_change_result,
            "goods_verify": self._handle_goods_verify,
        }

        for name, (topic, group_id) in self.TOPICS.items():
            consumer = self._create_consumer(topic, group_id)
            await consumer.start()
            self.consumers[name] = consumer
            self.tasks[name] = asyncio.create_task(
                self._consume_loop(consumer, handlers[name], name)
            )

    async def stop(self) -> None:
        for name, task in self.tasks.items():
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            await self.consumers[name].stop()

    @staticmethod
    async def _consume_loop(
        consumer: AIOKafkaConsumer, handler: Callable[[dict], Any], name: str
    ) -> None:
        async for msg in consumer:
            try:
                if not msg.value:
                    continue
                event = json.loads(msg.value)
                await handler(event)
            except Exception:
                logger.exception("Failed to process %s message: %s", name, msg.value)

    async def _handle_verification_prompt(self, event: dict) -> None:
        try:
            keyboard = Keyboard.build_keyboard_verify_account(event["user_id"])
            await self.bot.send_message(
                chat_id=event["tg_id"],
                text=event.get("message") or "Подтвердите верификацию аккаунта.",
                reply_markup=keyboard,
            )
        except Exception as e:
            logger.error("Ошибка при верификации: %s", e)

    @staticmethod
    def _get_chat_ids(event: dict, event_name: str) -> list | None:
        chat_ids = event.get("chat_ids") or []
        if not chat_ids:
            logger.warning("No chat_ids in %s event: %s", event_name, event)
        return chat_ids or None

    async def _handle_order_created(self, event: dict) -> None:
        if not (chat_ids := self._get_chat_ids(event, "order_created")):
            return

        slug = event.get("slug")
        positions = event.get("positions") or []

        lines = [
            f"Новый заказ {slug}",
            f"Статус: {event.get('status_text') or '—'}",
            f"Сумма: {event.get('total_sum', 0)} ₽",
            f"Позиции: {len(positions)}, Кол-во: {event.get('total_count', 0)}",
            "",
        ]
        lines.extend(
            f"{i}) {p.get('name', '—')} x{p.get('count', 0)} = {p.get('subtotal', 0)} ₽"
            for i, p in enumerate(positions, 1)
        )

        message_text = "\n".join(lines)
        keyboard = Keyboard.build_status_keyboard(slug, event.get("status_text"))

        for chat_id in chat_ids:
            try:
                sent = await self.bot.send_message(
                    chat_id=chat_id, text=message_text, reply_markup=keyboard
                )
                if slug:
                    self._order_messages[slug].append(
                        {
                            "chat_id": chat_id,
                            "message_id": sent.message_id,
                            "text": message_text,
                        }
                    )
            except Exception:
                logger.exception("Failed to notify chat %s", chat_id)

    async def _handle_status_change_result(self, event: dict) -> None:
        slug = event.get("slug")
        status = event.get("current_status_text")
        keyboard = Keyboard.build_status_keyboard(slug, status)

        entries = self._order_messages.get(slug, [])
        if not entries:
            logger.warning("No stored messages for slug %s", slug)

        for entry in entries:
            updated_text = update_status_line(entry.get("text"), status)
            try:
                await self.bot.edit_message_text(
                    chat_id=entry["chat_id"],
                    message_id=entry["message_id"],
                    text=updated_text,
                    reply_markup=keyboard,
                )
                entry["text"] = updated_text
            except Exception as e:
                logger.warning(
                    "Cannot edit message for chat %s: %s", entry["chat_id"], e
                )

        if not keyboard:
            self._order_messages.pop(slug, None)

    async def _handle_goods_verify(self, event: dict) -> None:
        try:
            if not (chat_ids := self._get_chat_ids(event, "goods_verify")):
                return
            if (product_id := event.get("product_id")) is None:
                logger.warning("No product_id in goods_verify event")
                return

            product = event["product_data"]
            message = (
                f"Добавлен новый товар: {product['name']}\n"
                f"Описание: {product.get('description') or '—'}\n"
                f"Цена: {product['price']} руб.\n"
                f"Поставщик id: {event['supplier_id']}"
            )

            for chat_id in chat_ids:
                await self._send_goods_verify_message(
                    chat_id, product_id, product, message
                )

        except Exception as e:
            logger.error("Ошибка при обработке товара: %s", e)

    async def _send_goods_verify_message(
        self, chat_id: int, product_id: int, product: dict, message: str
    ) -> None:
        image_urls = product.get("image_urls") or []
        media = [InputMediaPhoto(media=url) for url in image_urls]

        if media:
            media[0].caption = message
            media_msg = await self.bot.send_media_group(chat_id=chat_id, media=media)
            message_id = media_msg[0].message_id
        else:
            text_msg = await self.bot.send_message(chat_id=chat_id, text=message)
            message_id = text_msg.message_id

        keyboard = Keyboard.build_keyboard_verify_goods(product_id, message_id)
        keyboard_msg = await self.bot.send_message(
            chat_id=chat_id,
            text="Принять или отклонить товар?",
            reply_markup=keyboard,
        )
        _goods_verify_messages[product_id].append(
            (chat_id, message_id, message, keyboard_msg.message_id)
        )


def update_status_line(message_text: str | None, status_text: str | None) -> str:
    if not message_text:
        return f"Статус: {status_text or '—'}"

    lines = message_text.splitlines()
    new_line = f"Статус: {status_text or '—'}"

    for i, line in enumerate(lines):
        if line.strip().lower().startswith("статус:"):
            lines[i] = new_line
            return "\n".join(lines)

    if len(lines) > 2:
        lines[2] = new_line
    return "\n".join(lines)
