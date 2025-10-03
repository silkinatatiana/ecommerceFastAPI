from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, status, HTTPException, Request, Query, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy import select, func
import httpx
import jwt
from loguru import logger
from starlette.responses import RedirectResponse

from database.crud.category import get_category
from database.crud.products import get_product, get_products_with_filters
from database.db_depends import get_db
from schemas import CreateProduct, ProductOut
from models import *
from models import Review
from functions.cart_func import get_in_cart_product_ids
from functions.auth_func import get_current_user, get_user_id_by_token
from functions.favorites_func import get_favorite_product_ids
from app.config import Config

router = APIRouter(prefix='/products', tags=['products'])
templates = Jinja2Templates(directory='app/templates/')


@router.get("/create", response_class=HTMLResponse)
async def create_product_form(
        request: Request
):
    try:
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
                    "config": {"url": Config.url}
                }
            )

    except Exception:
        return templates.TemplateResponse(
            "products/create_product.html",
            {
                "request": request,
                "categories": [],
                "config": {"url": Config.url}
            }
        )


@router.post('/create', response_model=ProductOut)
async def create_product(
        db: Annotated[AsyncSession, Depends(get_db)],
        product_data: CreateProduct,
        token: Optional[str] = Cookie(None, alias='token')
):
    try:
        if not token:
            return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)

        supplier_id = get_user_id_by_token(token)
        category = await get_category(db=db, category_id=product_data.category_id)

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='NOT FOUND'
            )

        product = await create_product(db=db, product_data=product_data, supplier_id=supplier_id)

        return product

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/")
async def all_products(db: AsyncSession = Depends(get_db),
                       category_id: Optional[str] = Query(None),
                       colors: Optional[str] = Query(None),
                       built_in_memory: Optional[str] = Query(None),
                       product_ids: Optional[str] = Query(None)
):
    try:
        params = {}

        if category_id:
            categ_ids = [int(categ_id) for categ_id in category_id.split(",")]
            params['categ_ids'] = categ_ids

        if product_ids:
            ids_list = [int(id_) for id_ in product_ids.split(",")]
            params['ids_list'] = ids_list

        if colors:
            params['colors'] = colors.split(",")

        if built_in_memory:
            params['built_in_memory'] = built_in_memory.split(",")

        products = await get_product(db=db, **params)
        return products

    except Exception as e:
        logger.error(f"Error fetching products: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/by_category/{category_id}')
async def products_by_category(
    category_id: int,
    user_id: int,
    request: Request,
    per_page: int = Query(3, ge=1, le=50, description="Количество товаров на странице"),
    colors: str = Query(None),
    built_in_memory: str = Query(None),
    favorites: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    category = await get_category(db=db, category_id=category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Category not found'
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
        favorites=favorites
    )

    total_pages = max(1, (total_count + per_page - 1) // per_page) if total_count > 0 else 1
    pagination = {
        "page": page,
        "per_page": per_page,
        "total_count": total_count,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }

    return {
        "products": products,
        "pagination": pagination
    }


@router.get('/{product_id}', response_class=HTMLResponse)
async def product_detail_page(
        request: Request,
        product_id: int,
        db: AsyncSession = Depends(get_db),
        token: Optional[str] = Cookie(default=None, alias="token")
):
    is_authenticated = False
    is_favorite = False
    in_cart = False
    user_id = None
    favorite_product_ids = []
    in_cart_product_ids = []

    if token and token != "None" and token != "undefined":
        try:
            current_user = await get_current_user(token)
            user_id = current_user['id']
            is_authenticated = True

            favorite_product_ids = await get_favorite_product_ids(user_id=current_user['id'], db=db)
            is_favorite = product_id in favorite_product_ids

            in_cart_product_ids = await get_in_cart_product_ids(user_id=current_user['id'], db=db)
            in_cart = product_id in in_cart_product_ids

        except jwt.ExpiredSignatureError:
            print("Токен истёк")
        except jwt.InvalidTokenError as e:
            print(f"Невалидный токен: {e}")
        except Exception as e:
            print(f"Ошибка при проверке авторизации: {e}")

    product = await db.scalar(
        select(Product)
        .options(joinedload(Product.category))
        .options(joinedload(Product.reviews).joinedload(Review.user))
        .where(Product.id == product_id)
    )

    if not product:
        return templates.TemplateResponse(
            "exceptions/not_found.html",
            {"request": request}
        )

    review_count = len(product.reviews)
    avg_rating = sum(r.grade for r in product.reviews) / review_count if review_count > 0 else 0

    formatted_reviews = []

    for review in product.reviews:
        formatted_reviews.append({
            "author": review.user.username if review.user else "Аноним",
            "date": review.comment_date.strftime("%d.%m.%Y"),
            "rating": review.grade,
            "text": review.comment,
            "images": review.photo_urls or []
        })

    recommended_products = await db.scalars(
        select(Product)
        .where(Product.category_id == product.category_id)
        .where(Product.id != product.id)
    )

    spec = [product.name, product.RAM_capacity, product.built_in_memory_capacity, product.screen, product.cpu,
            product.color]

    name = ', '.join([str(s) for s in spec if s is not None])

    return templates.TemplateResponse(
        "products/product.html",
        {
            "request": request,
            "is_authenticated": is_authenticated,
            "user_id": user_id,
            "product": {
                "id": product.id,
                "name": name,
                "description": product.description,
                "price": product.price,
                "stock": product.stock,
                "image_urls": product.image_urls,
                "rating": avg_rating,
                "category_id": product.category_id,
                "category_name": product.category.name if product.category else "Без категории",
                "RAM_capacity": product.RAM_capacity,
                "built_in_memory_capacity": product.built_in_memory_capacity,
                "screen": product.screen,
                "cpu": product.cpu,
                "number_of_processor_cores": product.number_of_processor_cores,
                "number_of_graphics_cores": product.number_of_graphics_cores,
                "color": product.color,
                "is_favorite": is_favorite,
                "in_cart": in_cart
            },
            "reviews": formatted_reviews,
            "review_count": review_count,
            "recommended_products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "price": p.price,
                    "stock": p.stock,
                    "image_urls": p.image_urls
                } for p in recommended_products
            ],
            "favorite_product_ids": favorite_product_ids,
            "in_cart_product_ids": in_cart_product_ids,
            "url": Config.url,
            "shop_name": Config.shop_name,
            "descr": Config.descr,
        }
    )
