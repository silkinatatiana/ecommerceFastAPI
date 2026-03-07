import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Request, status
from fastapi.templating import Jinja2Templates
from slugify import slugify
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse, RedirectResponse

from app.routers.cart import get_cart_by_user
from config import Config, Statuses
from database.crud.decorators import handler_base_errors
from database.crud.orders import get_orders, update_status
from database.crud.products import get_product
from database.db_depends import get_db
from general_functions.auth_func import checking_access_rights
from general_functions.kafka_func import get_chat_ids
from general_functions.orders_func import fetch_orders_for_user
from general_functions.product_func import update_stock
from schemas import OrderResponse


router = APIRouter(prefix="/orders", tags=["orders"])
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


@router.get("/user/{user_id}")
async def get_orders_by_user_id(
    user_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(5, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    token: str | None = Cookie(None, alias="token"),
):
    try:
        user_id_from_token = await checking_access_rights(
            token=token, roles=["customer"]
        )

        if user_id != user_id_from_token:
            raise HTTPException(
                status_code=403, detail="Недостаточно прав для просмотра заказов"
            )

        return await fetch_orders_for_user(user_id, page, per_page, db)

    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise


@router.get("/{slug}", response_model=OrderResponse)
async def get_order_by_slug(
    slug: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: str | None = Cookie(None, alias="token"),
):
    try:
        await checking_access_rights(token=token, roles=["customer"])

        order = await get_orders(order_slug=slug, db=db)

        if not order:
            return templates.TemplateResponse(
                "exceptions/not_found.html", {"request": request}
            )
        return order

    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_order(
    request: Request,
    token: str | None = Cookie(None, alias="token"),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_id = await checking_access_rights(token=token, roles=["customer"])
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
            )

        order_products = await get_cart_by_user(token=token, db=db)
        if not order_products:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Корзина пуста"
            )

        products_data = {}
        positions = []
        total_sum = 0
        total_count = 0

        for item in order_products:
            pid = str(item["product_id"])
            price = item["product"]["price"]
            count = item["count"]
            products_data[pid] = {"price": price, "count": count}

            total_sum += price * count
            total_count += count
            positions.append(
                {
                    "product_id": item["product_id"],
                    "name": item["product"].get("name"),
                    "count": count,
                    "price": price,
                    "subtotal": price * count,
                }
            )

        slug = slugify(f"order-{datetime.utcnow():%Y%m%d}-{str(uuid.uuid4())[:6]}")

        chat_ids = await get_chat_ids(db=db)

        payload = {
            "user_id": user_id,
            "products": products_data,
            "total_sum": total_sum,
            "total_count": total_count,
            "slug": slug,
            "created_at": datetime.utcnow().isoformat(),
            "positions": positions,
            "chat_ids": chat_ids,
            "status_text": Statuses.DESIGNED,
        }

        await request.app.state.kafka_producer.send_order(payload)

    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise

    except Exception as e:
        logger.exception("Ошибка при подготовке заказа")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания заказа: {str(e)}",
        ) from e


@router.patch("/cancel_order/{order_id}")
async def cancel_order(
    order_id: int,
    token: str | None = Cookie(None, alias="token"),
    db: AsyncSession = Depends(get_db),
):
    try:
        await checking_access_rights(token=token, roles=["customer"])

        await update_status(order_id=order_id, db=db, new_status="CANCELLED")

        order = await get_orders(db=db, order_id=order_id)

        for product_id, product_info in order.products.items():
            await update_stock(
                product_id=int(product_id), count=product_info["count"], db=db, add=True
            )
        return f"Заказ № {order_id} отменен"

    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise

    except SQLAlchemyError as e:
        logger.error(f"Общая ошибка SQLAlchemy: {e}")
        await db.rollback()

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла внутренняя ошибка при отмене заказа",
        ) from None


@router.get("/order/{order_slug}", response_class=HTMLResponse)
@handler_base_errors
async def order_page(
    request: Request,
    order_slug: str,
    token: str | None = Cookie(default=None, alias="token"),
    db: AsyncSession = Depends(get_db),
):
    is_authenticated = False
    try:
        user_id = await checking_access_rights(token=token, roles=["customer"])
        role = "customer"

        if user_id:
            is_authenticated = True
        order = await get_orders(order_slug=order_slug, db=db)

        if not order:
            return templates.TemplateResponse(
                "exceptions/not_found.html", {"request": request}
            )

        order_products = []
        total_amount = 0

        for product_id, product_data in order.products.items():
            product = await get_product(db=db, product_id=int(product_id))
            if product:
                item_total = product_data["count"] * product_data["price"]
                order_products.append(
                    {
                        "id": product.id,
                        "name": product.name,
                        "price": product_data["price"],
                        "count": product_data["count"],
                        "image_url": (product.image_urls or [None])[0],
                        "item_total": item_total,
                    }
                )
                total_amount += item_total

        order.created_at = order.date.strftime("%Y-%m-%d %H:%M")
        order.total_sum = order.summa

        context = {
            "request": request,
            "order": order,
            "products": order_products,
            "total_amount": total_amount,
            "is_authenticated": is_authenticated,
            "user_id": user_id,
            "role": role,
            "shop_name": Config.shop_name,
            "descr": Config.descr,
        }
        return templates.TemplateResponse("orders/order_page.html", context)

    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/auth/create", status_code=303)
        raise
