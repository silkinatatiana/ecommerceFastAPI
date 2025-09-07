from typing import AsyncGenerator, Optional, Annotated

from fastapi import FastAPI, Request, HTTPException, Query, Depends, Cookie
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from contextlib import asynccontextmanager

from starlette import status
from starlette.middleware.cors import CORSMiddleware
import asyncio
import logging
import httpx
import jwt

from app.routers import category, products, auth, permission, reviews, favorites, cart, orders
from app.backend.db_depends import get_db
from app.backend.db import Base, engine
from app.models import *
from app.config import Config
from app.functions.favorites_func import get_favorite_product_ids
from app.functions.cart_func import get_in_cart_product_ids

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


class NoCacheStaticFiles(StaticFiles):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        return response


app = FastAPI(lifespan=lifespan)

templates = Jinja2Templates(directory="app/templates")

app.mount("/static", NoCacheStaticFiles(directory="app/static"), name="static")

app.include_router(products.router)
app.include_router(auth.router)
app.include_router(permission.router)
app.include_router(category.router)
app.include_router(reviews.router)
app.include_router(favorites.router)
app.include_router(cart.router)
app.include_router(orders.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://127.0.0.1:8000'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

shop_info = {
    'shop_name': 'PEAR',
    'descr': 'магазин электроники'
}


@app.on_event("startup")
async def startup():
    logger.info("Приложение запущено")
    for route in app.routes:
        print(f"{route.path} -> {route.name}")


# TODO добавить более детальный вывод ошибки
#  и еще записывать логи в текстовый файлик (вид запроса, данные пользователя, время запроса, ошибка (если будет).
#  Выделять красным ошибку, успех зеленым, желтым - предупреждение. Все в одном файле
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


async def get_filters(db: Annotated[AsyncSession, Depends(get_db)]) -> dict:
    filter_fields = {
        "colors": "color",
        "ram_capacities": "RAM_capacity",
        "built_in_memory_capacities": "built_in_memory_capacity",
        "screens": "screen",
        "cpus": "cpu",
        "processor_cores": "number_of_processor_cores",
        "graphics_cores": "number_of_graphics_cores"
    }

    filters = {}

    for name, column in filter_fields.items():
        query = select(distinct(getattr(products.Product, column)))
        query = query.where(getattr(products.Product, column) != None)
        query = query.order_by(getattr(products.Product, column))

        result = await db.execute(query)
        values = [row[0] for row in result if row[0] is not None]
        filters[name] = sorted(values)

    return filters


def sort_func(memory):
    num, val = memory.split()
    return val, int(num)


@app.get('/', response_class=HTMLResponse)
async def get_main_page(
        request: Request,
        db: Annotated[AsyncSession, Depends(get_db)],
        token: Optional[str] = Cookie(None, alias='token'),
        category_id: Optional[str] = Query(None),
        colors: Optional[str] = Query(None),
        built_in_memory: Optional[str] = Query(None),
        is_favorite: bool = Query(False),
        partial: bool = Query(False),
        page: int = Query(1, ge=1, description="Номер страницы"),
        per_page: int = Query(3, ge=1, le=50, description="Количество товаров на странице"),
):
    is_authenticated = False
    user_id = None
    favorite_product_ids = []
    in_cart_product_ids = []
    role = None

    if token:
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
            is_authenticated = True
            user_id = payload.get("id")
            role = payload.get("role")

            if is_authenticated:
                favorite_product_ids = await get_favorite_product_ids(user_id=user_id, db=db)
                in_cart_product_ids = await get_in_cart_product_ids(user_id=user_id, db=db)

        except Exception as e:
            print(f"Ошибка декодирования токена: {e}")

    try:
        async with httpx.AsyncClient() as client:
            categories_response = await client.get(f"{Config.url}/categories/")
            categories_response.raise_for_status()
            categories_data = categories_response.json()

    except httpx.HTTPStatusError:
        raise HTTPException(502, detail="Сервис каталога недоступен")
    except Exception as e:
        raise HTTPException(500, detail=f"Ошибка при запросе к API: {str(e)}")

    categories_products = {}
    selected_category_ids = [int(cid) for cid in category_id.split(',')] if category_id else []

    for category in categories_data:
        if selected_category_ids and category['id'] not in selected_category_ids:
            continue

        try:
            products_url = f"{Config.url}/products/by_category/{category['id']}"
            params = {
                "page": page,
                "per_page": per_page,
                "user_id": user_id if user_id else 0,
            }

            if colors:
                params["colors"] = colors
            if built_in_memory:
                params["built_in_memory"] = built_in_memory

            if is_favorite and is_authenticated and favorite_product_ids:
                params["favorites"] = ",".join(map(str, favorite_product_ids))

            async with httpx.AsyncClient() as client:
                products_response = await client.get(products_url, params=params)
                products_response.raise_for_status()
                products_data = products_response.json()

        except httpx.HTTPStatusError as e:
            print(f"Ошибка при запросе продуктов для категории {category['id']}: {e}")
            products_data = {"products": [], "pagination": {}}

        formatted_products = []
        for p in products_data.get('products', []):
            characteristics = [
                p.get('name'),
                p.get('RAM_capacity'),
                p.get('built_in_memory_capacity'),
                p.get('screen'),
                p.get('cpu'),
                p.get('color')
            ]
            name_parts = [str(s) for s in characteristics if s is not None]

            formatted_products.append({
                **p,
                'name': ', '.join(name_parts)
            })

        pagination_info = products_data.get('pagination', {})
        has_more = pagination_info.get('has_next', False)
        total_count = pagination_info.get('total_count', 0)
        displayed_count = len(formatted_products) + ((page - 1) * per_page)

        categories_products[category['name']] = {
            "id": category['id'],
            "products": formatted_products,
            "pagination": pagination_info,
            "has_more": has_more,
            "total_count": total_count,
            "displayed_count": displayed_count,
            "current_page": page,
            "per_page": per_page
        }

    if partial:
        template_name = 'products/more_products.html'
    else:
        template_name = 'index.html'

    filters = await get_filters(db)

    color_query = select(distinct(Product.color)).where(Product.color.isnot(None))
    if selected_category_ids:
        color_query = color_query.where(Product.category_id.in_(selected_category_ids))
    all_colors = (await db.execute(color_query)).scalars().all()

    memory_query = select(distinct(Product.built_in_memory_capacity)).where(
        Product.built_in_memory_capacity.isnot(None))
    if selected_category_ids:
        memory_query = memory_query.where(Product.category_id.in_(selected_category_ids))
    all_built_in_memory = sorted((await db.execute(memory_query)).scalars().all(), key=sort_func)

    selected_colors_list = colors.split(",") if colors else []
    selected_memory_list = built_in_memory.split(",") if built_in_memory else []

    context = {
        "request": request,
        "shop_name": "PEAR",
        "descr": "Магазин техники и электроники",
        "categories": list(categories_products.keys()),
        "colors": all_colors,
        "selected_colors": selected_colors_list,
        "all_built_in_memory": all_built_in_memory,
        "selected_built_in_memory": selected_memory_list,
        "categories_products": categories_products,
        "url": Config.url,
        "current_categories": selected_category_ids,
        "filters": filters,
        "has_products": any(c["products"] for c in categories_products.values()),
        "is_favorite": is_favorite,
        "is_authenticated": is_authenticated,
        "user_id": user_id,
        "favorite_product_ids": favorite_product_ids,
        "in_cart_product_ids": in_cart_product_ids,
        "role": role,
        "current_page": page,
        "per_page": per_page
    }

    response = templates.TemplateResponse(template_name, context)

    if token and not is_authenticated:
        response.delete_cookie("token")

    return response

# if __name__ == "__main__":
#     uvicorn.run(
#         app,
#         host=Config.API_HOST,
#         port=Config.API_PORT,
#         reload=True
#     )
