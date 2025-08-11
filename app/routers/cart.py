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


router = APIRouter(prefix="/cart", tags=["cart"])
templates = Jinja2Templates(directory="app/templates")


@router.get('/{user_id}')
async def get_cart_by_user():
    pass


@router.post('/add')
async def add_product_to_cart():
    pass


@router.patch('/update')
async def update_count_cart():
    """если количество 0, то вызывает ручку delete"""
    pass


@router.delete('/{product_id}')
async def delete_product_from_cart():
    pass


@router.delete('/clear')
async def clear_cart():
    pass





@router.get('/')
async def get_cart_html():
    pass