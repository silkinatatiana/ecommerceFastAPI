from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, status, HTTPException, Cookie, Request, Query, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.functions.auth_func import get_user_id_by_token
from database.crud.chats import update_chat_status, get_chat
from database.db_depends import get_db
from database.crud.messages import get_message
from models import *
from app_support.config import Config
from functions.auth_func import get_current_user

router = APIRouter(prefix='/support/chats', tags=['chats'])
templates = Jinja2Templates(directory='app_support/templates')


@router.get('/', response_class=HTMLResponse)
async def get_all_chats(
    request: Request,
    status_filter: str = Query("active"),
    sort: str = Query("desc"),
    token: Optional[str] = Cookie(None, alias='token'),
    db: AsyncSession = Depends(get_db)
):
    if not token:
        return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)

    user_dict = await get_current_user(token=token)
    employee_id = user_dict['id']

    active = True if status_filter == "active" else None
    #
    # chats_with_extra = await get_chat(
    #     employee_id=employee_id,
    #     sort_desc=(sort == "desc"),
    #     active=active,
    #     limit=11,
    #     db=db
    # )
    query = ( # чтобы не было ошибки с загрузкой
        select(Chats)
        .options(selectinload(Chats.employee))  # ← загружаем employee сразу
        .where(Chats.employee_id == employee_id)
    )

    if active is not None:
        query = query.where(Chats.active == active)

    if sort == "desc":
        query = query.order_by(Chats.created_at.desc())
    else:
        query = query.order_by(Chats.created_at.asc())

    query = query.limit(11)
    result = await db.execute(query)
    chats_with_extra = result.scalars().all()
    has_more = len(chats_with_extra) > 10
    chats = chats_with_extra[:10]

    for chat in chats:
        last_msg = await get_message(chat_id=chat.id, sort_desc=True, limit=1, db=db)
        chat.last_message = last_msg

    return templates.TemplateResponse("chats/chat_list.html", {
        "request": request,
        "chats": chats,
        "has_more": has_more,
        "next_page": 2 if has_more else None,
        "status_filter": status_filter,
        "sort": sort,
        "shop_name": Config.shop_name,
        "descr": Config.descr,
        "is_authenticated": True
    })


@router.get('/load-more', response_class=HTMLResponse)
async def get_chats_partial(
    request: Request,
    page: int = 1,
    status_filter: str = Query("active"),
    sort: str = Query("desc"),
    token: Optional[str] = Cookie(None, alias='token'),
    db: AsyncSession = Depends(get_db)
):
    if not token:
        return HTMLResponse("")

    user_dict = await get_current_user(token=token)
    employee_id = user_dict['id']

    active = True if status_filter == "active" else None
    limit = 10
    offset = (page - 1) * limit

    chats_with_extra = await get_chat(
        employee_id=employee_id,
        sort_desc=(sort == "desc"),
        active=active,
        offset=offset,
        limit=limit + 1,
        db=db
    )
    has_more = len(chats_with_extra) > limit
    chats = chats_with_extra[:limit]

    for chat in chats:
        last_msg = await get_message(chat_id=chat.id, sort_desc=True, limit=1, db=db)
        chat.last_message = last_msg

    return templates.TemplateResponse("chats/chat_items.html", {
        "request": request,
        "chats": chats,
        "has_more": has_more,
        "next_page": page + 1 if has_more else None,
        "status_filter": status_filter,
        "sort": sort,
        "is_authenticated": True
    })


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

#
# @router.patch('/close', status_code=status.HTTP_204_NO_CONTENT)
# async def chats_close(chat_id: int,
#                       db: AsyncSession = Depends(get_db)):
#     try:
#         await update_chat_status(chat_id=chat_id, db=db)
#
#     except HTTPException:
#         raise
#
#     except Exception as e:
#         await db.rollback()
#         raise HTTPException(status_code=500, detail=str(e))


@router.post('/{chat_id}/send')
async def send_message(
    chat_id: int,
    content: str = Form(...),
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

    # Создаём сообщение
    new_msg = Messages(
        chat_id=chat_id,
        sender_id=user_id,
        content=content,
        created_at=datetime.utcnow()
    )
    db.add(new_msg)
    await db.commit()

    return RedirectResponse(url=f"/chat/{chat_id}/view", status_code=303)


@router.post('/{chat_id}/complete')
async def complete_chat(
    chat_id: int,
    token: Optional[str] = Cookie(None, alias='token'),
    db: AsyncSession = Depends(get_db)
):
    if not token:
        raise HTTPException(status_code=403)

    chat = await get_chat(chat_id=chat_id, db=db)
    if not chat:
        raise HTTPException(status_code=404)

    chat.active = False
    chat.completed_at = datetime.utcnow()
    await db.commit()

    return RedirectResponse(url=f"/chat/{chat_id}/view", status_code=303)


@router.get('/{chat_id}/view', response_class=HTMLResponse)
async def view_chat(
    request: Request,
    chat_id: int,
    token: Optional[str] = Cookie(None, alias='token'),
    db: AsyncSession = Depends(get_db)
):
    if not token:
        return RedirectResponse(url='/auth/create', status_code=303)

    user_dict = await get_current_user(token=token)
    user_id = user_dict['id']

    chat = await get_chat(chat_id=chat_id, db=db)
    if not chat:
        return templates.TemplateResponse("exceptions/not_found.html", {"request": request})

    employee = await db.scalar(select(User).where(User.id == chat.employee_id))
    current_user = await db.scalar(select(User).where(User.id == user_id))

    messages = await get_message(chat_id=chat_id, sort_asc=True, db=db)

    return templates.TemplateResponse('chat/chat_detail.html', {
        'request': request,
        'chat': chat,
        'messages': messages,
        'user': current_user,
        'employee': employee,
        'active': chat.active,
        'shop_name': Config.shop_name,
        'descr': Config.descr,
    })