from random import choice

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from config import Config
from database.crud.chats import create_chat, get_chat, update_chat_status
from database.crud.decorators import handler_base_errors
from database.crud.messages import get_message
from database.crud.users import get_user
from database.db_depends import get_db
from general_functions.auth_func import checking_access_rights
from schemas import ChatCreate


router = APIRouter(prefix="/chats", tags=["chats"])
templates = Jinja2Templates(directory="app/templates/")


@router.get("/my")
@handler_base_errors
async def get_all_chats(
    db: AsyncSession = Depends(get_db),
    token: str | None = Cookie(None, alias="token"),
):
    try:
        user_id = await checking_access_rights(
            token=token, roles=["customer", "seller"]
        )

        chats = await get_chat(user_id=user_id, sort_desc=True, db=db)
        if not chats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Чаты не найдены"
            )

        for chat in chats:
            last_msg = await get_message(chat_id=chat.id, sort_desc=True, db=db)

            chat.last_message = last_msg

        return chats
    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise


@router.get("/load-more", response_class=HTMLResponse)
async def get_chats_partial(
    request: Request,
    page: int = 1,
    token: str | None = Cookie(None, alias="token"),
    db: AsyncSession = Depends(get_db),
):
    from app.main import logger
    try:
        user_id = await checking_access_rights(
            token=token, roles=["customer", "seller"]
        )

        limit = 10
        offset = (page - 1) * limit

        chats_with_extra = await get_chat(
            user_id=user_id, sort_desc=True, offset=offset, limit=(limit + 1), db=db
        )
        has_more = len(chats_with_extra) > limit
        chats = chats_with_extra[:limit]

        for chat in chats:
            last_msg = await get_message(
                chat_id=chat.id, sort_desc=True, limit=1, db=db
            )
            chat.last_message = last_msg

        return templates.TemplateResponse(
            "profile/chat_items.html",
            {
                "request": request,
                "chats": chats,
                "has_more": has_more,
                "next_page": page + 1 if has_more else None,
            },
        )
    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise

    except Exception as e:
        logger.error(f"Ошибка при подгрузке чатов: {e}")


@router.get("/{chat_id}")
@handler_base_errors
async def chat_by_id(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    token: str | None = Cookie(None, alias="token"),
):
    try:
        await checking_access_rights(token=token, roles=["customer", "seller"])

        chat = await get_chat(chat_id=chat_id, db=db)

        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Чат не найден"
            )
        return chat

    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise


@router.post("/create", status_code=status.HTTP_201_CREATED)
@handler_base_errors
async def chat_create(
    chat_data: ChatCreate,
    db: AsyncSession = Depends(get_db),
    token: str | None = Cookie(None, alias="token"),
):
    try:
        user_id = await checking_access_rights(
            token=token, roles=["customer", "seller"]
        )

        employee_ids = await get_user(db=db, role="seller")

        new_chat = await create_chat(
            user_id=user_id,
            employee_id=choice(employee_ids).id,
            topic=chat_data.topic,
            db=db,
        )

        return new_chat

    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise


@router.patch("/close", status_code=status.HTTP_204_NO_CONTENT)
@handler_base_errors
async def chats_close(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    token: str | None = Cookie(None, alias="token"),
):
    try:
        await checking_access_rights(token=token, roles=["customer", "seller"])
        await update_chat_status(chat_id=chat_id, db=db)
    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise


@router.get("/{chat_id}/view", response_class=HTMLResponse)
async def view_chat(
    request: Request,
    chat_id: int,
    token: str | None = Cookie(None, alias="token"),
    db: AsyncSession = Depends(get_db),
):
    from app.main import logger
    try:
        user_id = await checking_access_rights(
            token=token, roles=["customer", "seller"]
        )

        chat = await get_chat(chat_id=chat_id, db=db)
        if not chat:
            return templates.TemplateResponse(
                "exceptions/not_found.html", {"request": request}
            )

        employee = await get_user(db=db, user_id=chat.employee_id)

        messages = await get_message(chat_id=chat_id, sort_asc=True, db=db)

        current_user = await get_user(db=db, user_id=user_id)

        return templates.TemplateResponse(
            "chat/chat_detail.html",
            {
                "request": request,
                "chat": chat,
                "messages": messages,
                "user": current_user,
                "employee": employee,
                "is_authenticated": True,
                "user_id": user_id,
                "shop_name": Config.shop_name,
                "descr": Config.descr,
            },
        )

    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise

    except Exception as e:
        logger.error(f"Ошибка при отображении чата: {e}")
        return RedirectResponse(url="/auth/account?section=chats_tab", status_code=303)
