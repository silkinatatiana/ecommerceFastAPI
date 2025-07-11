import httpx
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from app.routers import category, products, reviews, auth, permission
from app.backend.db import Base, engine, async_session_maker
from loguru import logger
from uuid import uuid4
from contextlib import asynccontextmanager
from fastapi import FastAPI
from typing import AsyncGenerator
import asyncio
from app.config import Config
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.routers.category import Category
from urllib.parse import unquote
import logging


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('info.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(products.router)
print(">>> Роутер products подключен")
app.include_router(auth.router)
app.include_router(permission.router)
app.include_router(category.router)

print(">>> Приложение FastAPI инициализировано")
shop_info = {
    'shop_name': 'PEAR',
    'descr': 'магазин электроники'
}

@app.on_event("startup")
async def startup():
    logger.info("Приложение запущено")
    for route in app.routes:
        print(f"{route.path} -> {route.name}")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"Запрос: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.debug(f"Ответ: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}", exc_info=True)
        raise

# @app.middleware('http')
# async def log_middleware(request: Request, call_next):
#     log_id = str(uuid4())
#     with logger.contextualize(log_id=log_id):
#         try:
#             response = await call_next(request)
#             if response.status_code in [401, 402, 403, 404]:
#                 logger.warning(f'Request to {request.url.path} failed')
#             else:
#                 logger.info('Successfully accessed ' + request.url.path)
#         except Exception as ex:
#             logger.error(f'Request to {request.url.path} failed: {str(ex)}')
#             response = JSONResponse(content={'success': False}, status_code=500)
#         return response

# async def get_db() -> AsyncSession:  # TODO удалить этот фрагмент кода, поскольку то же самое есть в backend/db_depends.py
#     async with async_session_maker() as session:
#         try:
#             yield session
#         finally:
#             session.close()

@app.get('/', response_class=HTMLResponse)
async def get_main_page(request: Request):
    async with httpx.AsyncClient() as client:
        try:
            categories, products = await asyncio.gather(
                client.get(f"{Config.url}/categories/"),
                client.get(f"{Config.url}/products/")
            )
            categories.raise_for_status()
            products.raise_for_status()
        except httpx.HTTPException as e:
            raise HTTPException(502, "Сервис каталога недоступен")


    categories_products = {}

    for category in categories.json():
        categories_products[category['name']] = [product for product in products.json() if
                                                 product['category_id'] == category['id']]
    return templates.TemplateResponse(
        'index.html', {
            "request": request,
            "shop_name": "PEAR",
            "descr": "Магазин техники и электроники",
            "categories": list(categories_products.keys()),
            "categories_products": categories_products,
            "url": Config.url
        }
    )


# TODO на главной странице оставить вывод товаров у первой категории, а для остальных просто названия категорий
#  при нажатии на которые показываются первые 10 товаров из этой категории отсортированные по убыванию количества.
#  Добавить кнопку в конце категории с товарами - "Вывести/свернуть все товары из этой категории"

# TODO добавить кнопку для добавления товара на сайт по которой открывается новая страница (products/create_product) (новый html).
#  На этой странице  будет форма для добавления товара. Вводишь категгорию и свойства товара (название, кол-во и тд).
#  При отправке должен срабатывать пост запрос на создание товара (вытаскивать из введенной категории ее id).
#  Все это прописать в products.py

# TODO сделать страницу для товара (отдельной ручкой в product.py) get - запрос
