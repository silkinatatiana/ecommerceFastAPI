import json
import logging
from typing import Annotated

import httpx
import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette.responses import RedirectResponse

from config import Config
from database.crud.category import get_category
from database.crud.products import (
    create_new_product,
    get_product,
    get_products_with_filters,
)
from database.crud.views import (
    create_views_product,
    get_views_by_product_user,
    update_views_by_product_user,
)
from database.db_depends import get_db, get_redis
from general_functions.auth_func import checking_access_rights, get_current_user
from general_functions.cart_func import get_in_cart_product_ids
from general_functions.favorites_func import get_favorite_product_ids
from general_functions.kafka_func import get_chat_ids
from models import Product, Review
from schemas import CreateProduct, ProductOut, RecommendOut


router = APIRouter(prefix="/products", tags=["products"])
templates = Jinja2Templates(directory="app/templates/")
logger = logging.getLogger(__name__)


@router.get("/create", response_class=HTMLResponse)
async def create_product_form(
    request: Request, token: str | None = Cookie(None, alias="token")
):
    try:
        await checking_access_rights(token=token, roles=["seller"])

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{Config.url}/categories/")
            response.raise_for_status()
            categories = response.json()

            if not isinstance(categories, list):
                categories = []

            return templates.TemplateResponse(
                "products/create_product.html",
                {
                    "request": request,
                    "categories": categories,
                    "config": {"url": Config.url},
                },
            )
    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise


@router.get("/seller_products_data", response_class=HTMLResponse)
async def seller_products_data(
    verify: bool,
    db: Annotated[AsyncSession, Depends(get_db)],
    token: str | None = Cookie(None, alias="token"),
):
    try:
        seller_id = await checking_access_rights(token=token, roles=["seller"])
        products = await get_product(db=db, user_id=seller_id, verify=verify)

        return products

    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise


@router.get("/seller_products", response_class=HTMLResponse)
async def seller_products(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    token: str | None = Cookie(None, alias="token"),
):
    seller_products_active = await seller_products_data(db=db, token=token, verify=True)
    seller_products_inactive = await seller_products_data(
        db=db, token=token, verify=False
    )

    if isinstance(seller_products_active, RedirectResponse):
        return RedirectResponse(url="/auth/create", status_code=303)

    return templates.TemplateResponse(
        "products/seller_products.html",
        {
            "request": request,
            "active_products": seller_products_active,
            "inactive_products": seller_products_inactive,
            "is_authenticated": True,
            "role": "seller",
            "config": {"url": Config.url},
            "shop_name": Config.shop_name,
            "descr": Config.descr,
        },
    )


@router.post("/create", response_model=ProductOut)
async def create_product(
    db: Annotated[AsyncSession, Depends(get_db)],
    product_data: CreateProduct,
    token: str | None = Cookie(None, alias="token"),
):
    try:
        from app.main import producer

        supplier_id = await checking_access_rights(token=token, roles=["seller"])
        category = await get_category(db=db, category_id=product_data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND"
            )
        chat_ids = await get_chat_ids(db=db)

        product = await create_new_product(
            db=db, product_data=product_data, supplier_id=supplier_id, verify=False
        )

        payload = {
            "product_id": product.id,
            "supplier_id": supplier_id,
            "product_data": product_data.model_dump(),
            "chat_ids": chat_ids,
        }

        await producer.send_and_wait(
            Config.GOODS_TO_BOT_TOPIC,
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        )
        return product

    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("/")
async def all_products(
    db: AsyncSession = Depends(get_db),
    category_id: str | None = Query(None),
    colors: str | None = Query(None),
    built_in_memory: str | None = Query(None),
    product_ids: str | None = Query(None),
):
    try:
        params = {}

        if category_id:
            category_ids = [int(categ_id) for categ_id in category_id.split(",")]
            params["category_ids"] = category_ids

        if product_ids:
            ids_list = [int(id_) for id_ in product_ids.split(",")]
            params["ids_list"] = ids_list

        if colors:
            params["colors"] = colors.split(",")

        if built_in_memory:
            params["built_in_memory"] = built_in_memory.split(",")

        products = await get_product(db=db, **params)
        return products

    except Exception as e:
        logger.error(f"Error fetching products: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/by_category/{category_id}")
async def products_by_category(
    category_id: int,
    request: Request,
    user_id: int | None = Query(None),
    per_page: int = Query(3, ge=1, le=50, description="Количество товаров на странице"),
    colors: str = Query(None),
    built_in_memory: str = Query(None),
    favorites: list[str] | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    category = await get_category(db=db, category_id=category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    try:
        page = int(request.query_params.get("page", 1))
        if page < 1:
            page = 1
    except (TypeError, ValueError):
        page = 1

    products, total_count = await get_products_with_filters(
        db=db,
        category_id=category_id,
        page=page,
        per_page=per_page,
        colors=colors,
        built_in_memory=built_in_memory,
        user_id=user_id,
        favorites=favorites,
    )

    total_pages = (
        max(1, (total_count + per_page - 1) // per_page) if total_count > 0 else 1
    )
    pagination = {
        "page": page,
        "per_page": per_page,
        "total_count": total_count,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }

    return {"products": products, "pagination": pagination}


@router.get("/recommendations", response_model=RecommendOut)
async def get_recommend_products_id(
    redis_client: Redis = Depends(get_redis),
    token: str | None = Cookie(None, alias="token"),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_id = await checking_access_rights(token=token, roles=["customer"])
    except Exception:
        return RecommendOut(ids=[])

    try:
        cached = await redis_client.get(Config.REDIS_RECOMMENDATIONS_KEY)
        if cached:
            users_recs = json.loads(cached)
            ids = users_recs.get(str(user_id), [])
            logger.warning(f"[DEBUG] Raw IDs from Redis: {ids}")

            if isinstance(ids, list) and all(isinstance(x, int) for x in ids) and ids:
                verified_products = await get_product(
                    db=db,
                    product_ids=ids,
                    verify=True,
                )
                logger.warning(f"[DEBUG] Verified products: {verified_products}")
                verified_ids = [p.id for p in verified_products]
                logger.warning(f"[DEBUG] Verified IDs: {verified_ids}")
                return RecommendOut(ids=verified_ids)

    except Exception as e:
        logger.error(f"[DEBUG] Exception: {e}", exc_info=True)
        logger.warning(f"⚠️ Failed to get recommendations for user {user_id}: {e}")

    return RecommendOut(ids=[])


@router.get("/{product_id}", response_class=HTMLResponse)
async def product_detail_page(
    request: Request,
    product_id: int,
    db: AsyncSession = Depends(get_db),
    token: str | None = Cookie(default=None, alias="token"),
):
    is_authenticated = False
    is_favorite = False
    in_cart = False
    user_id = None
    role = None
    favorite_product_ids = []
    in_cart_product_ids = []

    if token and token != "None" and token != "undefined":
        try:
            current_user = await get_current_user(token)
            user_id = current_user["id"]
            role = current_user["role"]
            is_authenticated = True
            find_views = await get_views_by_product_user(
                user_id=user_id, product_id=product_id, db=db
            )

            if find_views:
                await update_views_by_product_user(
                    user_id=user_id, product_id=product_id, db=db
                )

            else:
                await create_views_product(
                    user_id=user_id, product_id=product_id, db=db
                )
            favorite_product_ids = await get_favorite_product_ids(
                user_id=current_user["id"], db=db
            )
            is_favorite = product_id in favorite_product_ids

            in_cart_product_ids = await get_in_cart_product_ids(
                user_id=current_user["id"], db=db
            )
            in_cart = product_id in in_cart_product_ids

        except jwt.ExpiredSignatureError:
            logger.error("Токен истёк")
        except jwt.InvalidTokenError as e:
            logger.error(f"Невалидный токен: {e}")
        except Exception as e:
            logger.error(f"Ошибка при проверке авторизации: {e}")

    product = await db.scalar(
        select(Product)
        .options(joinedload(Product.category))
        .options(joinedload(Product.reviews).joinedload(Review.user))
        .where(Product.id == product_id)
    )

    if not product:
        return templates.TemplateResponse(
            "exceptions/not_found.html", {"request": request}
        )

    review_count = len(product.reviews)
    avg_rating = (
        sum(r.grade for r in product.reviews) / review_count if review_count > 0 else 0
    )

    formatted_reviews = []

    for review in product.reviews:
        formatted_reviews.append(
            {
                "author": review.user.username if review.user else "Аноним",
                "date": review.comment_date.strftime("%d.%m.%Y"),
                "rating": review.grade,
                "text": review.comment,
                "images": review.photo_urls or [],
            }
        )

    recommended_result = await db.execute(
        select(Product)
        .options(joinedload(Product.category))
        .where(Product.category_id == product.category_id)
        .where(Product.id != product.id)
        .where(Product.verify == True)
    )
    recommended_products = recommended_result.unique().scalars().all()

    product.is_favorite = is_favorite
    product.in_cart = in_cart
    product.category_name = (
        product.category.name if product.category else "Без категории"
    )

    return templates.TemplateResponse(
        "products/product.html",
        {
            "request": request,
            "is_authenticated": is_authenticated,
            "user_id": user_id,
            "role": role,
            "product": product,
            "avg_rating": avg_rating,
            "reviews": formatted_reviews,
            "review_count": review_count,
            "recommended_products": recommended_products,
            "favorite_product_ids": favorite_product_ids,
            "in_cart_product_ids": in_cart_product_ids,
            "url": Config.url,
            "shop_name": Config.shop_name,
            "descr": Config.descr,
        },
    )
