from typing import Annotated, Optional

from fastapi import APIRouter, Depends, status, HTTPException, Request, Query, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy import select, func, or_
import httpx
import jwt
from loguru import logger

from app.backend.db_depends import get_db
from app.schemas import CreateProduct, ProductOut
from app.models import *
from app.models import Review
from app.functions.cart_func import get_in_cart_product_ids
from app.functions.auth_func import get_current_user, get_user_id_by_token
from app.schemas import MessageCreate
from app.config import Config

router = APIRouter(prefix='/messages', tags=['messages'])
templates = Jinja2Templates(directory='app/templates/')


@router.get('/by_chat/{chat_id}')
async def messages_by_chat_id(
    chat_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    try:
        offset = (page - 1) * limit

        # Джойним User, чтобы получить sender_name
        query = (
            select(Messages, User.username.label("sender_name"))
            .join(User, Messages.sender_id == User.id)
            .where(Messages.chat_id == chat_id)
            .order_by(Messages.created_at.asc())  # Старые сверху
            .offset(offset)
            .limit(limit)
        )

        result = await db.execute(query)
        rows = result.all()

        messages = []
        for row in rows:
            msg = row[0]  # Messages instance
            sender_name = row[1]  # username
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
async def messages_create(message_data: MessageCreate,
                          db: AsyncSession = Depends(get_db),
                          token: Optional[str] = Cookie(None, alias='token')):
    try:
        if not token:
            raise HTTPException(status_code=401, detail="Не авторизован")
        user_id = get_user_id_by_token(token)

        query = select(Chats).where(Chats.user_id == user_id)
        result = await db.execute(query)
        my_chats = result.scalars().all()
        print(my_chats)

        active_chat_id = [chat for chat in my_chats if chat.active][0].id
        print(active_chat_id)

        sender_id = get_user_id_by_token(token)
        query = select(Chats).where(Chats.id == active_chat_id)
        chat = await db.execute(query)
        chat = chat.scalar_one_or_none()
        if not chat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        message_item = Messages(
            chat_id=active_chat_id,
            message=message_data.message,
            sender_id=sender_id
        )

        db.add(message_item)
        await db.commit()

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
