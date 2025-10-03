from fastapi import HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.decorators import handle_db_errors
from models import Cart


@handle_db_errors
async def create_cart(db: AsyncSession,
                      user_id: int,
                      product_id: int,
                      count: int,
):
    cart_item = Cart(
                    user_id=user_id,
                    product_id=product_id,
                    count=count
                )
    db.add(cart_item)
    await db.commit()


@handle_db_errors
async def get_cart(db: AsyncSession,
                   user_id: int = None,
                   product_id: int = None
):
    query = select(Cart)

    if user_id:
        query = query.where(Cart.user_id == user_id)

    if product_id:
        query = query.where(Cart.product_id == product_id)

    if product_id:
        result = await db.scalar(query)

    else:
        chats = await db.execute(query)
        result = chats.scalars().all()

    return result


@handle_db_errors
async def update_cart_quantity(db: AsyncSession,
                               user_id: int,
                               product_id: int,
                               count: int,
                               add: bool,
):
    cart_item = await db.execute(
        select(Cart)
        .where(Cart.user_id == user_id)
        .where(Cart.product_id == product_id)
    )
    cart_item = cart_item.scalar_one_or_none()

    if add:
        if cart_item:
            cart_item.count += count
        else:
            cart_item = Cart(
                user_id=user_id,
                product_id=product_id,
                count=count
            )
            db.add(cart_item)

        await db.commit()
        return {
            "product_id": cart_item.product_id,
            "new_count": cart_item.count,
            "removed": False
        }
    else:
        if cart_item.count - count <= 0:
            await db.delete(cart_item)
            await db.commit()
            return {
                "product_id": cart_item.product_id,
                "new_count": 0,
                "removed": True
            }
        else:
            cart_item.count -= count
            await db.commit()
            return {
                "product_id": cart_item.product_id,
                "new_count": cart_item.count,
                "removed": False
            }


@handle_db_errors
async def delete_from_cart(db: AsyncSession,
                           user_id: int,
                           product_id: int = None,
                           clear_cart: bool = False,
):
    if clear_cart:
        await db.execute(delete(Cart).where(Cart.user_id == user_id))
    else:
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

