import json

from aiokafka import AIOKafkaProducer

from config import Config


class KafkaEventPublisher:
    def __init__(self) -> None:
        self.producer = AIOKafkaProducer(bootstrap_servers=Config.KAFKA_HOST)

    async def start(self) -> None:
        await self.producer.start()

    async def stop(self) -> None:
        await self.producer.stop()

    async def send_create_product(self, payload: dict) -> None:
        await self.producer.send_and_wait(
            Config.GOODS_TO_BOT_TOPIC,
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        )

    async def send_product_event(self, event: str, product_id: int, data: dict | None = None) -> None:
        """Отправка события товара (created/updated/deleted) в Kafka."""
        payload = {"event": event, "id": product_id}
        if data is not None:
            payload["data"] = data
        await self.producer.send_and_wait(
            Config.GOODS_TO_BOT_TOPIC,
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        )

    async def send_order(self, payload: dict) -> None:
        await self.producer.send_and_wait(
            Config.ORDERS_TOPIC,
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        )

    async def send_verification_prompt(
        self,
        *,
        tg_id: int,
        user_id: int,
        message: str,
    ) -> None:
        payload = {
            "tg_id": tg_id,
            "user_id": user_id,
            "message": message,
        }
        await self.producer.send_and_wait(
            Config.VERIFIED_TOPIC,
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        )
