from fastapi import Depends
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db_depends import get_db
from app.models import Chats


async def get_chat(
        chat_id: int = None,
        user_id: int = None,
        limit: int = None,
        offset: int = None,
        sort_asc: bool = False,
        sort_desc: bool = False,
        db: AsyncSession = Depends(get_db)):
    try:
        query = select(Chats)

        if chat_id:
            query = query.where(Chats.id == chat_id)

        if user_id:
            query = query.where(Chats.user_id == user_id)

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

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных: {str(e)}"
        )

    except Exception:
        raise f"Не удалось выполнить запрос в БД"


async def update_chat_status(chat_id: int,
                             db: AsyncSession = Depends(get_db)):
    query = update(Chats).where(Chats.id == chat_id).values(active=False)
    result = await db.execute(query)

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
    await db.commit()


async def create_chat(user_id: int,
                      employee_id: int,
                      topic: str,
                      db: AsyncSession = Depends(get_db)):
    chat_item = Chats(
        user_id=user_id,
        employee_id=employee_id,
        topic=topic
    )
    db.add(chat_item)
    await db.commit()
