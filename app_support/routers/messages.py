from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Cookie, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from functions.auth_func import get_current_user
from database.crud.chats import get_chat
from database.crud.messages import create_message
from database.db_depends import get_db

router = APIRouter(prefix='/support/messages', tags=['messages'])
templates = Jinja2Templates(directory='app_support/templates')


@router.post('/{chat_id}/send')
async def send_message(chat_id: int,
                       message: str = Form(...),
                       token: Optional[str] = Cookie(None, alias='token'),
                       db: AsyncSession = Depends(get_db)
):
    if not token:
        raise HTTPException(status_code=403)

    user_dict = await get_current_user(token=token)
    user_id = user_dict['id']

    chat = await get_chat(chat_id=chat_id, db=db)
    if not chat or not chat.active:
        raise HTTPException(status_code=400, detail="Чат неактивен")

    await create_message(chat_id=chat_id,
                         sender_id=user_id,
                         message=message
    )

    return RedirectResponse(url=f"/support/chats/{chat_id}/view", status_code=303)
