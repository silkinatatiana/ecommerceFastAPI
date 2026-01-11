from sqlalchemy import delete, select, update

from config import Config
from config import Statuses
from database.crud.orders import create_new_order, get_orders
from database.crud.users import get_user, set_telegram_data
from database.db import async_session_maker
from general_functions.product_func import update_stock
from models import Cart, Product, Orders

KAFKA_TOPIC = Config.KAFKA_ORDERS_TOPIC
KAFKA_BOOTSTRAP_SERVERS = Config.KAFKA_HOST


def _status_key_from_text(status_text: str | None) -> str | None:
    if not status_text:
        return None
    for attr, value in vars(Statuses).items():
        if attr.isupper() and value == status_text:
            return attr
    return None


async def consume_orders(consumer, producer):
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
                    await db.execute(
                        delete(Cart).where(Cart.user_id == payload['user_id'])
                    )
                    await db.commit()

                    logger.info(f"Заказ {order.id} успешно создан и корзина очищена")

                    product_ids = [int(pid) for pid in payload["products"].keys()]
                    product_map = {}
                    if product_ids:
                        products_rows = await db.execute(
                            select(Product.id, Product.name).where(Product.id.in_(product_ids))
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
                                "subtotal": (item.get("price") or 0) * (item.get("count") or 0),
                            }
                        )

                    support_users = await get_user(db=db, role="support")
                    chat_ids = [
                        user.tg_id
                        for user in support_users
                        if getattr(user, "tg_id", None)
                        and getattr(user, "is_verified", False)
                    ]

                    await producer.send_order_created_notification(
                        {
                            "order_id": order.id,
                            "slug": order.slug,
                            "user_id": order.user_id,
                            "status_text": order.status,
                            "status_key": _status_key_from_text(order.status),
                            "total_sum": payload.get("total_sum"),
                            "total_count": payload.get("total_count"),
                            "positions": positions,
                            "created_at": order.date.isoformat() if order.date else None,
                            "chat_ids": chat_ids,
                        }
                    )

            except Exception as e:
                logger.exception(f"Ошибка обработки заказа {payload.get('user_id')}: {e}")

    finally:
        await consumer.stop()


async def consume_support_events(consumer, producer):
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
            elif event.get("event_type") == "order_status_change_request":
                await handle_order_status_change_request(event, logger, producer)
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


async def handle_order_status_change_request(event: dict, logger, producer):
    order_id = event.get("order_id")
    target_status = event.get("target_status")
    requested_by_chat_id = event.get("requested_by_chat_id")
    requested_by_tg_id = event.get("requested_by_tg_id")
    requested_by_username = event.get("requested_by_username")

    if not order_id or not target_status:
        logger.warning("Incomplete order_status_change_request: %s", event)
        return

    async with async_session_maker() as db:
        try:
            requester = None
            if requested_by_tg_id:
                requester = await get_user(db=db, tg_id=requested_by_tg_id)

            if not requester or requester.role != "support" or not getattr(requester, "is_verified", False):
                await producer.send_order_status_change_result(
                    {
                        "order_id": order_id,
                        "success": False,
                        "message": "Нет прав на изменение статуса",
                        "requested_by_chat_id": requested_by_chat_id,
                        "target_status": target_status,
                        "current_status_text": None,
                    }
                )
                return

            order = await get_orders(db=db, order_id=order_id)
            if not order:
                await producer.send_order_status_change_result(
                    {
                        "order_id": order_id,
                        "success": False,
                        "message": "Заказ не найден",
                        "requested_by_chat_id": requested_by_chat_id,
                        "target_status": target_status,
                        "current_status_text": None,
                    }
                )
                return

            current_status_text = order.status
            new_status_text = getattr(Statuses, target_status, None)
            allowed_previous_status = Statuses.changing_statuses.get(target_status)

            if not new_status_text or allowed_previous_status is None:
                await producer.send_order_status_change_result(
                    {
                        "order_id": order_id,
                        "success": False,
                        "message": "Недопустимый статус",
                        "requested_by_chat_id": requested_by_chat_id,
                        "target_status": target_status,
                        "current_status_text": current_status_text,
                    }
                )
                return

            if current_status_text == new_status_text:
                await producer.send_order_status_change_result(
                    {
                        "order_id": order_id,
                        "success": False,
                        "message": f"Статус уже {new_status_text}",
                        "requested_by_chat_id": requested_by_chat_id,
                        "target_status": target_status,
                        "current_status_text": current_status_text,
                    }
                )
                return

            update_stmt = (
                update(Orders)
                .where(Orders.id == order_id, Orders.status == allowed_previous_status)
                .values(status=new_status_text)
                .returning(Orders.status)
            )
            updated_status = (await db.execute(update_stmt)).scalar_one_or_none()

            if not updated_status:
                await db.rollback()
                fresh_order = await get_orders(db=db, order_id=order_id)
                await producer.send_order_status_change_result(
                    {
                        "order_id": order_id,
                        "success": False,
                        "message": f"Статус уже изменён: {fresh_order.status if fresh_order else '?'}",
                        "requested_by_chat_id": requested_by_chat_id,
                        "target_status": target_status,
                        "current_status_text": fresh_order.status if fresh_order else current_status_text,
                    }
                )
                return

            if target_status == "CANCELLED":
                for product_id, product_info in order.products.items():
                    await update_stock(product_id=int(product_id), count=product_info["count"], db=db, add=True)

            await db.commit()

            await producer.send_order_status_change_result(
                {
                    "order_id": order_id,
                    "success": True,
                    "message": f"Статус изменён на {new_status_text}",
                    "requested_by_chat_id": requested_by_chat_id,
                    "target_status": target_status,
                    "current_status_text": new_status_text,
                }
            )

        except Exception as exc:  # noqa: BLE001
            await db.rollback()
            logger.exception("Failed to change order status: %s", exc)
            await producer.send_order_status_change_result(
                {
                    "order_id": order_id,
                    "success": False,
                    "message": "Ошибка при изменении статуса",
                    "requested_by_chat_id": requested_by_chat_id,
                    "target_status": target_status,
                    "current_status_text": None,
                }
            )