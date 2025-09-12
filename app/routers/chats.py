from typing import Optional
from random import choice

from fastapi import APIRouter, Depends, status, HTTPException, Cookie
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from sqlalchemy import select

from app.backend.db_depends import get_db
from app.schemas import ChatCreate
from app.models import *
from app.functions.auth_func import get_user_id_by_token


router = APIRouter(prefix='/chats', tags=['chats'])
templates = Jinja2Templates(directory='app/templates/')


@router.get('/my')
async def get_all_chats(db: AsyncSession = Depends(get_db),
                        token: Optional[str] = Cookie(None, alias='token')):
    try:
        if not token:
            raise HTTPException(status_code=401, detail="Не авторизован")

        user_id = get_user_id_by_token(token)

        query = select(Chats).where(Chats.user_id == user_id)
        result = await db.execute(query)
        all_chats_by_user_id = result.scalars().all()
        return all_chats_by_user_id

    except HTTPException:
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/{chat_id}')
async def chat_by_id(chat_id: int,
                     db: AsyncSession = Depends(get_db)):
    try:
        query = select(Chats).where(Chats.id == chat_id)
        chat = await db.scalar(query)

        if not chat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail='Чат не найден')
        return chat

    except HTTPException:
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/create', status_code=status.HTTP_201_CREATED)
async def chat_create(chat_data: ChatCreate,
                      db: AsyncSession = Depends(get_db),
                      token: Optional[str] = Cookie(None, alias='token')):
    try:
        if not token:
            raise HTTPException(status_code=401, detail="Не авторизован")

        user_id = get_user_id_by_token(token)

        query_employee_ids = select(User).where(User.role == 'seller')
        result = await db.execute(query_employee_ids)
        employee_ids = result.scalars().all()

        chat_item = Chats(
            user_id=user_id,
            employee_id=choice(employee_ids).id,
            topic=chat_data.topic
        )

        db.add(chat_item)
        await db.commit()
        return {"message": f"Создан новый чат на тему: '{chat_data.topic}'"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch('/close', status_code=status.HTTP_204_NO_CONTENT)
async def chats_close(chat_id: int,
                      db: AsyncSession = Depends(get_db)):
    try:
        query = update(Chats).where(Chats.id == chat_id).values(active=False)
        result = await db.execute(query)

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Chat not found")
        await db.commit()

    except HTTPException:
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
