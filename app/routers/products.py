from fastapi import APIRouter, Depends, status, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import Annotated
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from urllib.parse import unquote
import httpx
from loguru import logger

from app.backend.db_depends import get_db
from app.schemas import CreateProduct
from app.models import *
from app.routers.auth import get_current_user
from app.config import Config


router = APIRouter(prefix='/products', tags=['products'])
templates = Jinja2Templates(directory='app/templates/')


@router.get("/create", response_class=HTMLResponse)
async def create_product_form(
        request: Request,
):
    # if not (current_user.get('is_supplier') or current_user.get('is_admin')):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Недостаточно прав для добавления товара"
    #     )
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{Config.url}/categories/")
            response.raise_for_status()
            categories = response.json()
            
            return templates.TemplateResponse(
                "products/create_product.html",
                {
                    "request": request,
                    "categories": list(categories),
                    "config": {"url": Config.url}
                }
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось загрузить данные категорий"
        )
    

    
@router.post('/create')
async def create_product(
    db: Annotated[AsyncSession, Depends(get_db)], 
    create_product: CreateProduct
):
    category = await db.scalar(
        select(Category).where(Category.id == create_product.category_id)
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Category not found'
        )

    decoded_image_url = unquote(create_product.image_url) if create_product.image_url else None

    new_product = Product(
        name=create_product.name,
        description=create_product.description,
        price=create_product.price,
        image_url=decoded_image_url,
        stock=create_product.stock,
        category_id=create_product.category_id,
        rating=0.0,
        slug=slugify(create_product.name)
    )

    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product

@router.get('/')
async def all_products(db: Annotated[AsyncSession, Depends(get_db)]):
    products = await db.scalars(select(Product).where(Product.stock > 0))
    all_products = products.all()
    return all_products


@router.get('/{category_id}')
async def product_by_category(db: Annotated[AsyncSession, Depends(get_db)], category_id: int):
    category = await db.scalar(select(Category).where(Category.id == category_id))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Category not found'
        )
    products_category = await db.scalars(
        select(Product).where(Product.category_id == category.id, Product.stock > 0))
    return products_category.all()


@router.get('/detail/{product_slug}/page', response_class=HTMLResponse)
async def product_detail_page(
    request: Request,
    product_slug: str,
    db: AsyncSession = Depends(get_db)
):
    product = await db.scalar(
        select(Product).where(Product.slug == product_slug, Product.is_active == True)
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден"
        )
    category = await db.scalar(select(Category).where(Category.id == product.category_id))
    print(1)
    print(category)
    return templates.TemplateResponse(
        "products/product.html",
        {
            "request": request,
            "product": product,
            "category": category,
            "shop_name": "PEAR",
            "url": Config.url
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
            product_update.image_url = update_product_model.image_url
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
    
