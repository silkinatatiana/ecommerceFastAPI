import io
import uuid
from typing import TypedDict

from fastapi import Depends, Form, HTTPException, UploadFile
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from database.crud.favorites import get_favorite
from database.crud.orders import get_orders
from database.crud.views import get_all_views_by_user
from database.db_depends import get_db
from models import Product
from schemas import UpdateProduct


async def check_stock(product_id: int, db: AsyncSession = Depends(get_db)):
    stock_product = await db.scalar(
        select(Product.stock).where(Product.id == product_id)
    )
    if not stock_product:
        raise ValueError("Товар отсутствует на складе")

    return stock_product


async def update_stock(
    product_id: int, count: int, add: bool = False, db: AsyncSession = Depends(get_db)
):
    if not add:
        current_count = await check_stock(product_id=product_id, db=db)

        if current_count is None:
            raise ValueError(f"Товар с ID {product_id} не найден")

        if current_count - count < 0:
            raise ValueError(f"К заказу доступно {current_count} ед. товара")

        update_query = (
            update(Product)
            .where(Product.id == product_id)
            .values(stock=Product.stock - count)
        )
    else:
        update_query = (
            update(Product)
            .where(Product.id == product_id)
            .values(stock=Product.stock + count)
        )

    await db.execute(update_query)
    await db.commit()
    return {"message": "Количество товара на складе обновлено"}


async def get_recommend_product_ids(db: AsyncSession, user_id: int) -> list[int]:
    favorites = await get_user_favorite_ids(user_id=user_id, db=db)
    orders = await get_user_order_product_ids(user_id=user_id, db=db)
    views = await get_user_viewed_product_ids(user_id=user_id, db=db)

    combined = set(favorites) & set(orders) & set(views)
    return sorted(combined)[:20]


async def get_user_favorite_ids(db: AsyncSession, user_id: int) -> list[int]:
    favorites = await get_favorite(db=db, user_id=user_id)
    favorite_ids = [int(fav.product_id) for fav in favorites]
    return favorite_ids


async def get_user_order_product_ids(db: AsyncSession, user_id: int) -> list[int]:
    all_user_orders = await get_orders(db=db, user_id=user_id)

    product_ids: list[int] = []
    for order in all_user_orders:
        if order.products and isinstance(order.products, dict):
            product_ids.extend(int(key) for key in order.products.keys())

    return list(set(product_ids))


async def get_user_viewed_product_ids(db: AsyncSession, user_id: int) -> list[int]:
    all_views_by_user = await get_all_views_by_user(db=db, user_id=user_id)
    return [view.product_id for view in all_views_by_user]


def check_rights_for_product(product: Product | None, seller_id: int):
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден",
        )

    if seller_id != product.supplier_id:
        raise HTTPException(
            status_code=403,
            detail="Товар может изменить только продавец данного товара",
        )


def update_product_from_form(form: Form, product: Product):
    raw_data = {}
    for field_name in UpdateProduct.model_fields:
        value = form.get(field_name)

        if value is None:
            continue

        if isinstance(value, str):
            value = value.strip()
            if value == "":
                value = None

        raw_data[field_name] = value

    update_data = UpdateProduct(**raw_data).model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(product, key, value)


class UploadedSupplierImage(TypedDict):
    original_filename: str
    s3_key: str
    file_url: str
    file_size: int
    content_type: str


async def upload_supplier_image_to_s3(
    file: UploadFile,
    supplier_id: int,
    s3_client,
) -> UploadedSupplierImage | None:
    if not file or not file.filename:
        return None
    if not getattr(file, "content_type", "") or not str(file.content_type).startswith(
        "image/"
    ):
        return None
    contents = await file.read()
    if not contents:
        return None
    file_ext = (file.filename or "jpg").split(".")[-1].lower() or "jpg"
    if file_ext not in ("jpg", "jpeg", "png", "webp", "gif"):
        file_ext = "jpg"
    s3_key = f"users/{supplier_id}/{uuid.uuid4()}.{file_ext}"
    extra_args = {"ContentType": file.content_type or "image/jpeg"}
    content_type = file.content_type or "image/jpeg"
    file_url = s3_client.upload_fileobj(
        fileobj=io.BytesIO(contents),
        key=s3_key,
        extra_args=extra_args,
    )
    return {
        "original_filename": file.filename or "image",
        "s3_key": s3_key,
        "file_url": file_url,
        "file_size": len(contents),
        "content_type": content_type,
    }
