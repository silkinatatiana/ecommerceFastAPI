# CHATS:


# TODO получить первое сообщение по chat_id отсортировать по убыванию даты создания

#         for chat in chats:
#             last_msg_query = (
#                 select(Messages)
#                 .where(Messages.chat_id == chat.id)
#                 .order_by(Messages.created_at.desc())
#                 .limit(1)
#             )
#             chat.last_message = await db.scalar(last_msg_query)
#
# TODO получить первое сообщение по chat_id отсортировать по убыванию даты создания

#         for chat in chats:
#             last_msg_query = (
#                 select(Messages)
#                 .where(Messages.chat_id == chat.id)
#                 .order_by(Messages.created_at.desc())
#                 .limit(1)
#             )
#             last_msg = await db.scalar(last_msg_query)
#             chat.last_message = last_msg
#
# TODO получить все сообщения по chat_id отсортировать по возрастанию даты создания

#         messages_query = (
#             select(Messages)
#             .where(Messages.chat_id == chat_id)
#             .order_by(Messages.created_at.asc())
#         )
#         messages = (await db.execute(messages_query)).scalars().all()