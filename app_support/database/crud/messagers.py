from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Messages


async def get_message(
        db: AsyncSession,
        chat_id: int = None,
        limit: int = None,
        offset: int = None,
        sort_asc: bool = False,
        sort_desc: bool = False):
    try:
        query = select(Messages)

        if chat_id:
            query = query.where(Messages.chat_id == chat_id)

        if sort_asc:
            query = query.order_by(Messages.created_at.asc())

        if sort_desc:
            query = query.order_by(Messages.created_at.desc())

        if limit:
            query = query.limit(limit)

        if offset:
            query = query.offset(offset)

        if limit == 1:
            result = await db.scalar(query)

        else:
            messages = await db.execute(query)
            result = messages.scalars().all()

        return result

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных: {str(e)}"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось выполнить запрос в БД: {str(e)}"
        )


async def create_message(
        sender_id: int,
        chat_id: int,
        message: str,
        db: AsyncSession):
    try:
        message_item = Messages(
            chat_id=chat_id,
            message=message,
            sender_id=sender_id
        )
        db.add(message_item)
        await db.commit()

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных: {str(e)}"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось выполнить запрос в БД: {str(e)}"
        )
