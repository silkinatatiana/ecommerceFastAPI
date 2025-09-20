from fastapi import Depends
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db_depends import get_db
from app.models import Chats

# TODO
#  создать в папке бэкэнд (переименовать на БД) по одному файлу на каждую модель (таблицу).
#  Файл это класс, похожий на бота в ТГ. В идеале 4 метода - GET, ADD, UPDATE, DELETE
#  (если в проекте используются несколько селектов -
#  постараться их объединить в одну функцию с аргументами, отвечающими за логику)


# async def select_command(table,
#                          condition,
#                          all: bool = False,
#                          db: AsyncSession = Depends(get_db)):
#     try:
#         query = select(table)
#
#         if condition:
#             query.where(condition) # TODO в condition может быть несколько условий
#
#         if all:
#             answer = await db.execute(query)
#             result = answer.scalars().all()
#         else:
#             result = await db.scalar(query)
#
#         return result
#
#     except SQLAlchemyError as e:
#         await db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Ошибка базы данных: {str(e)}"
#         )
#
#     except Exception:
#         raise f"Не удалось выполнить запрос в БД"
#
#
# query = select(Chats).where(Chats.user_id == user_id).order_by(Chats.created_at.desc())
#         result = await db.execute(query)
#         chats = result.scalars().all()
#
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
#         return chats
#
#
#
# limit = 10
#         offset = (page - 1) * limit
#
#         query = (
#             select(Chats)
#             .where(Chats.user_id == user_id)
#             .order_by(Chats.created_at.desc())
#             .offset(offset)
#             .limit(limit + 1)
#         )
#         result = await db.execute(query)
#         chats_with_extra = result.scalars().all()
#
#         has_more = len(chats_with_extra) > limit
#         chats = chats_with_extra[:limit]
#
#         for chat in chats:
#             last_msg_query = (
#                 select(Messages)
#                 .where(Messages.chat_id == chat.id)
#                 .order_by(Messages.created_at.desc())
#                 .limit(1)
#             )
#             chat.last_message = await db.scalar(last_msg_query)
#
#
#
#
#
# query = select(Chats).where(Chats.id == chat_id)
#         chat = await db.scalar(query)
#
#         if not chat:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                                 detail='Чат не найден')
#         return chat
#
#
# query_employee_ids = select(User).where(User.role == 'seller')
#         result = await db.execute(query_employee_ids)
#         employee_ids = result.scalars().all()
#
#
#
#
# chat = await db.scalar(select(Chats).where(Chats.id == chat_id))
#         if not chat:
#             return templates.TemplateResponse(
#                 "exceptions/not_found.html",
#                 {"request": request}
#             )
#
#         employee = await db.scalar(select(User).where(User.id == chat.employee_id))
#         messages_query = (
#             select(Messages)
#             .where(Messages.chat_id == chat_id)
#             .order_by(Messages.created_at.asc())
#         )
#         messages = (await db.execute(messages_query)).scalars().all()
#
#         current_user = await db.scalar(select(User).where(User.id == user_id))


#TODO UPDATE
async def update_chat_status(chat_id: int,
                         db: AsyncSession = Depends(get_db)):
    query = update(Chats).where(Chats.id == chat_id).values(active=False)
    result = await db.execute(query)

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
    await db.commit()

#TODO CREATE
#
# chat_item = Chats(
#     user_id=user_id,
#     employee_id=choice(employee_ids).id,
#     topic=chat_data.topic
# )
