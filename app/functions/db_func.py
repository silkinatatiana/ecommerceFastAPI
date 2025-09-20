from fastapi import Depends
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db_depends import get_db


async def select_command(table,
                         condition,
                         all: bool = False,
                         db: AsyncSession = Depends(get_db)):
    try:
        query = select(table)

        if condition:
            query.where(condition) # TODO в condition может быть несколько условий

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

    except Exception:
        raise f"Не удалось выполнить запрос в БД"

    # TODO
    #  создать в папке бэкэнд (переименовать на БД) по одному файлу на каждую модель (таблицу).
    #  Файл это класс, похожий на бота в ТГ. В идеале 4 метода - GET, ADD, UPDATE, DELETE
    #  (если в проекте используются несколько селектов -
    #  постараться их объединить в одну функцию с аргументами, отвечающими за логику)
