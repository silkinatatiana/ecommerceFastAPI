# Отдельный сервис (все заказы, видим статус и от кого заказ, можем менять статус заказа)
# Есть страница чатов, страница чата где можем отправить сообщения.

import time
from typing import AsyncGenerator

from fastapi import FastAPI, Request, HTTPException, Query, Depends, Cookie
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models import *
from app_support.routers import orders #chats, messages


app = FastAPI()
templates = Jinja2Templates(directory="app_support/templates")

app.include_router(orders.router)
# app.include_router(chats.router)
# app.include_router(messages.router)


@app.get('/')
async def get_all_orders() -> dict:
    return {'message': 'message'}