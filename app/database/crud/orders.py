from fastapi import HTTPException, status
from sqlalchemy import select, update, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Statuses
from app.models import Orders


async def create_new_order(user_id: int,
                           products: dict,
                           summa: int,
                           db: AsyncSession
):
    try:
        order = Orders(
            user_id=user_id,
            products=products,
            summa=summa
        )
        db.add(order)
        await db.flush()
        await db.commit()

        return order

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


async def get_orders(db: AsyncSession,
                     order_id: int = None,
                     user_id: int = None,
                     limit: int = None,
                     offset: int = None,
                     sort_asc: bool = False,
                     sort_desc: bool = False,
                     func_count: bool = False
):
    try:
        query = select(Orders)

        if func_count:
            query = select(func.count()).select_from(Orders)

        if order_id:
            query = query.where(Orders.id == order_id)

        if user_id:
            query = query.where(Orders.user_id == user_id)

        if sort_asc:
            query = query.order_by(Orders.date.asc())

        if sort_desc:
            query = query.order_by(Orders.date.desc())

        if limit:
            query = query.limit(limit)

        if offset:
            query = query.offset(offset)

        if func_count or limit == 1 or order_id:
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


async def update_order_status(order_id: int, db: AsyncSession):
    try:
        order = await db.scalar(select(Orders).where(Orders.id == order_id))

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Заказ с ID {order_id} не найден'
            )

        if order.status != Statuses.DESIGNED:
            raise Exception(
                f"Заказ можно отменить только при статусе 'Оформлен'. Текущий статус заказа: {order.status}")

        query = update(Orders).where(Orders.id == order_id).values(status=Statuses.CANCELLED)
        await db.execute(query)
        await db.commit()

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных: {str(e)}"
        )







