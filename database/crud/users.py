from fastapi import HTTPException, status
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.decorators import handle_db_errors
from models import User


@handle_db_errors
async def create_user(
    db: AsyncSession,
    first_name: str,
    last_name: str,
    username: str,
    email: str,
    hashed_password: str,
    role: str,
    tg_id: int | None = None,
    tg_username: str | None = None,
    is_verified: bool | None = None,
):
    result = await db.execute(
        insert(User)
        .values(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            tg_id=tg_id,
            tg_username=tg_username,
            is_verified=is_verified if is_verified is not None else False,
            hashed_password=hashed_password,
            role=role,
        )
        .returning(User)
    )

    await db.commit()
    created_user = result.scalar_one()
    return created_user


@handle_db_errors
async def get_user(
    db: AsyncSession,
    user_id: int | None = None,
    username: str | None = None,
    telegram: str | None = None,
    tg_id: int | None = None,
    tg_username: str | None = None,
    role: str | None = None,
):
    if user_id:
        user = await db.scalar(select(User).where(User.id == user_id))
        return user

    if tg_id:
        user = await db.scalar(select(User).where(User.tg_id == tg_id))
        return user

    if tg_username:
        user = await db.scalar(select(User).where(User.tg_username == tg_username))
        return user

    if telegram:
        user = await db.scalar(select(User).where(User.tg_username == telegram))
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
async def get_all_users(db: AsyncSession):
    query = select(User)
    result = await db.execute(query)
    users = result.scalars().all()
    return users


@handle_db_errors
async def update_user_info(
    db: AsyncSession,
    user_id: int,
    hashed_password: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    telegram: str | None = None,
    tg_id: int | None = None,
    tg_username: str | None = None,
    is_verified: bool | None = None,
):
    update_data = {}

    if hashed_password is not None:
        update_data["hashed_password"] = hashed_password
    if first_name is not None:
        update_data["first_name"] = first_name
    if last_name is not None:
        update_data["last_name"] = last_name
    if email is not None:
        update_data["email"] = email
    if telegram is not None:
        update_data["tg_username"] = telegram
    if tg_id is not None:
        update_data["tg_id"] = tg_id
    if tg_username is not None:
        update_data["tg_username"] = tg_username
    if is_verified is not None:
        update_data["is_verified"] = is_verified

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не указаны данные для обновления",
        )

    query = update(User).where(User.id == user_id).values(**update_data)
    await db.execute(query)
    await db.commit()


@handle_db_errors
async def delete_user_from_db(db: AsyncSession, user_id: int):
    user = await get_user(db=db, user_id=user_id)
    await db.delete(user)
    await db.commit()


@handle_db_errors
async def set_telegram_data(
    db: AsyncSession,
    user_id: int,
    tg_id: int,
    tg_username: str,
    is_verified: bool = True,
):
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(tg_id=tg_id, tg_username=tg_username, is_verified=is_verified)
    )
    await db.commit()
