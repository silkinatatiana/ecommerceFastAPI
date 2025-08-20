from typing import Annotated, Optional

from fastapi import APIRouter, Depends, status, HTTPException, Request, Query, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select
import httpx
import jwt
from loguru import logger

from app.backend.db_depends import get_db
from app.schemas import CreateProduct, ProductOut
from app.models import *
from app.models import Review
from app.functions import get_current_user
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

    except Exception as e:
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
        product_data: CreateProduct
):
    try:
        category = await db.scalar(
            select(Category).where(Category.id == product_data.category_id)
        )
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Категория не найдена"
            )

        product = Product(
            **product_data.dict(exclude_unset=True),
            supplier_id=1  # когда добавлю ЛК, это поле будет браться из таблицы user
        )

        db.add(product)
        await db.commit()
        await db.refresh(product)

        return product

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/")
async def all_products(
        db: AsyncSession = Depends(get_db),
        category_id: Optional[str] = Query(None),
        colors: Optional[str] = Query(None),
        built_in_memory: Optional[str] = Query(None),
        product_ids: Optional[str] = Query(None)
):
    try:
        query = select(Product)

        if category_id:
            categ_ids = [int(categ_id) for categ_id in category_id.split(",")]
            query = query.where(Product.category_id.in_(categ_ids))

        if product_ids:
            ids_list = [int(id_) for id_ in product_ids.split(",")]
            query = query.where(Product.id.in_(ids_list))

        if colors:
            query = query.where(Product.color.in_(colors.split(",")))

        if built_in_memory:
            query = query.where(Product.built_in_memory_capacity.in_(built_in_memory.split(",")))

        result = await db.execute(query)
        products = result.scalars().all()
        return products or []

    except Exception as e:
        logger.error(f"Error fetching products: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/by_category/{category_id}')
async def products_by_category(db: Annotated[AsyncSession, Depends(get_db)], category_id: int):
    category = await db.scalar(select(Category).where(Category.id == category_id))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Category not found'
        )
    products_category = await db.scalars(
        select(Product).where(Product.category_id == category.id))
    return products_category.all()


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

    if token and token != "None" and token != "undefined":
        try:
            current_user = await get_current_user(token)
            is_authenticated = True

            favorite = await db.scalar(
                select(Favorites).where(
                    Favorites.user_id == current_user['id'],
                    Favorites.product_id == product_id
                )
            )
            is_favorite = favorite is not None

            cart = await db.scalar(
                select(Cart).where(
                    Cart.user_id == current_user['id'],
                    Cart.product_id == product_id
                )
            )
            in_cart = cart is not None

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден"
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
            "photo_urls": review.photo_urls if review.photo_urls else []
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
            "shop_name": "PEAR",
            "url": Config.url,
            "descr": "Интернет-магазин электроники"
        }
    )


# @router.put('/{product_slug}')
# async def update_product(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str,
#                          update_product_model: CreateProduct, get_user: Annotated[dict, Depends(get_current_user)]):
#     if get_user.get('is_supplier') or get_user.get('is_admin'):
#         product_update = await db.scalar(select(Product).where(Product.slug == product_slug))
#         if product_update is None:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail='There is no product found'
#             )
#         if get_user.get('id') == product_update.supplier_id or get_user.get('is_admin'):
#             category = await db.scalar(select(Category).where(Category.id == update_product_model.category_id))
#             if category is None:
#                 raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND,
#                     detail='There is no category found'
#                 )
#             product_update.name = update_product_model.name
#             product_update.description = update_product_model.description
#             product_update.price = update_product_model.price
#             product_update.image_urls = update_product_model.image_urls
#             product_update.stock = update_product_model.stock
#             product_update.category_id = update_product_model.category_id
#             product_update.slug = slugify(update_product_model.name)

#             await db.commit()
#             return {
#                 'status_code': status.HTTP_200_OK,
#                 'transaction': 'Product update is successful'
#             }
#         else:

#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail='You have not enough permission for this action'
#             )
#     else:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail='You have not enough permission for this action'
#         )


# @router.delete('/{product_slug}')
# async def delete_product(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str,
#                          get_user: Annotated[dict, Depends(get_current_user)]):
#     product_delete = await db.scalar(select(Product).where(Product.slug == product_slug))
#     if product_delete is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail='There is no product found'
#         )
#     if get_user.get('is_supplier') or get_user.get('is_admin'):
#         if get_user.get('id') == product_delete.supplier_id or get_user.get('is_admin'):
#             product_delete.is_active = False
#             await db.commit()
#             return {
#                 'status_code': status.HTTP_200_OK,
#                 'transaction': 'Product delete is successful'
#             }
#         else:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail='You have not enough permission for this action'
#             )
#     else:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail='You have not enough permission for this action'
#         )

@router.get("/by_category/")
async def get_products_by_category(
        request: Request,
        db: AsyncSession = Depends(get_db),
        category_id: int = Query(..., alias="categoryId"),
        skip: int = Query(6, alias="skip"),
        is_favorite: bool = Query(False, alias="isFavorite"),
        user_id: Optional[int] = Query(None)
):
    try:
        # Базовые параметры для запроса продуктов
        params = {'category_id': category_id}

        # Если включен фильтр "Избранное" и есть user_id
        if is_favorite and user_id:
            # 1. Получаем все избранные товары пользователя
            fav_query = select(Favorites.product_id).where(Favorites.user_id == user_id)
            fav_result = await db.execute(fav_query)
            all_favorites = fav_result.scalars().all()

            if not all_favorites:
                return []  # Нет избранных товаров вообще

            # 2. Получаем товары из нужной категории, которые есть в избранном
            products_query = select(Product.id).where(
                Product.id.in_(all_favorites),
                Product.category_id == category_id
            )
            products_result = await db.execute(products_query)
            valid_products = products_result.scalars().all()

            if not valid_products:
                return []  # Нет избранных товаров в этой категории

            params['product_ids'] = ','.join(map(str, valid_products))

        # Делаем запрос к основному API продуктов
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{Config.url}/products/",
                params=params
            )
            response.raise_for_status()
            products = response.json()

            return products[skip - 1:] if skip <= len(products) else []

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Product service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Request processing error: {str(e)}"
        )
