from typing import Optional

from fastapi import APIRouter, Depends, status, HTTPException, Request, Cookie
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import HTMLResponse, RedirectResponse

from functions.auth_func import checking_access_rights
from database.crud.cart import update_cart_quantity, delete_from_cart
from database.db_depends import get_db
from app.config import Config
from models import Product
from models import Cart
from schemas import CartItem, CartUpdate
from functions.product_func import check_stock
from app.exception import NotMoreProductsException

router = APIRouter(prefix="/cart", tags=["cart"])
templates = Jinja2Templates(directory="app/templates")


@router.get('/{user_id}')
async def get_cart_by_user(token: Optional[str] = Cookie(None, alias='token'),
                           db: AsyncSession = Depends(get_db)
):
    try:
        user_id = await checking_access_rights(token=token, roles=['customer'])

        query = await db.execute(
            select(Cart, Product)
            .join(Product, Cart.product_id == Product.id)
            .where(Cart.user_id == user_id)
        )

        cart_items = []
        for cart, product in query.all():
            cart_dict = {k: v for k, v in cart.__dict__.items() if not k.startswith('_')}
            product_dict = {k: v for k, v in product.__dict__.items() if not k.startswith('_')}
            cart_dict['product'] = product_dict
            cart_items.append(cart_dict)

        return cart_items

    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise


@router.post('/add', status_code=status.HTTP_201_CREATED)
async def add_product_to_cart(cart_data: CartItem,
                              db: AsyncSession = Depends(get_db),
                              token: Optional[str] = Cookie(None, alias='token')
):
    try:
        user_id = await checking_access_rights(token=token, roles=['customer'])

        product = await db.get(Product, cart_data.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='NOT FOUND'
            )

        await check_stock(product_id=cart_data.product_id, db=db)

        await update_cart_quantity(user_id=user_id,
                                   product_id=cart_data.product_id,
                                   count=cart_data.count,
                                   add=True,
                                   db=db)
        return {"message": "Товар добавлен в корзину"}

    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch('/update')
async def update_count_cart(cart_data: CartUpdate,
                            db: AsyncSession = Depends(get_db),
                            token: Optional[str] = Cookie(None, alias='token')
):
    try:
        user_id = await checking_access_rights(token=token, roles=['customer'])

        result = await update_cart_quantity(user_id=user_id,
                                            product_id=cart_data.product_id,
                                            count=cart_data.count,
                                            add=cart_data.add,
                                            db=db)
        return result

    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных: {str(e)}"
        )

    except NotMoreProductsException as e:
        return str(e)

    except Exception as e:
        raise f"Ошибка в обновлении количества товара в корзине: {e}"


@router.delete('/clear', status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(token: Optional[str] = Cookie(None, alias='token'),
                     db: AsyncSession = Depends(get_db)
):
    try:
        user_id = await checking_access_rights(token=token, roles=['customer'])

        await delete_from_cart(user_id=user_id, db=db, clear_cart=True)

    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при очистке корзины: {str(e)}"
        )


@router.delete('/{product_id}')
async def delete_product_from_cart(product_id: int,
                                   token: Optional[str] = Cookie(None, alias='token'),
                                   db: AsyncSession = Depends(get_db)
):
    try:
        user_id = await checking_access_rights(token=token, roles=['customer'])

        await delete_from_cart(user_id=user_id,
                               product_id=product_id,
                               db=db)

    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при удалении товара из корзины: {str(e)}"
        )


@router.get('/', response_class=HTMLResponse)
async def get_cart_html(request: Request,
                        token: Optional[str] = Cookie(default=None, alias='token'),
                        db: AsyncSession = Depends(get_db)
):
    try:
        is_authenticated = False
        cart_products = []

        user_id = await checking_access_rights(token=token, roles=['customer'])
        role = 'customer'
        if user_id:
            is_authenticated = True
        items = await get_cart_by_user(token=token, db=db)

        for product in items:
            cart_products.append({
                "id": product['product']['id'],
                "name": product['product']['name'],
                "description": product['product']['description'],
                "price": product['product']['price'],
                "image_urls": product['product']['image_urls'],
                "count": product['count'],
                "price_mult_count": product['product']['price'] * product['count']
            })
        return templates.TemplateResponse(
            "cart/cart.html",
            {
                "request": request,
                "is_authenticated": is_authenticated,
                "user_id": user_id,
                "role": role,
                "products": cart_products,
                "url": Config.url,
                "shop_name": Config.shop_name,
                "descr": Config.descr
            }
        )
    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise
