# from datetime import datetime, timezone
# from random import randint
# from select import select
#
# import pytest
# from httpx import AsyncClient
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from database.crud.messages import get_message
# from models import Messages
# from tests.conftest import fake
#
#
# class TestChat:
#
#     @pytest.mark.positive
#     async def test_new_message(self, client: AsyncClient, client_support: AsyncClient, db: AsyncSession,
#                                test_client_token: str, test_support_token: str, test_chat
#     ):
#         send_time = datetime.now(timezone.utc)
#         new_chat = test_chat
#
#         response_send = await client.post(f"/chats/{new_chat.id}/", json={"message": fake.text()},
#                                           cookies={"token": test_client_token})
#         assert response_send.status_code == 201, f"Failed to send message: {response_send.text}"
#
#         sent_response = response_send.json()
#         sent_text = sent_response["message"]
#         sent_created_at_str = sent_response["created_at"]
#         message_id = sent_response["id"]
#
#         response_support_messages = await client_support.get(
#             f"/support/chats/{new_chat.id}/messages", cookies={"token": test_support_token}
#         )
#         assert response_support_messages.status_code == 200
#         messages = response_support_messages.json()["messages"]
#
#         assert any(m["message"] == sent_text for m in messages), "Сообщение не найдено в списке"
#         matched_msgs = [m for m in messages if m["message"] == sent_text]
#         assert matched_msgs, "Сообщение не найдено для проверки времени"
#         msg_from_api = matched_msgs[0]
#
#         created_at_api = datetime.fromisoformat(
#             msg_from_api["created_at"].replace("Z", "+00:00")
#         )
#
#         result = await db.execute(select(Messages).where(Messages.id == msg_from_api["id"]))
#         db_msg = result.scalar_one_or_none()
#         assert db_msg is not None, "Сообщение не найдено в БД"
#         assert db_msg.message == sent_text
#
#         created_at_db = db_msg.created_at
#         if created_at_db.tzinfo is None:
#             created_at_db = created_at_db.replace(tzinfo=timezone.utc)
#
#         time_diff_sec = abs((created_at_db - created_at_api).total_seconds())
#         assert time_diff_sec <= 2.0, f"Расхождение во времени: {time_diff_sec:.3f} сек"
#
#     # TODO создать тест на проверку измения статуса поддержки и еще один при создании нового заказа клиентом, что у поддержки он появился и статус активен
