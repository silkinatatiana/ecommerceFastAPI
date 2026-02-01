import json

from aiokafka import AIOKafkaProducer

from config import Config


class KafkaEventPublisher:

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
            "tg_id": tg_id,
            "chat_id": chat_id,
            "user_id": user_id,
            "message": message,
        }
        await self.producer.send_and_wait(
            Config.VERIFIED_TOPIC,
            json.dumps(payload).encode("utf-8")
        )

    async def send_order_status_change_result(self, payload: dict) -> None:
        await self.producer.send_and_wait(
            Config.CHANGE_STATUS_TOPIC,
            json.dumps(payload, ensure_ascii=False).encode("utf-8")
        )

