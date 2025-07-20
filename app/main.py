import asyncio
import logging
import httpx
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from loguru import logger
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from app.routers import category, products, auth, permission, reviews
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
app.include_router(reviews.router)

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
async def get_main_page(request: Request, category_id: Optional[int] = Query(None)):
    async with httpx.AsyncClient() as client:
        try:
            products_url = f"{Config.url}/products/"
            if category_id:
                products_url += f"?category_id={category_id}"
            
            categories, products = await asyncio.gather(
                client.get(f"{Config.url}/categories/"),
                client.get(products_url)
            )
            
            categories.raise_for_status()
            products.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(502, detail="Сервис каталога недоступен")
        except Exception as e:
            raise HTTPException(500, detail=f"Ошибка при запросе к API: {str(e)}")

    categories_products = {}

    for category in categories.json():
            category_products = [
                {
                    **p,
                    'name': ', '.join([str(s) for s in [
                        p.get('name'),
                        p.get('RAM_capacity'),
                        p.get('built_in_memory_capacity'),
                        p.get('screen'),
                        p.get('cpu'),
                        p.get('color')
                    ] if s is not None])
                }
                for p in products.json()
                if p['category_id'] == category['id']
            ]
            
            if not category_id or category['id'] == category_id:
                categories_products[category['name']] = {
                    "id": category['id'],
                    "products": category_products[:6] if not category_id else category_products
                }

    return templates.TemplateResponse(
        'index.html', {
            "request": request,
            "shop_name": "PEAR",
            "descr": "Магазин техники и электроники",
            "categories": list(categories_products.keys()),
            "categories_products": categories_products,
            "url": Config.url,
            "current_category": category_id
        }
    )
