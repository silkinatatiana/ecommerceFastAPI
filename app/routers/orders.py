from typing import Optional
import jwt
from fastapi import APIRouter, Depends, status, HTTPException, Request, Cookie
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi.templating import Jinja2Templates

from app.backend.db_depends import get_db
from app.models.favorites import Favorites
from app.routers.auth import SECRET_KEY, ALGORITHM


router = APIRouter(prefix="/orders", tags=["orders"])
templates = Jinja2Templates(directory="app/templates")


@router.get('/{user_id}')
async def get_orders_by_user_id():
    pass


@router.get('/{order_id}')
async def get_order_by_id():
    pass


@router.post('/create')
async def create_order():
    pass


@router.patch('/cancel{order_id}')
async def cancel_order():
    pass


@router.get('/')
async def get_orders_html():
    pass