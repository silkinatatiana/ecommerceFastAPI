from typing import Optional

from fastapi import APIRouter, Depends, status, HTTPException, Request, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import HTMLResponse
import httpx
import jwt

from database.crud.cart import update_cart_quantity, delete_from_cart
from database.crud.users import get_user
from database.db_depends import get_db
from app.config import Config
from models import Product
from models import Cart
from schemas import CartItem, CartUpdate
from functions.product_func import check_stock
from functions.auth_func import get_user_id_by_token
from app.exception import NotMoreProductsException

router = APIRouter(prefix="/cart", tags=["cart"])
templates = Jinja2Templates(directory="app/templates")


@router.get('/{user_id}')
async def get_cart_by_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await get_user(user_id=user_id, db=db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='NOT FOUND'
        )

    query = await db.execute( # TODO
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


@router.post('/add', status_code=status.HTTP_201_CREATED)
async def add_product_to_cart(
        cart_data: CartItem,
        db: AsyncSession = Depends(get_db),
        token: Optional[str] = Cookie(None, alias='token')
):
    try:
        if not token:
            return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)

        user_id = get_user_id_by_token(token)

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

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch('/update')
async def update_count_cart(
        cart_data: CartUpdate,
        db: AsyncSession = Depends(get_db),
        token: Optional[str] = Cookie(None, alias='token')
):
    try:
        if not token:
            return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)

        user_id = get_user_id_by_token(token)

        result = await update_cart_quantity(user_id=user_id,
                                            product_id=cart_data.product_id,
                                            count=cart_data.count,
                                            add=cart_data.add,
                                            db=db)
        return result

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
async def clear_cart(
        token: Optional[str] = Cookie(None, alias='token'),
        db: AsyncSession = Depends(get_db)
):
    try:
        user_id = get_user_id_by_token(token)
        await delete_from_cart(user_id=user_id, db=db, clear_cart=True)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при очистке корзины: {str(e)}"
        )


@router.delete('/{product_id}')
async def delete_product_from_cart(product_id: int,
                                   token: Optional[str] = Cookie(None, alias='token'),
                                   db: AsyncSession = Depends(get_db)):
    try:
        user_id = get_user_id_by_token(token)

        await delete_from_cart(user_id=user_id,
                               product_id=product_id,
                               db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при удалении товара из корзины: {str(e)}"
        )


@router.get('/', response_class=HTMLResponse)
async def get_cart_html(request: Request,
                        token: Optional[str] = Cookie(default=None, alias='token')):
    is_authenticated = False
    cart_products = []
    user_id = None

    if token and token != 'None' and token != 'undefined':
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
            user_id = payload.get("id")
            if user_id:
                is_authenticated = True

            async with httpx.AsyncClient() as client:
                response = await client.get(f"{Config.url}/cart/{user_id}")
                response.raise_for_status()

                items = response.json()

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

        except jwt.ExpiredSignatureError:
            print("Токен истёк")
        except jwt.InvalidTokenError as e:
            print(f"Невалидный токен: {e}")
        except Exception as e:
            print(f"Ошибка при проверке авторизации: {e}")

    return templates.TemplateResponse(
        "cart/cart.html",
        {
            "request": request,
            "is_authenticated": is_authenticated,
            "user_id": user_id,
            "products": cart_products,
            "url": Config.url,
            "shop_name": Config.shop_name,
            "descr": Config.descr
        }
    )
