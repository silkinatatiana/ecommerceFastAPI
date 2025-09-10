from fastapi import Depends
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db


async def command_execute(query,
                          all: bool = False,
                          db: AsyncSession = Depends(get_db)):
    try:
        if all:
            answer = await db.execute(query)
            result = answer.scalars().all()
        else:
            result = await db.scalar(query)

        return result

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных: {str(e)}"
        )

    except Exception as e:
        raise f"Не удалось выполнить запрос в БД"

