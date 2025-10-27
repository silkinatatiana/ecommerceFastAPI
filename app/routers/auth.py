from typing import Annotated, Optional
from datetime import timedelta, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status, Cookie, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from jose import jwt, JWTError

from general_functions.auth_func import logout_func, create_tokens_and_set_cookies
from database.crud.users import create_user, get_user, update_user_info, delete_user_from_db
from general_functions.auth_func import get_current_user, authenticate_user, create_access_token, verify_password
from general_functions.profile import get_tab_by_section
from database.db_depends import get_db
from config import Config
from schemas import ProfileUpdate, PasswordUpdate, RegisterData, LoginData

router = APIRouter(prefix='/auth', tags=['auth'])
templates = Jinja2Templates(directory='app/templates/')
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


@router.get('/read_current_user')
async def read_current_user(user: dict = Depends(get_current_user)):
    return {'User': user}


@router.post('/token')
async def login(db: Annotated[AsyncSession, Depends(get_db)],
                form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await authenticate_user(db, form_data.username, form_data.password, roles=['customer', 'seller'])

    token = create_access_token(username=user.username,
                                user_id=user.id,
                                role=user.role,
                                is_admin=user.is_admin)

    return {
        'access_token': token,
        'token_type': 'bearer'
    }


@router.get('/account')
async def personal_account(request: Request,
                           page: int = Query(1, ge=1),
                           section: str = Query('profile_tab'),
                           token: Optional[str] = Cookie(None, alias='token'),
                           db: AsyncSession = Depends(get_db)
):
    if not token:
        return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)

    try:
        user_dict = await get_current_user(token=token)
        user = await get_user(user_id=user_dict['id'], db=db)
        response = await get_tab_by_section(section, templates, request, user, page, db, user_dict)
        return response

    except HTTPException:
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
async def register(register_data: RegisterData,
                   db: AsyncSession = Depends(get_db),
):
    if register_data.password != register_data.confirm_password:
        return JSONResponse(
            content={"detail": "Пароли не совпадают"},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = await create_user(first_name=register_data.first_name,
                                 last_name=register_data.last_name,
                                 username=register_data.username,
                                 email=register_data.email,
                                 hashed_password=bcrypt_context.hash(register_data.password),
                                 role=register_data.role,
                                 db=db)

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
        user = await authenticate_user(db, login_data.username, login_data.password, roles=['customer', 'seller'])

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
                "config": {"url": Config.url}
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )


async def set_token(request: Request,
                    token: str,
                    secret_key: str,
                    call_next):
    payload = jwt.decode(
        token,
        secret_key,
        algorithms=[Config.ALGORITHM]
    )

    new_access_token = create_access_token(
        username=payload["sub"],
        user_id=payload["id"],
        role=payload["role"],
        is_admin=payload.get("is_admin", False)
    )

    response = await call_next(request)

    response.set_cookie(
        key="token",
        value=new_access_token,
        httponly=True,
        max_age=int(Config.timedelta_token.total_seconds()),
        secure=False,
        samesite='lax',
        path='/'
    )
    return response


async def auto_refresh_token(request: Request, call_next):
    access_token = request.cookies.get("token")
    refresh_token = request.cookies.get("refresh_token")

    if request.url.path.startswith("/auth/"):
        return await call_next(request)

    if not access_token or not refresh_token:
        return await call_next(request)

    try:
        payload = jwt.decode(access_token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        exp = payload.get("exp")
        if exp is None:
            raise JWTError("No exp in access token")

        now = datetime.now(timezone.utc)
        token_expire_time = datetime.fromtimestamp(exp, tz=timezone.utc)
        time_until_expire = token_expire_time - now

        if timedelta(seconds=20) < time_until_expire < timedelta(minutes=Config.token_auto_refresh_threshold):
            return await set_token(
                request=request,
                token=access_token,
                secret_key=Config.SECRET_KEY,
                call_next=call_next
            )
        else:
            return await call_next(request)

    except jwt.ExpiredSignatureError:
        try:
            refresh_payload = jwt.decode(
                refresh_token,
                Config.SECRET_KEY,
                algorithms=[Config.ALGORITHM]
            )
            if refresh_payload.get("type") != "refresh":
                raise JWTError("Invalid refresh token type")

            return await set_token(
                request=request,
                token=refresh_token,
                secret_key=Config.SECRET_KEY,
                call_next=call_next
            )

        except JWTError:
            pass

    except JWTError:
        pass

    return await call_next(request)


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


@router.delete('/delete')
async def delete_user(token: Optional[str] = Cookie(None, alias='token'),
                      db: AsyncSession = Depends(get_db),
):
    if not token:
        return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)

    current_user = await get_current_user(token)

    current_user_id = current_user['id']
    role = current_user.get('role')

    if role == 'seller' or role == 'customer':
        await delete_user_from_db(db, current_user_id)

        response = await logout_func()
        return response

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Нет прав для удаления пользователя"
    )