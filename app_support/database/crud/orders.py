from fastapi import HTTPException, status
from sqlalchemy import select, update, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app_support.config import Statuses
from app.models import Orders


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


async def update_status(order_id: int,
                              new_status: str,
                              db: AsyncSession):
    try:
        order = await get_orders(order_id=order_id, db=db)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Заказ с ID {order_id} не найден'
            )

        allowed_previous_status = Statuses.changing_statuses.get(new_status)
        if allowed_previous_status is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Недопустимый новый статус'
            )

        if allowed_previous_status != order.status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Недопустимый переход статуса. Текущий статус: "{order.status}"'
            )

        new_status_text = getattr(Statuses, new_status, None)
        if new_status_text is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Недопустимый новый статус'
            )

        query = update(Orders).where(Orders.id == order_id).values(status=new_status_text)
        await db.execute(query)
        await db.commit()

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных: {str(e)}"
        )







