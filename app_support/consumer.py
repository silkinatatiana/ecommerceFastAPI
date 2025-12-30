from aiokafka import AIOKafkaConsumer
import json

from sqlalchemy import delete

from app_support.main import logger
from config import Config
from database.crud.orders import create_new_order
from database.db_depends import get_db
from general_functions.product_func import update_stock
from models import Cart

KAFKA_TOPIC = Config.KAFKA_ORDERS_TOPIC
KAFKA_BOOTSTRAP_SERVERS = Config.KAFKA_HOST


async def consume_orders(consumer):
    try:
        async for msg in consumer:
            payload = msg.value
            logger.info(f"Получен заказ: {payload.get('user_id')}, {len(payload.get('products', {}))} товаров")

            try:
                async with get_db() as db:
                    for product_id_str, item in payload['products'].items():
                        product_id = int(product_id_str)
                        await update_stock(product_id=product_id, count=item['count'], db=db)

                    order = await create_new_order(
                        user_id=payload['user_id'],
                        products=payload['products'],
                        summa=payload['total_sum'],
                        db=db
                    )

                    await db.execute(
                        delete(Cart).where(Cart.user_id == payload['user_id'])
                    )
                    await db.commit()

                    logger.info(f"Заказ {order.id} успешно создан и корзина очищена")

            except Exception as e:
                logger.exception(f"Ошибка обработки заказа {payload.get('user_id')}: {e}")

    finally:
        await consumer.stop()