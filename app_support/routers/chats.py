from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, status, HTTPException, Cookie, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.crud.chats import get_chat
from database.crud.decorators import handler_base_errors
from database.crud.users import get_user
from database.db_depends import get_db
from database.crud.messages import get_message
from models import Chats
from config import Config
from general_functions.auth_func import checking_access_rights

router = APIRouter(prefix='/support/chats', tags=['chats'])
templates = Jinja2Templates(directory='app_support/templates')


@router.get('/', response_class=HTMLResponse)
async def get_all_chats(request: Request,
                        status_filter: str = Query("active"),
                        sort: str = Query("desc"),
                        token: Optional[str] = Cookie(None, alias='token'),
                        db: AsyncSession = Depends(get_db)
):
    try:
        is_authenticated = False
        employee_id = await checking_access_rights(token=token, roles=['support'])

        if employee_id:
            is_authenticated = True

        active = True if status_filter == "active" else None

        query = (
            select(Chats)
            .options(selectinload(Chats.employee))
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
            "is_authenticated": is_authenticated
        })
    except HTTPException as e:
        if e.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
            return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)
        else:
            raise


@router.get('/load-more', response_class=HTMLResponse)
async def get_chats_partial(request: Request,
                            page: int = 1,
                            status_filter: str = Query("active"),
                            sort: str = Query("desc"),
                            token: Optional[str] = Cookie(None, alias='token'),
                            db: AsyncSession = Depends(get_db)
):
    try:
        is_authenticated = False
        employee_id = await checking_access_rights(token=token, roles=['support'])
        if employee_id:
            is_authenticated = True

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
            "is_authenticated": is_authenticated
        })
    except HTTPException as e:
        if e.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
            return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)
        else:
            raise


@router.get('/{chat_id}')
@handler_base_errors
async def chat_by_id(chat_id: int,
                     db: AsyncSession = Depends(get_db),
                     token: Optional[str] = Cookie(None, alias='token')
):
    try:
        await checking_access_rights(token=token, roles=['support'])

        chat = await get_chat(chat_id=chat_id, db=db)

        if not chat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail='Чат не найден')
        return chat

    except HTTPException as e:
        if e.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
            return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)
        else:
            raise


@router.get('/{chat_id}/view', response_class=HTMLResponse)
async def view_chat(request: Request,
                    chat_id: int,
                    token: Optional[str] = Cookie(None, alias='token'),
                    db: AsyncSession = Depends(get_db)
):
    try:
        employee_id = await checking_access_rights(token=token, roles=['support'])

        chat = await get_chat(chat_id=chat_id, db=db)
        if not chat:
            return templates.TemplateResponse("exceptions/not_found.html", {"request": request})

        client = await get_user(db=db, user_id=chat.user_id)
        if not client:
            return templates.TemplateResponse("exceptions/not_found.html", {"request": request})

        employee = await get_user(db=db, user_id=employee_id)
        if not employee:
            return templates.TemplateResponse("exceptions/not_found.html", {"request": request})

        messages = await get_message(chat_id=chat_id, sort_asc=True, db=db)

        return templates.TemplateResponse('chats/chat_detail.html', {
            'request': request,
            'chat': chat,
            'messages': messages,
            'client': client,
            'employee': employee,
            'is_active': chat.active,
            'shop_name': Config.shop_name,
            'descr': Config.descr,
            'is_authenticated': True
        })

    except HTTPException as e:
        if e.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
            return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)
        else:
            raise


@router.patch('/{chat_id}/complete')
async def complete_chat(chat_id: int,
                        token: Optional[str] = Cookie(None, alias='token'),
                        db: AsyncSession = Depends(get_db)
):
    try:
        await checking_access_rights(token=token, roles=['support'])

        chat = await get_chat(chat_id=chat_id, db=db)
        if not chat:
            raise HTTPException(status_code=404)

        chat.active = False
        chat.completed_at = datetime.utcnow()
        await db.commit()

        return RedirectResponse(url=f"/support/chats/{chat_id}/view", status_code=303)

    except HTTPException as e:
        if e.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
            return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)
        else:
            raise
