import logging
from typing import Annotated, Any

import httpx
from fastapi import Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from jose import jwt
from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers import products
from config import Config
from database.crud.products import get_product
from database.db_depends import get_db
from general_functions.cart_func import get_in_cart_product_ids
from general_functions.favorites_func import get_favorite_product_ids
from models import Product


logger = logging.getLogger(__name__)


async def get_filters(db: Annotated[AsyncSession, Depends(get_db)]) -> dict:
    filter_fields = {
        "colors": "color",
        "ram_capacities": "RAM_capacity",
        "built_in_memory_capacities": "built_in_memory_capacity",
        "screens": "screen",
        "cpus": "cpu",
        "processor_cores": "number_of_processor_cores",
        "graphics_cores": "number_of_graphics_cores",
    }

    filters = {}

    for name, column in filter_fields.items():
        query = select(distinct(getattr(products.Product, column)))
        query = query.where(getattr(products.Product, column).isnot(None))
        query = query.order_by(getattr(products.Product, column))

        result = await db.execute(query)
        values = [row[0] for row in result if row[0] is not None]
        filters[name] = sorted(values)

    return filters


def sort_func(memory):
    num, val = memory.split()
    return val, int(num)


async def fetch_categories() -> list[dict[str, Any]]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{Config.url}/categories/")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError:
        raise HTTPException(502, detail="Сервис каталога недоступен") from None
    except Exception as e:
        raise HTTPException(500, detail=f"Ошибка при запросе к API: {str(e)}") from e


async def fetch_products_for_category(
    category_id: int,
    user_id: int | None,
    favorite_product_ids: list[int],
    colors: str | None = None,
    built_in_memory: str | None = None,
    is_favorite: bool = False,
    current_page: int = 1,
    per_page: int = 3,
) -> dict[str, Any]:
    params = {
        "page": current_page,
        "per_page": per_page,
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
        logger.error(f"Ошибка при запросе продуктов для категории {category_id}: {e}")
        return {"products": [], "pagination": {}}


def format_product_name(product: dict[str, Any]) -> str:
    parts = [
        product.get("name"),
        product.get("RAM_capacity"),
        product.get("built_in_memory_capacity"),
        product.get("screen"),
        product.get("cpu"),
        product.get("color"),
    ]
    return ", ".join(str(p) for p in parts if p is not None)


async def get_filtered_values(
    db: AsyncSession,
    column,
    model,
    category_ids: list[int] | None = None,
    sort_key=None,
):
    query = select(distinct(column)).where(column.isnot(None))
    if category_ids:
        query = query.where(model.category_id.in_(category_ids))
    result = await db.execute(query)
    values = result.scalars().all()
    if sort_key:
        return sorted(values, key=sort_key)
    return sorted(values)


def parse_int_list(param: str | None) -> list[int]:
    if not param:
        return []
    try:
        return [int(cid.strip()) for cid in param.split(",") if cid.strip()]
    except ValueError:
        raise HTTPException(400, "Некорректный формат параметра") from None


async def auth_user(token: str | None, db: AsyncSession):
    if not token:
        return {
            "is_authenticated": False,
            "user_id": None,
            "role": None,
            "favorite_product_ids": [],
            "in_cart_product_ids": [],
        }

    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        user_id = payload.get("id")
        role = payload.get("role")
        if user_id is not None:
            favorite_ids = await get_favorite_product_ids(user_id=user_id, db=db)
            cart_ids = await get_in_cart_product_ids(user_id=user_id, db=db)
            return {
                "is_authenticated": True,
                "user_id": user_id,
                "role": role,
                "favorite_product_ids": favorite_ids,
                "in_cart_product_ids": cart_ids,
            }
    except Exception as e:
        logger.error(f"Ошибка декодирования токена: {e}")

    return {
        "is_authenticated": False,
        "user_id": None,
        "role": None,
        "favorite_product_ids": [],
        "in_cart_product_ids": [],
    }


async def handle_partial_request(
    request: Request,
    db: AsyncSession,
    user_data: dict[str, Any],
    colors: str | None,
    built_in_memory: str | None,
    is_favorite: bool,
):
    cat_id_str = request.query_params.get("category_id")
    if not cat_id_str:
        raise HTTPException(400, "Для partial-запроса требуется category_id")

    target_cat_id = parse_int_list(cat_id_str)[0]
    categories_data = await fetch_categories()
    target_category = next(
        (c for c in categories_data if c["id"] == target_cat_id), None
    )
    if not target_category:
        return HTMLResponse("")

    page_key = f"page_cat_{target_cat_id}"
    current_page = max(1, int(request.query_params.get(page_key, 1)))

    products_data = await fetch_products_for_category(
        category_id=target_cat_id,
        user_id=user_data["user_id"],
        favorite_product_ids=user_data["favorite_product_ids"],
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
        **user_data,
    }
    return "products/more_products.html", context


async def build_full_page_context(
    request: Request,
    db: AsyncSession,
    user_data: dict[str, Any],
    selected_category_ids: list[int],
    recommend_product_ids: list[int],
    colors: str | None,
    built_in_memory: str | None,
    is_favorite: bool,
) -> dict[str, Any]:
    recommend_products = []
    if recommend_product_ids:
        recommend_products = await get_product(db=db, product_ids=recommend_product_ids)

    categories_data = await fetch_categories()
    categories_products = {}

    for category in categories_data:
        if selected_category_ids and category["id"] not in selected_category_ids:
            continue

        page_key = f"page_cat_{category['id']}"
        current_page = max(1, int(request.query_params.get(page_key, 1)))
        user_id = None
        if user_data:
            user_id = user_data["user_id"]
        products_data = await fetch_products_for_category(
            category_id=category["id"],
            user_id=user_id,
            favorite_product_ids=user_data["favorite_product_ids"],
            colors=colors,
            built_in_memory=built_in_memory,
            is_favorite=is_favorite,
            current_page=current_page,
        )

        formatted_products = [
            {**p, "name": format_product_name(p)}
            for p in products_data.get("products", [])
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
        db,
        Product.built_in_memory_capacity,
        Product,
        selected_category_ids,
        sort_key=sort_func,
    )

    selected_colors_list = colors.split(",") if colors else []
    selected_memory_list = built_in_memory.split(",") if built_in_memory else []

    return {
        "request": request,
        "shop_name": Config.shop_name,
        "descr": Config.descr,
        "recommend_products": recommend_products,
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
        **user_data,
    }
