import logging

from sqlalchemy import delete, select

from config import Config, Statuses
from database.crud.orders import create_new_order, get_orders, update_status
from database.crud.users import get_user, set_telegram_data
from database.db import async_session_maker
from general_functions.product_func import update_stock
from models import Cart, Product


KAFKA_BOOTSTRAP_SERVERS = Config.KAFKA_HOST
logger = logging.getLogger(__name__)


def _status_key_from_text(status_text: str | None) -> str | None:
    if not status_text:
        return None
    for attr, value in vars(Statuses).items():
        if attr.isupper() and value == status_text:
            return attr
    return None


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

                    logger.info(f"Заказ {order.id} успешно создан и корзина очищена")

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

                    # await producer.send_(
                    #     {
                    #         "order_id": order.id,
                    #         "slug": order.slug,
                    #         "user_id": order.user_id,
                    #         "status_text": order.status,
                    #         "status_key": _status_key_from_text(order.status),
                    #         "total_sum": payload.get("total_sum"),
                    #         "total_count": payload.get("total_count"),
                    #         "positions": positions,
                    #         "chat_ids": await get_chat_ids(db=db),
                    #         "created_at": order.date.isoformat() if order.date else None
                    #     }
                    # )

            except Exception as e:
                logger.exception(
                    f"Ошибка обработки заказа {payload.get('user_id')}: {e}"
                )

    finally:
        await consumer.stop()


async def consume_support_verified(consumer):
    try:
        async for msg in consumer:
            event = msg.value
            logger.info("Support event received: %s", event)

            if not isinstance(event, dict):
                logger.warning("Ignore malformed event: %s", event)
                continue

            await handle_telegram_verification_response(event, logger)

    finally:
        await consumer.stop()


async def consume_support_change_orders_status(consumer):
    try:
        async for msg in consumer:
            event = msg.value
            logger.info("Support event received: %s", event)

            if not isinstance(event, dict):
                logger.warning("Ignore malformed event: %s", event)
                continue

            await handle_order_status_change_request(event, logger)

    finally:
        await consumer.stop()


async def handle_telegram_verification_response(event: dict, logger):
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


async def handle_order_status_change_request(event: dict, logger):
    slug = event.get("slug")
    target_status = event.get("target_status")

    async with async_session_maker() as db:
        try:
            order = await get_orders(db=db, slug=slug)
            if not order:
                logger.info("Заказ не найден")
            else:
                await update_status(db=db, new_status=target_status, order_id=order.id)

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
            logger.exception("Failed to change order status: %s", exc)
