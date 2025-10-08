from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.decorators import handle_db_errors
from models import Chats


@handle_db_errors
async def get_chat(db: AsyncSession,
                   chat_id: int = None,
                   user_id: int = None,
                   employee_id: int = None,
                   active: bool = False,
                   limit: int = None,
                   offset: int = None,
                   sort_asc: bool = False,
                   sort_desc: bool = False
):
    query = select(Chats)

    if chat_id:
        query = query.where(Chats.id == chat_id)

    if user_id:
        query = query.where(Chats.user_id == user_id)

    if employee_id:
        query = query.where(Chats.employee_id == employee_id)

    if active:
        query = query.where(Chats.active == active)

    if sort_asc:
        query = query.order_by(Chats.created_at.asc())

    if sort_desc:
        query = query.order_by(Chats.created_at.desc())

    if limit:
        query = query.limit(limit)

    if offset:
        query = query.offset(offset)

    if chat_id or limit == 1:
        result = await db.scalar(query)

    else:
        chats = await db.execute(query)
        result = chats.scalars().all()

    return result


@handle_db_errors
async def update_chat_status(db: AsyncSession,
                             chat_id: int
):
    query = update(Chats).where(Chats.id == chat_id).values(active=False)
    result = await db.execute(query)

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
    await db.commit()


@handle_db_errors
async def create_chat(db: AsyncSession,
                      user_id: int,
                      employee_id: int,
                      topic: str,
):
    chat_item = Chats(
        user_id=user_id,
        employee_id=employee_id,
        topic=topic
    )
    db.add(chat_item)
    await db.commit()

