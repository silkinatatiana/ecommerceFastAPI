import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

from aiokafka import AIOKafkaConsumer
from sqlalchemy import delete, select, update

from config import Config, Statuses
from database.crud.orders import create_new_order, get_orders, update_status
from database.crud.products import get_product
from database.crud.users import get_user, set_telegram_data
from database.db import async_session_maker
from general_functions.product_func import update_stock
from models import Cart, Product

KAFKA_BOOTSTRAP_SERVERS = Config.KAFKA_HOST
logger = logging.getLogger(__name__)


class KafkaEventConsumer:
    def __init__(
        self, topic: str, group_id: str, handler_method_name: str
    ) -> None:
        self.topic = topic
        self.group_id = group_id
        self.handler_method_name = handler_method_name
        self._consumer: AIOKafkaConsumer | None = None
        self._task: asyncio.Task | None = None

    def _create_consumer(self) -> AIOKafkaConsumer:
        return AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=Config.KAFKA_HOST,
            group_id=self.group_id,
            auto_offset_reset="earliest",
            value_deserializer=lambda v: v and v.decode("utf-8"),
        )

    async def start(self) -> None:
        handler = getattr(self, self.handler_method_name)
        self._consumer = self._create_consumer()
        await self._consumer.start()
        self._task = asyncio.create_task(
            self._consume_loop(
                self._consumer, handler, self.handler_method_name
            )
        )

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._consumer is not None:
            await self._consumer.stop()

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

    @staticmethod
    def _status_key_from_text(status_text: str | None) -> str | None:
        if not status_text:
            return None
        for attr, value in vars(Statuses).items():
            if attr.isupper() and value == status_text:
                return attr
        return None

    async def handle_order_created(self, event: dict) -> None:
        user_id = event.get("user_id")
        products = event.get("products") or {}
        total_sum = event.get("total_sum", 0)
        slug = event.get("slug")
        if user_id is None or not products or not slug:
            logger.warning("Incomplete order event: user_id=%s, slug=%s", user_id, slug)
            return
        try:
            async with async_session_maker() as db:
                for product_id_str, item in products.items():
                    product_id = int(product_id_str)
                    await update_stock(
                        product_id=product_id, count=item["count"], db=db
                    )
                order = await create_new_order(
                    user_id=user_id,
                    products=products,
                    summa=total_sum,
                    slug=slug,
                    db=db,
                )
                await db.execute(delete(Cart).where(Cart.user_id == user_id))
                await db.commit()
                logger.info(
                    "Order %s (id=%s) created, cart cleared for user_id=%s",
                    slug,
                    order.id,
                    user_id,
                )
        except Exception as exc:
            logger.exception("Failed to create order from event: %s", exc)

    @staticmethod
    async def consume_orders(consumer):
        try:
            async for msg in consumer:
                logger.info(f"Получено сообщение (raw): {msg.value}")
                logger.info(msg.value, type(msg.value))
                payload = msg.value
                logger.info(
                    f"Получен заказ: {payload.get('user_id')}, {len(payload.get('products', {}))} товаров"
                )

                try:
                    async with async_session_maker() as db:
                        for product_id_str, item in payload["products"].items():
                            product_id = int(product_id_str)
                            await update_stock(
                                product_id=product_id, count=item["count"], db=db
                            )

                        order = await create_new_order(
                            user_id=payload["user_id"],
                            products=payload["products"],
                            summa=payload["total_sum"],
                            slug=payload["slug"],
                            db=db,
                        )
                        await db.execute(
                            delete(Cart).where(Cart.user_id == payload["user_id"])
                        )
                        await db.commit()

                        logger.info(
                            f"Заказ {order.id} успешно создан и корзина очищена"
                        )

                        product_ids = [int(pid) for pid in payload["products"].keys()]
                        product_map = {}
                        if product_ids:
                            products_rows = await db.execute(
                                select(Product.id, Product.name).where(
                                    Product.id.in_(product_ids)
                                )
                            )
                            product_map = {row.id: row.name for row in products_rows}

                        positions = []
                        for pid_str, item in payload["products"].items():
                            pid = int(pid_str)
                            positions.append(
                                {
                                    "product_id": pid,
                                    "name": product_map.get(pid, f"Товар {pid}"),
                                    "count": item.get("count"),
                                    "price": item.get("price"),
                                    "subtotal": (item.get("price") or 0)
                                    * (item.get("count") or 0),
                                }
                            )

                except Exception as e:
                    logger.exception(
                        f"Ошибка обработки заказа {payload.get('user_id')}: {e}"
                    )

        finally:
            await consumer.stop()

    async def consume_support_verified(self, consumer):
        try:
            async for msg in consumer:
                event = msg.value
                logger.info("Support event received: %s", event)

                if not isinstance(event, dict):
                    logger.warning("Ignore malformed event: %s", event)
                    continue

                await self.handle_telegram_verification_response(event)

        finally:
            await consumer.stop()

    async def consume_support_change_orders_status(self, consumer):
        try:
            async for msg in consumer:
                event = msg.value
                logger.info("Support event received: %s", event)

                if not isinstance(event, dict):
                    logger.warning("Ignore malformed event: %s", event)
                    continue

                await self.handle_order_status_change_request(event)

        finally:
            await consumer.stop()

    async def consume_goods_verify_decision(self, consumer):
        try:
            async for msg in consumer:
                event = msg.value

                if not isinstance(event, dict):
                    logger.warning("Ignore malformed event: %s", event)
                    continue

                await self.handle_goods_verify_decision(event)
        finally:
            await consumer.stop()

    async def handle_telegram_verification_response(self, event: dict) -> None:
        user_id = event.get("user_id")
        tg_id = event.get("tg_id")
        tg_username = event.get("tg_username") or ""
        decision = event.get("decision")

        if not user_id or not tg_id or decision not in {"approve", "reject"}:
            logger.warning("Incomplete telegram_verification_response: %s", event)
            return

        is_verified = decision == "approve"
        if not is_verified:
            logger.info(
                "User %s rejected Telegram verification; skipping DB update", user_id
            )
            return

        try:
            async with async_session_maker() as db:
                user = await get_user(db=db, user_id=user_id)

                if not user:
                    logger.warning("User %s not found for verification", user_id)
                    return

                await set_telegram_data(
                    db=db,
                    user_id=user_id,
                    tg_id=int(tg_id),
                    tg_username=tg_username,
                    is_verified=is_verified,
                )
                logger.info(
                    "Updated Telegram linkage for user %s (verified=%s)",
                    user_id,
                    is_verified,
                )

        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to handle telegram verification response: %s", exc)

    async def handle_order_status_change_request(self, event: dict) -> None:
        slug = event.get("slug")
        target_status = event.get("target_status")

        async with async_session_maker() as db:
            try:
                order = await get_orders(db=db, slug=slug)
                if not order:
                    logger.info("Заказ не найден")
                else:
                    await update_status(
                        db=db, new_status=target_status, order_id=order.id
                    )

                    if target_status == "CANCELLED":
                        for product_id, product_info in order.products.items():
                            await update_stock(
                                product_id=int(product_id),
                                count=product_info["count"],
                                db=db,
                                add=True,
                            )

            except Exception as exc:
                await db.rollback()
                logger.exception("Failed to apply goods verify decision: %s", exc)

    async def handle_goods_verify_decision(self, event: dict):
        product_id = event.get("product_id")
        decision = event.get("decision")

        if decision != "approve":
            return

        async with async_session_maker() as db:
            try:
                product = await get_product(db=db, product_id=product_id, verify=False)

                if not product:
                    logger.info("Товар не найден")
                else:
                    await db.execute(
                        update(Product)
                        .where(Product.id == product_id)
                        .values(verify=True)
                    )
                    await db.commit()

            except Exception as exc:
                await db.rollback()
                logger.exception("Failed to change order status: %s", exc)
