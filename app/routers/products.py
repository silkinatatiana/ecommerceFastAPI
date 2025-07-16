from fastapi import APIRouter, Depends, status, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import Annotated
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select, insert
from urllib.parse import unquote
import httpx
from loguru import logger
import time
import uuid

from app.backend.db_depends import get_db
from app.schemas import CreateProduct, ProductOut
from app.models import *
from app.models import Review, User
from app.routers.auth import get_current_user
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
        # В случае ошибки передаем пустой список
        return templates.TemplateResponse(
            "products/create_product.html",
            {
                "request": request,
                "categories": [],
                "config": {"url": Config.url}
            }
        )

async def create_slug(db: AsyncSession, name: str) -> str:
    base_slug = slugify(name)
    unique_slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
    
    existing_product = await db.scalar(select(Product).where(Product.slug == unique_slug))
    
    if existing_product:
        unique_slug = f"{unique_slug}-{uuid.uuid4().hex[:4]}"
    
    return unique_slug

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

        slug = await create_slug(db, product_data.name)

        product = Product(
            **product_data.dict(exclude_unset=True),
            slug=slug,
            rating=0.0,
            is_active=True,
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
async def all_products(db: AsyncSession = Depends(get_db), response_model=list[ProductOut]):
    try:
        result = await db.execute(select(Product))
        products = result.scalars().all()
        return products or []
    except Exception as e:
        logger.error(f"5 - Full error: {repr(e)}")
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
        select(Product).where(Product.category_id == category.id, Product.stock > 0))
    return products_category.all()


@router.get('/{product_id}', response_class=HTMLResponse)
async def product_detail_page(
    request: Request,
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
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

    active_reviews = [r for r in product.reviews if r.is_active]
    review_count = len(active_reviews)
    avg_rating = sum(r.grade for r in active_reviews) / review_count if review_count > 0 else 0

    formatted_reviews = []
    for review in active_reviews:
        formatted_reviews.append({
            "author": review.user.username if review.user else "Аноним",
            "date": review.comment_date.strftime("%d.%m.%Y"),
            "rating": review.grade,
            "text": review.comment,
            "photo_urls": review.photo_urls.split(',') if review.photo_urls else []
        })

    recommended_products = await db.scalars(
        select(Product)
        .where(Product.category_id == product.category_id)
        .where(Product.id != product.id)
        .limit(4)
    )

    return templates.TemplateResponse(
        "products/product.html",
        {
            "request": request,
            "product": {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "stock": product.stock,
                "image_urls": product.image_urls,
                "category_id": product.category_id,
                "category_name": product.category.name if product.category else "Без категории",
                "rating": product.rating,
                "RAM_capacity": product.RAM_capacity,
                "built_in_memory_capacity": product.built_in_memory_capacity,
                "screen": product.screen,
                "cpu": product.cpu,
                "number_of_processor_cores": product.number_of_processor_cores,
                "number_of_graphics_cores": product.number_of_graphics_cores,
                "color": product.color
            },
            "reviews": formatted_reviews,
            "review_count": review_count,
            "rating": avg_rating,
            "recommended_products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "price": p.price,
                    "stock": p.stock,
                    "image_urls": p.image_urls,
                    "rating": p.rating
                } for p in recommended_products
            ],
            "shop_name": "PEAR",
            "url": Config.url,
            "descr": "Интернет-магазин электроники"
        }
    )


@router.put('/{product_slug}')
async def update_product(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str,
                         update_product_model: CreateProduct, get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get('is_supplier') or get_user.get('is_admin'):
        product_update = await db.scalar(select(Product).where(Product.slug == product_slug))
        if product_update is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='There is no product found'
            )
        if get_user.get('id') == product_update.supplier_id or get_user.get('is_admin'):
            category = await db.scalar(select(Category).where(Category.id == update_product_model.category_id))
            if category is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='There is no category found'
                )
            product_update.name = update_product_model.name
            product_update.description = update_product_model.description
            product_update.price = update_product_model.price
            product_update.image_urls = update_product_model.image_urls
            product_update.stock = update_product_model.stock
            product_update.category_id = update_product_model.category_id
            product_update.slug = slugify(update_product_model.name)

            await db.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'transaction': 'Product update is successful'
            }
        else:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You have not enough permission for this action'
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You have not enough permission for this action'
        )


@router.delete('/{product_slug}')
async def delete_product(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    product_delete = await db.scalar(select(Product).where(Product.slug == product_slug))
    if product_delete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no product found'
        )
    if get_user.get('is_supplier') or get_user.get('is_admin'):
        if get_user.get('id') == product_delete.supplier_id or get_user.get('is_admin'):
            product_delete.is_active = False
            await db.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'transaction': 'Product delete is successful'
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You have not enough permission for this action'
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You have not enough permission for this action'
        )
    
