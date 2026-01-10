import json

from aiokafka import AIOKafkaProducer

from bot.bot_config import BotConfig


class KafkaEventPublisher:
    """Kafka producer used by the Telegram bot."""

    def __init__(self) -> None:
        self.producer = AIOKafkaProducer(
            bootstrap_servers=BotConfig.KAFKA_HOST
        )

    async def start(self) -> None:
        await self.producer.start()

    async def stop(self) -> None:
        await self.producer.stop()

    async def send_verification_decision(
        self,
        *,
        user_id: int,
        tg_id: int,
        tg_username: str | None,
        chat_id: int,
        decision: str
    ) -> None:
        """Send user's decision back to app_support."""
        message = {
            "event_type": "telegram_verification_response",
            "user_id": user_id,
            "tg_id": tg_id,
            "tg_username": tg_username,
            "chat_id": chat_id,
            "decision": decision,
        }
        await self.producer.send_and_wait(
            BotConfig.SUPPORT_TOPIC,
            json.dumps(message).encode("utf-8")
        )