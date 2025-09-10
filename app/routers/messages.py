from typing import Annotated, Optional

from fastapi import APIRouter, Depends, status, HTTPException, Request, Query, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy import select, func, or_
import httpx
import jwt
from loguru import logger

from app.backend.db_depends import get_db
from app.schemas import CreateProduct, ProductOut
from app.models import *
from app.models import Review
from app.functions.cart_func import get_in_cart_product_ids
from app.functions.auth_func import get_current_user
from app.functions.favorites_func import get_favorite_product_ids

from app.config import Config

router = APIRouter(prefix='/messages', tags=['messages'])
templates = Jinja2Templates(directory='app/templates/')


@router.get('/by_chat/{chat_id}')
async def messages_by_chat_id():
    pass


@router.post('/create/{chat_id}')
async def messages_create():
    pass
