from typing import Annotated, Optional
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status, Cookie, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from database.crud.users import create_user, get_user, update_user_info
from general_functions.auth_func import get_current_user, authenticate_user, create_access_token, verify_password, \
    create_tokens_and_set_cookies, logout_func
from general_functions.profile import get_tab_by_section
from database.db_depends import get_db
from config import Config
from schemas import ProfileUpdate, PasswordUpdate, RegisterData, LoginData

router = APIRouter(prefix='/auth', tags=['auth'])
templates = Jinja2Templates(directory='app_support/templates/')
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


@router.get('/read_current_user')
async def read_current_user(user: dict = Depends(get_current_user)):
    return {'User': user}


@router.post('/token')
async def login(db: Annotated[AsyncSession, Depends(get_db)],
                form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await authenticate_user(db, form_data.username, form_data.password, roles=['support'])

    token = create_access_token(user.username, user.id, timedelta(minutes=Config.minutes), user.is_admin, user.role)

    return {
        'access_token': token,
        'token_type': 'bearer'
    }


@router.get('/account')
async def personal_account(
        request: Request,
        page: int = Query(1, ge=1),
        section: str = Query('profile_tab'),
        token: Optional[str] = Cookie(None, alias='token'),
        db: AsyncSession = Depends(get_db)
):
    try:
        user_dict = await get_current_user(token=token)
        user = await get_user(user_id=user_dict['id'], db=db)
        response = await get_tab_by_section(section, templates, request, user, page, db, user_dict)
        return response

    except HTTPException:
        response = RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)
        return response


@router.post("/telegram/verification")
async def request_telegram_verification(
    request: Request,
    token: Optional[str] = Cookie(None, alias="token"),
    db: AsyncSession = Depends(get_db),
):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Необходима авторизация")

    try:
        user_dict = await get_current_user(token=token)
        user = await get_user(user_id=user_dict["id"], db=db)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения пользователя: {exc}"
        ) from exc

    if user.is_verified:
        return {"detail": "Профиль уже подтвержден"}

    if not user.tg_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="В профиле отсутствует Telegram ID"
        )

    producer = getattr(request.app.state, "kafka_producer", None)
    if not producer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис подтверждения недоступен, попробуйте позже"
        )

    await producer.send_verification_prompt(
        tg_id=user.tg_id,
        chat_id=user.tg_id,
        user_id=user.id,
        message="Подтвердите аккаунт в PEAR."
    )

    return {"detail": "Запрос отправлен. Проверьте сообщения бота в Telegram."}


@router.get("/create", response_class=HTMLResponse)
def create_auth_form(request: Request):
    return templates.TemplateResponse(
        "auth/create_auth_form.html",
        {
            "request": request,
            "config": {"url": Config.url_support}
        }
    )


@router.post('/register')
async def register(register_data: RegisterData,
                   request: Request,
                   db: AsyncSession = Depends(get_db)
):
    try:
        if register_data.password != register_data.confirm_password:
            return JSONResponse(
                content={"detail": "Пароли не совпадают"},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        tg_id = None
        try:
            tg_id = int(register_data.telegram)
        except Exception:
            tg_id = None

        user = await create_user(first_name=register_data.first_name,
                                 last_name=register_data.last_name,
                                 username=register_data.username,
                                 email=register_data.email,
                                 tg_id=tg_id,
                                 hashed_password=bcrypt_context.hash(register_data.password),
                                 role=register_data.role,
                                 db=db)

        producer = request.app.state.kafka_producer
        if tg_id:
            await producer.send_verification_prompt(
                tg_id=tg_id,
                chat_id=tg_id,
                user_id=user.id,
                message="Подтвердите регистрацию в PEAR."
            )

        return create_tokens_and_set_cookies(
            username=user.username,
            user_id=user.id,
            role=user.role,
            is_admin=user.is_admin
        )

    except Exception as e:
        await db.rollback()
        error_msg = "Пользователь с таким именем уже существует" if "username" in str(e) else "Ошибка регистрации"
        return JSONResponse(
            content={"detail": error_msg},
            status_code=status.HTTP_400_BAD_REQUEST
        )


@router.post('/login')
async def login(request: Request,
                login_data: LoginData,
                db: AsyncSession = Depends(get_db)
):
    try:
        user = await authenticate_user(db, login_data.username, login_data.password, roles=['support'])

        return create_tokens_and_set_cookies(
            username=user.username,
            user_id=user.id,
            role=user.role,
            is_admin=user.is_admin
        )

    except HTTPException:
        return templates.TemplateResponse(
            "auth/create_auth_form.html",
            {
                "request": request,
                "error": "Неверное имя пользователя или пароль",
                "config": {"url": Config.url_support}
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )


@router.get('/logout')
async def logout():
    response = await logout_func()
    return response


@router.put('/update')
async def update_profile(profile_update: ProfileUpdate,
                         token: Optional[str] = Cookie(None, alias='token'),
                         db: AsyncSession = Depends(get_db)
                         ):
    try:
        if not token:
            return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)

        user = await get_current_user(token)

        await update_user_info(user_id=user['id'],
                               first_name=profile_update.first_name,
                               last_name=profile_update.last_name,
                               email=profile_update.email,
                               db=db)
        return {"message": "Данные профиля успешно обновлены"}

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении данных: {str(e)}"
        )


@router.patch('/update/password')
async def update_password(data: PasswordUpdate,
                          token: Optional[str] = Cookie(None, alias='token'),
                          db: AsyncSession = Depends(get_db)
                          ):
    try:
        if not token:
            return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)

        if data.new_password != data.new_password_one_more_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Пароли не совпадают'
            )

        data_user = await get_current_user(token)
        user = await get_user(user_id=data_user['id'], db=db)

        if not verify_password(plain_password=data.old_password,
                               hashed_password=user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Неправильный пароль'
            )

        await update_user_info(db=db,
                               user_id=data_user['id'],
                               hashed_password=bcrypt_context.hash(data.new_password))

        return {"message": "Данные профиля успешно обновлены"}

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении данных: {str(e)}"
        )
