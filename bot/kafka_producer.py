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

    async def send_verification_decision(
        self,
        *,
        user_id: int,
        tg_id: int,
        tg_username: str | None,
        chat_id: int,
        decision: str,
    ) -> None:
        message = {
            "user_id": user_id,
            "tg_id": tg_id,
            "tg_username": tg_username,
            "chat_id": chat_id,
            "decision": decision,
        }
        await self.producer.send_and_wait(
            Config.TG_VERIFIED_TOPIC, json.dumps(message).encode("utf-8")
        )

    async def send_order_status_change_request(
        self, *, slug: str, target_status: str
    ) -> None:
        payload = {"slug": slug, "target_status": target_status}
        await self.producer.send_and_wait(
            Config.CHANGE_STATUS_TOPIC_TO_SUPPORT, json.dumps(payload).encode("utf-8")
        )

    async def send_goods_verify_decision(self, *, product_id: int, decision: str) -> None:
        payload = {"product_id": product_id, "decision": decision}
        await self.producer.send_and_wait(
            Config.GOODS_VERIFY_DECISION_TOPIC,
            json.dumps(payload).encode("utf-8"),
        )