from typing import Optional, Annotated, List, Dict, Any

from fastapi import HTTPException, Depends
from sqlalchemy import select, distinct
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.routers import products
from database.db_depends import get_db
from config import Config


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


async def fetch_products_for_category(category_id: int,
                                      db: AsyncSession,
                                      user_id: Optional[int],
                                      favorite_product_ids: List[int],
                                      colors: Optional[str] = None,
                                      built_in_memory: Optional[str] = None,
                                      is_favorite: bool = False,
                                      current_page: int = 1,
                                      per_page: int = 3) -> Dict[str, Any]:
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
