import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties

from bot.bot_logic import router, set_publisher
from bot.kafka_consumer import KafkaEventConsumer
from bot.kafka_producer import KafkaEventPublisher
from bot.bot_config import BotConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


validated_token = _validate_token(BotConfig.TELEGRAM_BOT_TOKEN)
logger.info("Using TELEGRAM_BOT_TOKEN: %s", _mask_token(validated_token))

bot = Bot(
    token=validated_token,
    default=DefaultBotProperties(parse_mode="HTML"),
)
dp = Dispatcher()
dp.include_router(router)


async def main() -> None:
    kafka_publisher = KafkaEventPublisher()
    kafka_consumer = KafkaEventConsumer(bot)

    await kafka_publisher.start()
    set_publisher(kafka_publisher)
    await kafka_consumer.start()

    try:
        await dp.start_polling(bot)
    finally:
        await kafka_consumer.stop()
        await kafka_publisher.stop()
        await bot.session.close()


if __name__ == "__main__":
    logger.info(BotConfig.TELEGRAM_BOT_TOKEN)
    asyncio.run(main())
