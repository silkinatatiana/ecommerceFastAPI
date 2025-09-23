from typing import Optional
from random import choice

from fastapi import APIRouter, Depends, status, HTTPException, Cookie, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.crud.chats import update_chat_status, create_chat, get_chat
from app.database.db_depends import get_db
from app.database.crud.messages import get_message
from app.schemas import ChatCreate
from app.models import *
from app.config import Config
from app.functions.auth_func import get_user_id_by_token, get_current_user

router = APIRouter(prefix='support/chats', tags=['chats'])
templates = Jinja2Templates(directory='app_support/templates/')


@router.get('/{active}')
async def get_active_chats(db: AsyncSession = Depends(get_db)):
    pass


@router.get('/{chat_id}')
async def chat_by_id(chat_id: int,
                     db: AsyncSession = Depends(get_db)):
    try:
        chat = await get_chat(chat_id=chat_id, db=db)

        if not chat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail='Чат не найден')
        return chat

    except HTTPException:
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch('/close', status_code=status.HTTP_204_NO_CONTENT)
async def chats_close(chat_id: int,
                      db: AsyncSession = Depends(get_db)):
    try:
        await update_chat_status(chat_id=chat_id, db=db)

    except HTTPException:
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/{chat_id}/view', response_class=HTMLResponse)
async def view_chat(
        request: Request,
        chat_id: int,
        token: Optional[str] = Cookie(None, alias='token'),
        db: AsyncSession = Depends(get_db)
):
    try:
        if not token:
            return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)

        user_dict = await get_current_user(token=token)
        user_id = user_dict['id']

        chat = await get_chat(chat_id=chat_id, db=db)
        if not chat:
            return templates.TemplateResponse(
                "exceptions/not_found.html",
                {"request": request}
            )

        employee = await db.scalar(select(User).where(User.id == chat.employee_id))

        messages = await get_message(
                                    chat_id=chat_id,
                                    sort_asc=True,
                                    db=db)

        current_user = await db.scalar(select(User).where(User.id == user_id))

        return templates.TemplateResponse('chat/chat_detail.html', {
            'request': request,
            'chat': chat,
            'messages': messages,
            'user': current_user,
            'employee': employee,
            'is_authenticated': True,
            'user_id': user_id,
            "shop_name": Config.shop_name,
            "descr": Config.descr,
        })

    except Exception as e:
        print(f"Ошибка при отображении чата: {e}")
        return RedirectResponse(url='/auth/account?section=chats_tab', status_code=303)
