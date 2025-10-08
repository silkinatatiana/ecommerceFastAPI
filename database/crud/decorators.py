from functools import wraps

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


def handle_db_errors(func):
    @wraps(func)
    async def wrapper(db: AsyncSession, *args, **kwargs):
        try:
            return await func(db, *args, **kwargs)
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка базы данных: {e}"
            )
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Не удалось выполнить запрос в БД: {e}"
            )
    return wrapper


def handler_base_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        db = kwargs.get('db')
        if not isinstance(db, AsyncSession):
            for arg in args:
                if isinstance(arg, AsyncSession):
                    db = arg
                    break
        try:
            return await func(*args, **kwargs)

        except Exception as e:
            if db is not None:
                await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    return wrapper