from fastapi import HTTPException, status
from sqlalchemy import select, update, insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from models import User


async def create_user(first_name: str,
                      last_name: str,
                      username: str,
                      email:str,
                      hashed_password: str,
                      db: AsyncSession):
    try:
        result = await db.execute(insert(User).values(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            hashed_password=hashed_password
        ).returning(User))

        await db.commit()
        created_user = result.scalar_one()
        return created_user

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


async def get_user(db: AsyncSession,
                   user_id: int = None,
                   role: str = None):
    try:
        if user_id:
            user = await db.scalar(select(User).where(User.id == user_id))
            return user

        if role:
            query_employee_ids = select(User).where(User.role == role)
            result = await db.execute(query_employee_ids)
            employee_ids = result.scalars().all()
            return employee_ids

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


async def update_user_info(db: AsyncSession,
                           user_id: int,
                           hashed_password: str = None,
                           first_name: str = None,
                           last_name: str = None,
                           email: str = None,
):
    try:
        update_data = {}

        if hashed_password is not None:
            update_data['hashed_password'] = hashed_password
        if first_name is not None:
            update_data['first_name'] = first_name
        if last_name is not None:
            update_data['last_name'] = last_name
        if email is not None:
            update_data['email'] = email

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Не указаны данные для обновления'
            )

        query = update(User).where(User.id == user_id).values(**update_data)
        await db.execute(query)
        await db.commit()

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении данных: {str(e)}"
        )





