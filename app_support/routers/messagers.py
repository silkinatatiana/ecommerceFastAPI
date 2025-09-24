from typing import Optional

from fastapi import APIRouter, Depends, status, HTTPException, Query, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.crud.chats import get_chat
from database.db_depends import get_db
from database.crud.messages import create_message
from models import *
from functions.auth_func import get_user_id_by_token
from schemas import MessageCreate

router = APIRouter(prefix='/support/messages', tags=['messages'])
templates = Jinja2Templates(directory='app_support/templates/')


@router.get('/by_chat/{chat_id}')
async def messages_by_chat_id(
        chat_id: int,
        page: int = Query(1, ge=1),
        limit: int = Query(15, ge=1, le=50),
        db: AsyncSession = Depends(get_db)
):
    try:
        offset = (page - 1) * limit

        query = (
            select(Messages, User.username.label("sender_name"))
            .join(User, Messages.sender_id == User.id)
            .where(Messages.chat_id == chat_id)
            .order_by(Messages.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await db.execute(query)
        rows = result.all()

        messages = []
        for row in rows:
            msg = row[0]
            sender_name = row[1]
            msg_dict = {
                "id": msg.id,
                "chat_id": msg.chat_id,
                "sender_id": msg.sender_id,
                "sender_name": sender_name,
                "message": msg.message,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            }
            messages.append(msg_dict)

        return messages

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/create', status_code=status.HTTP_201_CREATED)
async def messages_create(
        message_data: MessageCreate,
        db: AsyncSession = Depends(get_db),
        token: Optional[str] = Cookie(None, alias='token')
):
    try:
        if not token:
            return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)

        user_id = get_user_id_by_token(token)

        chat = await get_chat(chat_id=message_data.chat_id,
                              user_id=user_id,
                              is_active=True,
                              db=db)

        if not chat:
            raise HTTPException(status_code=404, detail="Активный чат не найден")

        await create_message(
            chat_id=message_data.chat_id,
            message=message_data.message,
            sender_id=user_id,
            db=db
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
