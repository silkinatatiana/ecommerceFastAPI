import json

from aiokafka import AIOKafkaProducer

from config import Config


class KafkaEventPublisher:
    """Kafka producer used by app_support to talk to the bot."""

    def __init__(self) -> None:
        self.producer = AIOKafkaProducer(
            bootstrap_servers=Config.KAFKA_HOST
        )

    async def start(self) -> None:
        await self.producer.start()

    async def stop(self) -> None:
        await self.producer.stop()

    async def send_verification_prompt(
        self,
        *,
        tg_id: int,
        chat_id: int,
        user_id: int,
        message: str,
    ) -> None:
        payload = {
            "event_type": "telegram_verification_prompt",
            "tg_id": tg_id,
            "chat_id": chat_id,
            "user_id": user_id,
            "message": message,
        }
        await self.producer.send_and_wait(
            Config.SUPPORT_TOPIC,
            json.dumps(payload).encode("utf-8")
        )

