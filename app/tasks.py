import asyncio
import json
import logging
import threading

import redis.asyncio as redis

from config import Config
from database.crud.users import get_all_users
from database.db import async_session_maker
from general_functions.product_func import get_recommend_product_ids

from .celery_app import celery_app


logger = logging.getLogger(__name__)

_LOOP_LOCAL = threading.local()


def get_or_create_eventloop() -> asyncio.AbstractEventLoop:
    """Возвращает активный event loop в текущем потоке или создаёт новый."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
        return loop
    except (RuntimeError, ValueError):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def run_async(coro):
    """Безопасный вызов async-функции из sync-контекста Celery."""
    loop = get_or_create_eventloop()
    return loop.run_until_complete(coro)


@celery_app.task(bind=True, name="generate_recommendations")
def generate_recommendations(self):
    logger.info("🔄 Запущена задача генерации рекомендаций")
    try:
        result = run_async(_run_async())
        logger.info("✅ Задача генерации рекомендаций завершена успешно")
        return result
    except Exception as exc:
        logger.exception("💥 Ошибка в задаче generate_recommendations")
        raise self.retry(exc=exc, countdown=60, max_retries=3) from exc


async def _run_async() -> str:
    redis_client = redis.Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        db=0,
        decode_responses=False,
        socket_connect_timeout=2,
        socket_timeout=2,
        max_connections=10,
    )

    try:
        await redis_client.ping()
        logger.info("📡 Подключение к Redis успешно")
    except redis.ConnectionError:
        logger.error("❌ Не удалось подключиться к Redis", exc_info=True)
        raise

    try:
        async with async_session_maker() as db:
            users = await get_all_users(db=db)
            logger.info(f"👥 Найдено пользователей: {len(users)}")

            users_rec = {}
            for user in users:
                recommend_ids = await get_recommend_product_ids(db=db, user_id=user.id)
                users_rec[user.id] = recommend_ids
                logger.info(
                    f"🧾 Сформированы рекомендации для user_id={user.id}: {len(recommend_ids)} товаров"
                )

            payload = json.dumps(users_rec, ensure_ascii=False).encode("utf-8")
            await redis_client.setex(
                Config.REDIS_RECOMMENDATIONS_KEY, Config.RECOMMENDATIONS_TIME, payload
            )

            logger.info(
                f"💾 Рекомендации сохранены в Redis для {len(users)} пользователей"
            )
            return "OK"

    except Exception as e:
        logger.error(f"❌ Ошибка при генерации/сохранении рекомендаций: {e}")
        raise
    finally:
        await redis_client.close()
