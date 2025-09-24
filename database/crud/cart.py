from fastapi import HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from models import Cart


async def create_cart(user_id: int,
                      product_id: int,
                      count: int,
                      db: AsyncSession):
    try:
        cart_item = Cart(
                        user_id=user_id,
                        product_id=product_id,
                        count=count
                    )
        db.add(cart_item)
        await db.commit()

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных: {str(e)}"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось выполнить запрос в БД: {str(e)}"
        )

# query = await db.execute(
#     select(Cart, Product)
#     .join(Product, Cart.product_id == Product.id)
#     .where(Cart.user_id == user_id)
# )


async def get_cart(
        db: AsyncSession,
        user_id: int = None,
        product_id: int = None
):
    try:
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

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных: {str(e)}"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось выполнить запрос в БД: {str(e)}"
        )


async def update_cart_quantity(user_id: int,
                               product_id: int,
                               count: int,
                               add: bool,
                               db: AsyncSession):
    try:
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

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных: {str(e)}"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось выполнить запрос в БД: {str(e)}"
        )
# TODO написать общий функционал в декоратор и навесить на функции


async def delete_from_cart(db: AsyncSession,
                           user_id: int,
                           product_id: int = None,
                           clear_cart: bool = False,
):
    try:
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

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных: {str(e)}"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось выполнить запрос в БД: {str(e)}"
        )
