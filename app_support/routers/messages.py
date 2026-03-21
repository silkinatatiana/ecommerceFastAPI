from fastapi import APIRouter, Cookie, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.chats import get_chat
from database.crud.messages import create_message, get_message
from database.db_depends import get_db
from general_functions.auth_func import checking_access_rights


router = APIRouter(prefix="/support/messages", tags=["messages"])
templates = Jinja2Templates(directory="app_support/templates")


@router.post("/{chat_id}/send")
async def send_message(
    chat_id: int,
    message: str = Form(...),
    token: str | None = Cookie(None, alias="token"),
    db: AsyncSession = Depends(get_db),
):
    try:
        employee_id = await checking_access_rights(token=token, roles=["support"])
        chat = await get_chat(chat_id=chat_id, db=db)
        if not chat or not chat.active:
            raise HTTPException(status_code=400, detail="Чат неактивен")

        await create_message(
            db=db, chat_id=chat_id, sender_id=employee_id, message=message
        )
        return RedirectResponse(url=f"/support/chats/{chat_id}/view", status_code=303)

    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise


@router.get("/{chat_id}/messages")
async def get_chat_messages(
    chat_id: int, token: str = Cookie(...), db: AsyncSession = Depends(get_db)
):
    await checking_access_rights(token=token, roles=["support"])
    chat = await get_chat(chat_id=chat_id, db=db)
    if not chat:
        raise HTTPException(404)
    messages = await get_message(chat_id=chat_id, sort_asc=True, db=db)
    return {"chat_id": chat.id, "messages": messages}
