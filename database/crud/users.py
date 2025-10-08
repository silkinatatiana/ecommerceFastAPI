from fastapi import HTTPException, status
from httpx import delete
from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.decorators import handle_db_errors
from models import User


@handle_db_errors
async def create_user(db: AsyncSession,
                      first_name: str,
                      last_name: str,
                      username: str,
                      email:str,
                      hashed_password: str,
                      role: str
):
    result = await db.execute(insert(User).values(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role
    ).returning(User))

    await db.commit()
    created_user = result.scalar_one()
    return created_user


@handle_db_errors
async def get_user(db: AsyncSession,
                   user_id: int = None,
                   username: str = None,
                   role: str = None
):
    if user_id:
        user = await db.scalar(select(User).where(User.id == user_id))
        return user

    if username:
        user = await db.scalar(select(User).where(User.username == username))
        return user

    if role:
        query_employee_ids = select(User).where(User.role == role)
        result = await db.execute(query_employee_ids)
        employee_ids = result.scalars().all()
        return employee_ids


@handle_db_errors
async def update_user_info(db: AsyncSession,
                           user_id: int,
                           hashed_password: str = None,
                           first_name: str = None,
                           last_name: str = None,
                           email: str = None
):
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


@handle_db_errors
async def delete_user_from_db(db: AsyncSession,
                              user_id: int
):
    user = await get_user(db=db, user_id=user_id)
    await db.delete(user)
    await db.commit()


