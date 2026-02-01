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

    async def send_verification_decision(
        self,
        *,
        user_id: int,
        tg_id: int,
        tg_username: str | None,
        chat_id: int,
        decision: str
    ) -> None:
        message = {
            "user_id": user_id,
            "tg_id": tg_id,
            "tg_username": tg_username,
            "chat_id": chat_id,
            "decision": decision,
        }
        await self.producer.send_and_wait(
            Config.TG_VERIFIED_TOPIC,
            json.dumps(message).encode("utf-8")
        )

    async def send_order_status_change_request(
        self,
        *,
        order_id: int,
        target_status: str,
        requested_by_chat_id: int,
        requested_by_tg_id: int,
        requested_by_username: str | None = None,
    ) -> None:
        payload = {
            "order_id": order_id,
            "target_status": target_status,
            "requested_by_chat_id": requested_by_chat_id,
            "requested_by_tg_id": requested_by_tg_id,
            "requested_by_username": requested_by_username,
        }
        await self.producer.send_and_wait(
            Config.CHANGE_STATUS_TOPIC,
            json.dumps(payload).encode("utf-8")
        )