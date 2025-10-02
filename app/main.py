import time
from typing import AsyncGenerator, Optional, Annotated, List, Dict, Any

from fastapi import FastAPI, Request, HTTPException, Query, Depends, Cookie
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.cors import CORSMiddleware
from loguru import logger
from contextlib import asynccontextmanager
import logging
import httpx
import jwt

from app.routers import category, products, auth, permission, reviews, favorites, cart, orders, chats, messages
from database.db_depends import get_db
from database.db import Base, engine
from models import *
from app.config import Config
from functions.favorites_func import get_favorite_product_ids
from functions.cart_func import get_in_cart_product_ids
from app.log.log import LOGGER

logger = LOGGER
logger.setLevel(logging.INFO)


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
app.include_router(chats.router)
app.include_router(messages.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://127.0.0.1:8000'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    logger.info("Приложение запущено")
    for route in app.routes:
        print(f"{route.path} -> {route.name}")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            f"{request.method} {request.url.path} - "
            f"IP: {client_ip} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.2f}s"
        )
        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"ERROR: {request.method} {request.url.path} - "
            f"IP: {client_ip} - "
            f"Error: {str(e)} - "
            f"Time: {process_time:.2f}s"
        )
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


async def fetch_categories() -> List[Dict[str, Any]]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{Config.url}/categories/")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError:
        raise HTTPException(502, detail="Сервис каталога недоступен")
    except Exception as e:
        raise HTTPException(500, detail=f"Ошибка при запросе к API: {str(e)}")


async def fetch_products_for_category(
    category_id: int,
    db: AsyncSession,
    user_id: Optional[int],
    favorite_product_ids: List[int],
    colors: Optional[str] = None,
    built_in_memory: Optional[str] = None,
    is_favorite: bool = False,
    current_page: int = 1,
    per_page: int = 3,
) -> Dict[str, Any]:
    params = {
        "page": current_page,
        "user_id": user_id or 0,
    }
    if colors:
        params["colors"] = colors
    if built_in_memory:
        params["built_in_memory"] = built_in_memory
    if is_favorite and favorite_product_ids:
        params["favorites"] = ",".join(map(str, favorite_product_ids))

    try:
        async with httpx.AsyncClient() as client:
            url = f"{Config.url}/products/by_category/{category_id}"
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Ошибка при запросе продуктов для категории {category_id}: {e}")
        return {"products": [], "pagination": {}}


def format_product_name(product: Dict[str, Any]) -> str:
    parts = [
        product.get('name'),
        product.get('RAM_capacity'),
        product.get('built_in_memory_capacity'),
        product.get('screen'),
        product.get('cpu'),
        product.get('color')
    ]
    return ', '.join(str(p) for p in parts if p is not None)


async def get_filtered_values(
    db: AsyncSession,
    column,
    model,
    category_ids: Optional[List[int]] = None,
    sort_key=None
):
    query = select(distinct(column)).where(column.isnot(None))
    if category_ids:
        query = query.where(model.category_id.in_(category_ids))
    result = await db.execute(query)
    values = result.scalars().all()
    if sort_key:
        return sorted(values, key=sort_key)
    return sorted(values)


def parse_int_list(param: Optional[str]) -> List[int]:
    if not param:
        return []
    try:
        return [int(cid.strip()) for cid in param.split(',') if cid.strip()]
    except ValueError:
        raise HTTPException(400, "Некорректный формат параметра")


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
):
    # === Аутентификация ===
    is_authenticated = False
    user_id = None
    favorite_product_ids = []
    in_cart_product_ids = []
    role = None

    if token:
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
            user_id = payload.get("id")
            role = payload.get("role")
            if user_id is not None:
                is_authenticated = True
                favorite_product_ids = await get_favorite_product_ids(user_id=user_id, db=db)
                in_cart_product_ids = await get_in_cart_product_ids(user_id=user_id, db=db)
        except Exception as e:
            print(f"Ошибка декодирования токена: {e}")

    # === Загрузка категорий ===
    categories_data = await fetch_categories()
    selected_category_ids = parse_int_list(category_id)

    # === Partial-запрос (для "Показать ещё") ===
    if partial:
        cat_id_str = request.query_params.get("category_id")
        if not cat_id_str:
            raise HTTPException(400, "Для partial-запроса требуется category_id")
        target_cat_id = parse_int_list(cat_id_str)[0]

        target_category = next((c for c in categories_data if c["id"] == target_cat_id), None)
        if not target_category:
            return HTMLResponse("")

        page_key = f"page_cat_{target_cat_id}"
        current_page = max(1, int(request.query_params.get(page_key, 1)))

        products_data = await fetch_products_for_category(
            category_id=target_cat_id,
            db=db,
            user_id=user_id,
            favorite_product_ids=favorite_product_ids,
            colors=colors,
            built_in_memory=built_in_memory,
            is_favorite=is_favorite,
            current_page=current_page,
            per_page=3,
        )

        formatted_products = [
            {**p, "name": format_product_name(p)} for p in products_data.get("products", [])
        ]

        pagination_info = products_data.get("pagination", {})
        has_more = pagination_info.get("has_next", False)

        category_data = {
            "id": target_cat_id,
            "page_key": page_key,
            "products": formatted_products,
            "pagination": pagination_info,
            "has_more": has_more,
            "current_page": current_page,
            "per_page": 3,
        }

        context = {
            "request": request,
            "category_data": category_data,
            "is_authenticated": is_authenticated,
            "favorite_product_ids": favorite_product_ids,
            "in_cart_product_ids": in_cart_product_ids,
            "user_id": user_id,
            "role": role,
        }
        return templates.TemplateResponse("products/more_products.html", context)

    categories_products = {}

    for category in categories_data:
        if selected_category_ids and category["id"] not in selected_category_ids:
            continue

        page_key = f"page_cat_{category['id']}"
        current_page = max(1, int(request.query_params.get(page_key, 1)))

        products_data = await fetch_products_for_category(
            category_id=category["id"],
            db=db,
            user_id=user_id,
            favorite_product_ids=favorite_product_ids,
            colors=colors,
            built_in_memory=built_in_memory,
            is_favorite=is_favorite,
            current_page=current_page,
            per_page=3,
        )

        formatted_products = [
            {**p, "name": format_product_name(p)} for p in products_data.get("products", [])
        ]

        pagination_info = products_data.get("pagination", {})
        has_more = pagination_info.get("has_next", False)
        total_count = pagination_info.get("total_count", 0)
        displayed_count = len(formatted_products) + ((current_page - 1) * 3)

        categories_products[category["name"]] = {
            "id": category["id"],
            "page_key": page_key,
            "products": formatted_products,
            "pagination": pagination_info,
            "has_more": has_more,
            "total_count": total_count,
            "displayed_count": displayed_count,
            "current_page": current_page,
            "per_page": 3,
        }

    filters = await get_filters(db)

    all_colors = await get_filtered_values(
        db, Product.color, Product, selected_category_ids
    )

    all_built_in_memory = await get_filtered_values(
        db, Product.built_in_memory_capacity, Product, selected_category_ids, sort_key=sort_func
    )

    selected_colors_list = colors.split(",") if colors else []
    selected_memory_list = built_in_memory.split(",") if built_in_memory else []

    context = {
        "request": request,
        "shop_name": Config.shop_name,
        "descr": Config.descr,
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
    }

    response = templates.TemplateResponse("index.html", context)

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
