from datetime import datetime, timezone
from typing import Annotated, Dict, Any, Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse
import bcrypt

from database.crud.users import get_user
from database.db_depends import get_db
from config import Config

SECRET_KEY = Config.SECRET_KEY
ALGORITHM = Config.ALGORITHM
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/token')


def create_access_token(username: str,
                        user_id: int,
                        role: str,
                        is_admin: bool = False
):
    payload = {
        'sub': username,
        'id': user_id,
        'is_admin': is_admin,
        'role': role,
        'exp': datetime.now(timezone.utc) + Config.timedelta_token,
        'type': 'access'
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(username: str,
                         user_id: int,
                         role: str,
                         is_admin: bool = False,
):
    to_encode = {
        "sub": username,
        "id": user_id,
        "role": role,
        "is_admin": is_admin,
        "exp": datetime.now(timezone.utc) + Config.timedelta_refresh_token,
        "type": "refresh"
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str,
                 token_type: str = 'access') -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        if payload.get('type') != token_type:
            raise JWTError('Invalid token type')
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Invalid or expired token')


def create_tokens_and_set_cookies(username: str,
                                  user_id: int,
                                  role: str,
                                  is_admin: bool = False
) -> RedirectResponse:
    access_token = create_access_token(
        username=username,
        user_id=user_id,
        role=role,
        is_admin=is_admin
    )

    refresh_token = create_refresh_token(
        username=username,
        user_id=user_id,
        role=role,
        is_admin=is_admin
    )

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    response.set_cookie(
        key="token",
        value=access_token,
        httponly=True,
        max_age=int(Config.timedelta_token.total_seconds()),
        secure=False,
        samesite='lax',
        path='/'
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=int(Config.timedelta_refresh_token.total_seconds()),
        secure=False,
        samesite='lax',
        path='/'
    )

    return response


async def get_current_user(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise credentials_exception

        expire = payload.get("exp")
        if expire is None or datetime.now(timezone.utc) > datetime.fromtimestamp(expire, tz=timezone.utc):
            raise credentials_exception

        return {
            "username": username,
            "id": user_id,
            "is_admin": payload.get("is_admin", False),
            "role": payload.get("role", "user")
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise credentials_exception


def get_user_id_by_token(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id = payload.get("id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходимо авторизоваться"
        )
    return user_id


async def authenticate_user(db: Annotated[AsyncSession, Depends(get_db)],
                            username: str,
                            password: str,
                            roles: list):
    user = await get_user(db=db, username=username)

    if not user or not bcrypt_context.verify(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.role not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Нет прав доступа в личный кабинет'
        )
    return user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


async def logout_func():
    response = RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(
        key="token",
        secure=False,
        samesite='lax',
        path='/'
    )

    response.delete_cookie(
        key="refresh_token",
        secure=False,
        samesite='lax',
        path='/'
    )

    return response


async def checking_access_rights(token: Optional[str],
                                 roles: Optional[list]
):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не авторизован"
        )

    user = await get_current_user(token)

    if user.get("is_admin"):
        return user["id"]

    if user.get("role") not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав доступа"
        )

    return user["id"]
