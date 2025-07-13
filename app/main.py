import asyncio
import logging
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from loguru import logger
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.routers import category, products, auth, permission
from app.backend.db import Base, engine
from app.config import Config


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
app.include_router(auth.router)
app.include_router(permission.router)
app.include_router(category.router)

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
        except httpx.HTTPStatusError as e:  # Ловим ошибки HTTP (4xx, 5xx)
            raise HTTPException(502, detail="Сервис каталога недоступен")
        except Exception as e:  # Ловим другие ошибки (например, сетевые)
            raise HTTPException(500, detail=f"Ошибка при запросе к API: {str(e)}")


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

