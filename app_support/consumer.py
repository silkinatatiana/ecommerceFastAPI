from fastapi import Depends
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from config import Config
from database.crud.orders import create_new_order
from database.crud.users import get_user, set_telegram_data
from database.db import async_session_maker
from database.db_depends import get_db
from general_functions.product_func import update_stock
from models import Cart

KAFKA_TOPIC = Config.KAFKA_ORDERS_TOPIC
KAFKA_BOOTSTRAP_SERVERS = Config.KAFKA_HOST


async def consume_orders(consumer):
    from app_support.main import logger

    try:
        async for msg in consumer:
            logger.info(f"Получено сообщение (raw): {msg.value}")
            logger.info(msg.value, type(msg.value))
            payload = msg.value
            logger.info(f"Получен заказ: {payload.get('user_id')}, {len(payload.get('products', {}))} товаров")

            try:
                async with async_session_maker() as db:
                    for product_id_str, item in payload['products'].items():
                        product_id = int(product_id_str)
                        await update_stock(product_id=product_id, count=item['count'], db=db)

                    order = await create_new_order(
                        user_id=payload['user_id'],
                        products=payload['products'],
                        summa=payload['total_sum'],
                        slug=payload['slug'],
                        db=db

                    )
                    logger.info(1)
                    await db.execute(
                        delete(Cart).where(Cart.user_id == payload['user_id'])
                    )
                    await db.commit()

                    logger.info(f"Заказ {order.id} успешно создан и корзина очищена")

            except Exception as e:
                logger.exception(f"Ошибка обработки заказа {payload.get('user_id')}: {e}")

    finally:
        await consumer.stop()


async def consume_support_events(consumer):
    """Handle events coming from the Telegram bot."""
    from app_support.main import logger

    try:
        async for msg in consumer:
            event = msg.value
            logger.info("Support event received: %s", event)

            if not isinstance(event, dict):
                logger.warning("Ignore malformed event: %s", event)
                continue

            if event.get("event_type") == "telegram_verification_response":
                await handle_telegram_verification_response(event, logger)
    finally:
        await consumer.stop()


async def handle_telegram_verification_response(event: dict, logger):
    """Persist verification decision coming from Telegram bot."""
    user_id = event.get("user_id")
    tg_id = event.get("tg_id")
    tg_username = event.get("tg_username") or ""
    decision = event.get("decision")

    if not user_id or not tg_id or decision not in {"approve", "reject"}:
        logger.warning("Incomplete telegram_verification_response: %s", event)
        return

    is_verified = decision == "approve"
    if not is_verified:
        logger.info("User %s rejected Telegram verification; skipping DB update", user_id)
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
                is_verified=is_verified
            )
            logger.info("Updated Telegram linkage for user %s (verified=%s)", user_id, is_verified)

    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to handle telegram verification response: %s", exc)