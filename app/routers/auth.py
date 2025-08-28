from typing import Annotated, Optional
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Form, status, Cookie, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from app.functions.auth_func import get_current_user, authenticate_user, create_access_token
from app.models.users import User
from app.backend.db_depends import get_db
from app.config import Config
from app.routers.orders import get_orders_by_user_id

router = APIRouter(prefix='/auth', tags=['auth'])
templates = Jinja2Templates(directory='app/templates/')
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


@router.get('/read_current_user')
async def read_current_user(user: dict = Depends(get_current_user)):
    return {'User': user}


@router.post('/token')
async def login(db: Annotated[AsyncSession, Depends(get_db)],
                form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await authenticate_user(db, form_data.username, form_data.password)

    token = await create_access_token(user.username, user.id, user.is_admin, user.role,
                                      expires_delta=timedelta(minutes=Config.minutes))
    return {
        'access_token': token,
        'token_type': 'bearer'
    }


@router.get('/account')
async def personal_account(
        request: Request,
        page: int = Query(1, ge=1),
        token: Optional[str] = Cookie(None, alias='token'),
        db: AsyncSession = Depends(get_db)
):
    try:
        user_dict = await get_current_user(token=token)
        orders_data = await get_orders_by_user_id(user_dict['id'], page, 5, db)
        user = await db.scalar(select(User).where(User.id == user_dict['id']))

        return templates.TemplateResponse(
            "auth/personal_account.html",
            {
                "request": request,
                "user": user,
                "orders_data": orders_data,
                "config": Config.url
            }
        )
    except HTTPException as e:
        response = RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)
        return response


@router.get("/create", response_class=HTMLResponse)
def create_auth_form(request: Request):
    return templates.TemplateResponse(
        "auth/create_auth_form.html",
        {
            "request": request,
            "config": {"url": Config.url}
        }
    )


@router.post('/register')
async def register(
        db: AsyncSession = Depends(get_db),
        first_name: str = Form(...),
        last_name: str = Form(...),
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        confirm_password: str = Form(...)
):
    if password != confirm_password:
        return JSONResponse(
            content={"detail": "Пароли не совпадают"},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        await db.execute(insert(User).values(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            hashed_password=bcrypt_context.hash(password))
        )
        await db.commit()
        return JSONResponse(
            content={"redirect_url": "/auth/account"},
            status_code=status.HTTP_200_OK
        )

    except Exception as e:
        await db.rollback()
        error_msg = "Пользователь с таким именем уже существует" if "username" in str(e) else "Ошибка регистрации"
        return JSONResponse(
            content={"detail": error_msg},
            status_code=status.HTTP_400_BAD_REQUEST
        )


@router.post('/login', response_class=HTMLResponse)
async def login(request: Request,
                db: AsyncSession = Depends(get_db),
                username: str = Form(...),
                password: str = Form(...)
                ):
    try:
        user = await authenticate_user(db, username, password)
        token = await create_access_token(
            user.username,
            user.id,
            user.is_admin,
            user.role,
            timedelta(minutes=20)
        )

        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            key="token",
            value=token,
            httponly=True,
            max_age=3600,
            secure=False,
            samesite='lax',
            path='/'
        )
        return response

    except HTTPException as e:
        return templates.TemplateResponse(
            "auth/create_auth_form.html",
            {
                "request": request,
                "error": "Неверное имя пользователя или пароль",
                "config": {"url": Config.url}
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )


@router.get('/logout')
async def logout():
    response = RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("token")
    return response
