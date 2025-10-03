from typing import Optional
from random import choice

from fastapi import APIRouter, Depends, status, HTTPException, Cookie, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.chats import update_chat_status, create_chat, get_chat
from database.crud.decorators import handler_base_errors
from database.crud.users import get_user
from database.db_depends import get_db
from database.crud.messages import get_message
from schemas import ChatCreate
from app.config import Config
from functions.auth_func import get_user_id_by_token, get_current_user

router = APIRouter(prefix='/chats', tags=['chats'])
templates = Jinja2Templates(directory='app/templates/')


@router.get('/my')
@handler_base_errors
async def get_all_chats(db: AsyncSession = Depends(get_db),
                        token: Optional[str] = Cookie(None, alias='token')):
    if not token:
        return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)

    user_id = get_user_id_by_token(token)

    chats = await get_chat(user_id=user_id, sort_desc=True, db=db)
    if not chats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Чаты не найдены')

    for chat in chats:
        last_msg = await get_message(chat_id=chat.id,
                                     sort_desc=True,
                                     db=db)

        chat.last_message = last_msg

    return chats


@router.get('/load-more', response_class=HTMLResponse)
async def get_chats_partial(
        request: Request,
        page: int = 1,
        token: Optional[str] = Cookie(None, alias='token'),
        db: AsyncSession = Depends(get_db)
):
    try:
        if not token:
            return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)

        user_dict = await get_current_user(token=token)
        user_id = user_dict['id']

        limit = 10
        offset = (page - 1) * limit

        chats_with_extra = await get_chat(user_id=user_id, sort_desc=True, offset=offset, limit=(limit + 1), db=db)
        has_more = len(chats_with_extra) > limit
        chats = chats_with_extra[:limit]

        for chat in chats:
            last_msg = await get_message(chat_id=chat.id,
                                         sort_desc=True,
                                         limit=1,
                                         db=db)
            chat.last_message = last_msg

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
@handler_base_errors
async def chat_by_id(chat_id: int,
                     db: AsyncSession = Depends(get_db)
):
    chat = await get_chat(chat_id=chat_id, db=db)

    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Чат не найден')
    return chat


@router.post('/create', status_code=status.HTTP_201_CREATED)
@handler_base_errors
async def chat_create(chat_data: ChatCreate,
                      db: AsyncSession = Depends(get_db),
                      token: Optional[str] = Cookie(None, alias='token')
):
    if not token:
        return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)

    user_id = get_user_id_by_token(token)

    employee_ids = await get_user(db=db, role='seller')

    await create_chat(user_id=user_id,
                      employee_id=choice(employee_ids).id,
                      topic=chat_data.topic,
                      db=db)

    return {"message": f"Создан новый чат на тему: '{chat_data.topic}'"}


@router.patch('/close', status_code=status.HTTP_204_NO_CONTENT)
@handler_base_errors
async def chats_close(chat_id: int,
                      db: AsyncSession = Depends(get_db)
):
    await update_chat_status(chat_id=chat_id, db=db)


@router.get('/{chat_id}/view', response_class=HTMLResponse)
async def view_chat(request: Request,
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

        employee = await get_user(db=db, user_id=chat.employee_id)

        messages = await get_message(chat_id=chat_id,
                                     sort_asc=True,
                                     db=db)

        current_user = await get_user(db=db, user_id=user_id)

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
