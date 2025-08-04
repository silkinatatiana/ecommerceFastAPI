from fastapi import APIRouter, Depends, status, HTTPException, Request, Form, status, Cookie
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Annotated
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
import httpx

from app.models.users import User
from app.schemas import CreateUser
from app.backend.db_depends import get_db
from app.config import Config

SECRET_KEY = 'a7c3da68e483259507f3857aa85a9379e0cde15a7e4aebd846f957651c748628'
ALGORITHM = 'HS256'

router = APIRouter(prefix='/auth', tags=['auth'])
templates = Jinja2Templates(directory='app/templates/')
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/token')


async def create_access_token(username: str, user_id: int, is_admin: bool, is_supplier: bool, is_customer: bool,
                              expires_delta: timedelta):
    payload = {
        'sub': username,
        'id': user_id,
        'is_admin': is_admin,
        'is_supplier': is_supplier,
        'is_customer': is_customer,
        'exp': datetime.now(timezone.utc) + expires_delta
    }

    payload['exp'] = int(payload['exp'].timestamp())
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get('sub')
        user_id: int | None = payload.get('id')
        is_admin: bool | None = payload.get('is_admin')
        is_supplier: bool | None = payload.get('is_supplier')
        is_customer: bool | None = payload.get('is_customer')
        expire: int | None = payload.get('exp')

        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate user'
            )
        if expire is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token supplied"
            )

        if not isinstance(expire, int):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token format"
            )

        current_time = datetime.now(timezone.utc).timestamp()

        if expire < current_time:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired!"
            )

        return {
            'username': username,
            'id': user_id,
            'is_admin': is_admin,
            'is_supplier': is_supplier,
            'is_customer': is_customer,
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired!"
        )
    except jwt.exceptions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate user'
        )


@router.get('/read_current_user')
async def read_current_user(user: dict = Depends(get_current_user)):
    return {'User': user}


@router.post('/token')
async def login(db: Annotated[AsyncSession, Depends(get_db)],
                form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await authenticate_user(db, form_data.username, form_data.password)

    token = await create_access_token(user.username, user.id, user.is_admin, user.is_supplier, user.is_customer,
                                      expires_delta=timedelta(minutes=20))
    return {
        'access_token': token,
        'token_type': 'bearer'
    }


# @router.post('/')
# async def create_user(db: Annotated[AsyncSession, Depends(get_db)], create_user: CreateUser):
#     await db.execute(insert(User).values(first_name=create_user.first_name,
#                                          last_name=create_user.last_name,
#                                          username=create_user.username,
#                                          email=create_user.email,
#                                          hashed_password=bcrypt_context.hash(create_user.password),
#                                          ))
#     await db.commit()
#     return {
#         'status_code': status.HTTP_201_CREATED,
#         'transaction': 'Successful'
#     }
@router.get('/account', response_class=HTMLResponse)
async def personal_account(
        request: Request,
        token: str = Cookie(None),
        db: AsyncSession = Depends(get_db)
):
    try:
        print(token)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь не авторизован"
            )

        clean_token = token.replace("Bearer ", "")
        user_data = await get_current_user(clean_token)
        user = await db.get(User, user_data['id'])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь не авторизован"
            )
        return templates.TemplateResponse(
            "auth/personal_account.html",
            {
                "request": request,
                "auth_account_url": "/auth/account",
                "user": {
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": user.username,
                    "email": user.email
                },
                "config": {"url": Config.url, "shop_name": "Pear"}
            }
        )
    except HTTPException as e:
        response = RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)
        return response


async def authenticate_user(db: Annotated[AsyncSession, Depends(get_db)], username: str, password: str):
    user = await db.scalar(select(User).where(User.username == username))
    if not user or not bcrypt_context.verify(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.get("/create", response_class=HTMLResponse)
def create_auth_form(request: Request):
    return templates.TemplateResponse(
        "auth/create_auth_form.html",
        {
            "request": request,
            "config": {"url": Config.url}
        }
    )


from fastapi.responses import JSONResponse


@router.post('/register')
async def register(
        request: Request,
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
            user.is_supplier,
            user.is_customer,
            timedelta(minutes=20)
        )

        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            key="token",
            value=token,
            httponly=True,
            max_age=1200,
            secure=True,  # Для HTTPS
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


async def get_current_user_from_cookie(request: Request):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return await get_current_user(token.replace("Bearer", ""))


@router.get('/favorites', response_class=HTMLResponse)
async def favorites_page(request: Request):
    return {"message": "It`s favorites"}