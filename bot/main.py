import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties

from bot.bot_logic import router, set_publisher
from bot.kafka.consumer import KafkaEventConsumer
from bot.kafka.producer import KafkaEventPublisher
from config import Config, Topics


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_KAFKA_TOPICS = Topics.BOT_KAFKA_TOPICS


def _mask_token(token: str | None) -> str:
    if not token:
        return "<empty>"
    return f"{token[:6]}... (len={len(token)})"


def _validate_token(token: str | None) -> str:
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN is empty or not set")
    cleaned = token.strip()
    if cleaned.count(":") != 1 or cleaned.startswith(":") or cleaned.endswith(":"):
        raise ValueError(
            f"TELEGRAM_BOT_TOKEN has invalid format: {_mask_token(cleaned)}"
        )
    return cleaned


validated_token = _validate_token(Config.TELEGRAM_BOT_TOKEN)
logger.info("Using TELEGRAM_BOT_TOKEN: %s", _mask_token(validated_token))

bot = Bot(
    token=validated_token,
    default=DefaultBotProperties(parse_mode="HTML"),
)
dp = Dispatcher()
dp.include_router(router)


async def main() -> None:
    kafka_publisher = KafkaEventPublisher()
    kafka_consumers = [
        KafkaEventConsumer(bot, topic, group_id, handler_method_name)
        for topic, group_id, handler_method_name in BOT_KAFKA_TOPICS
    ]

    await kafka_publisher.start()
    set_publisher(kafka_publisher)
    for consumer in kafka_consumers:
        await consumer.start()

    try:
        await dp.start_polling(bot)
    finally:
        for consumer in kafka_consumers:
            await consumer.stop()
        await kafka_publisher.stop()
        await bot.session.close()


if __name__ == "__main__":
    logger.info(Config.TELEGRAM_BOT_TOKEN)
    asyncio.run(main())
