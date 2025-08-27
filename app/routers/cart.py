from typing import Optional

from fastapi import APIRouter, Depends, status, HTTPException, Request, Cookie
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import HTMLResponse, Response
import httpx
import jwt

from app.backend.db_depends import get_db
from app.config import Config
from app.models import Product
from app.models.cart import Cart
from app.models.users import User
from app.schemas import CartItem, CartUpdate
from app.functions.product_func import check_stock
from app.functions.auth_func import get_user_id_by_token
from app.functions.cart_func import update_quantity_cart_add, update_quantity_cart_reduce
from app.exception import NotMoreProductsException

router = APIRouter(prefix="/cart", tags=["cart"])
templates = Jinja2Templates(directory="app/templates")


@router.get('/{user_id}')
async def get_cart_by_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.id == user_id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='NOT FOUND'
        )

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


@router.post('/add', status_code=status.HTTP_201_CREATED)
async def add_product_to_cart(
        cart_data: CartItem,
        db: AsyncSession = Depends(get_db),
        token: Optional[str] = Cookie(None, alias='token')
):
    try:
        if not token:
            raise HTTPException(status_code=401, detail="Не авторизован")

        user_id = get_user_id_by_token(token)

        product = await db.get(Product, cart_data.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='NOT FOUND'
            )

        await check_stock(product_id=cart_data.product_id, db=db)

        cart_item = await db.execute(
            select(Cart)
            .where(Cart.user_id == user_id)
            .where(Cart.product_id == cart_data.product_id)
        )
        cart_item = cart_item.scalar_one_or_none()

        if cart_item:
            cart_item.count += cart_data.count
        else:
            cart_item = Cart(
                user_id=user_id,
                product_id=cart_data.product_id,
                count=cart_data.count
            )
            db.add(cart_item)

        await db.commit()
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
            raise HTTPException(status_code=401, detail="Не авторизован")

        user_id = get_user_id_by_token(token)

        cart_item = await db.scalar(
            select(Cart)
            .where(Cart.user_id == user_id)
            .where(Cart.product_id == cart_data.product_id)
        )

        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='NOT FOUND'
            )

        if cart_data.add:
            result = await update_quantity_cart_add(cart_data=cart_data, cart_item=cart_item, db=db)
        else:
            result = await update_quantity_cart_reduce(cart_data=cart_data, cart_item=cart_item, db=db)
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


@router.delete('/{product_id}')
async def delete_product_from_cart(product_id: int,
                                   token: Optional[str] = Cookie(None, alias='token'),
                                   db: AsyncSession = Depends(get_db)):
    try:
        user_id = get_user_id_by_token(token)

        cart_item = await db.scalar(
            select(Cart)
            .where(Cart.user_id == user_id)
            .where(Cart.product_id == product_id)
        )
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='NOT FOUND'
            )

        await db.delete(cart_item)
        await db.commit()

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка базы данных: {str(e)}"
        )


@router.post('/clear')  # TODO переписать вместе на delete(422)
async def clear_cart(
        token: Optional[str] = Cookie(None, alias='token'),
        db: AsyncSession = Depends(get_db)
):
    try:
        user_id = get_user_id_by_token(token)

        result = await db.execute(
            delete(Cart).where(Cart.user_id == user_id)
        )
        await db.commit()

        if result.rowcount == 0:
            return Response(status_code=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при очистке корзины: {str(e)}"
        )


@router.get('/', response_class=HTMLResponse)
async def get_cart_html(request: Request,
                        token: Optional[str] = Cookie(default=None, alias='token')):
    is_authenticated = False
    cart_products = []

    if token and token != 'None' and token != 'undefined':
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
            user_id = payload.get("id")

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
            "products": cart_products,
            "shop_name": "PEAR",
            "url": Config.url,
            "descr": "Интернет-магазин электроники"
        }
    )
