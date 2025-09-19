from typing import Optional
from random import choice

from fastapi import APIRouter, Depends, status, HTTPException, Cookie, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from sqlalchemy import select

from app.backend.db_depends import get_db
from app.schemas import ChatCreate
from app.models import *
from app.functions.auth_func import get_user_id_by_token, get_current_user

router = APIRouter(prefix='/chats', tags=['chats'])
templates = Jinja2Templates(directory='app/templates/')


@router.get('/my')
async def get_all_chats(db: AsyncSession = Depends(get_db),
                        token: Optional[str] = Cookie(None, alias='token')):
    try:
        if not token:
            raise HTTPException(status_code=401, detail="Не авторизован")

        user_id = get_user_id_by_token(token)

        query = select(Chats).where(Chats.user_id == user_id).order_by(Chats.created_at.desc())
        result = await db.execute(query)
        chats = result.scalars().all()

        for chat in chats:
            last_msg_query = (
                select(Messages)
                .where(Messages.chat_id == chat.id)
                .order_by(Messages.created_at.desc())
                .limit(1)
            )
            last_msg = await db.scalar(last_msg_query)
            chat.last_message = last_msg

        return chats

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/load-more', response_class=HTMLResponse)
async def get_chats_partial(
    request: Request,
    page: int = 1,
    token: Optional[str] = Cookie(None, alias='token'),
    db: AsyncSession = Depends(get_db)
):
    try:
        if not token:
            raise HTTPException(status_code=401, detail="Не авторизован")

        user_dict = await get_current_user(token=token)
        user_id = user_dict['id']

        limit = 10
        offset = (page - 1) * limit

        query = (
            select(Chats)
            .where(Chats.user_id == user_id)
            .order_by(Chats.created_at.desc())
            .offset(offset)
            .limit(limit + 1)
        )
        result = await db.execute(query)
        chats_with_extra = result.scalars().all()

        has_more = len(chats_with_extra) > limit
        chats = chats_with_extra[:limit]

        for chat in chats:
            last_msg_query = (
                select(Messages)
                .where(Messages.chat_id == chat.id)
                .order_by(Messages.created_at.desc())
                .limit(1)
            )
            chat.last_message = await db.scalar(last_msg_query)

        return templates.TemplateResponse("profile/chat_items.html", {
            "request": request,
            "chats": chats,
            "has_more": has_more,
            "next_page": page + 1 if has_more else None
        })

    except Exception as e:
        print(f"Ошибка при подгрузке чатов: {e}")
        return HTMLResponse(content="")


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