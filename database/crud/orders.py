from fastapi import HTTPException, status
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from config import Statuses
from database.crud.decorators import handle_db_errors
from models import Orders


@handle_db_errors
async def create_new_order(db: AsyncSession,
                           user_id: int,
                           products: dict,
                           summa: int,

):
    order = Orders(
        user_id=user_id,
        products=products,
        summa=summa
    )
    db.add(order)
    await db.flush()
    await db.commit()

    return order


@handle_db_errors
async def get_orders(db: AsyncSession,
                     order_id: int = None,
                     user_id: int = None,
                     limit: int = None,
                     offset: int = None,
                     sort_asc: bool = False,
                     sort_desc: bool = False,
                     func_count: bool = False# добавить фильтр по статусу (может быть несколько [list])
):
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


@handle_db_errors
async def get_orders(
    db: AsyncSession,
    order_id: int = None,
    user_id: int = None,
    limit: int = None,
    offset: int = None,
    sort_asc: bool = False,
    sort_desc: bool = False,
    func_count: bool = False
):
    if func_count:
        query = select(func.count()).select_from(Orders)
        if user_id:
            query = query.where(Orders.user_id == user_id)
        result = await db.scalar(query)
        return result

    query = select(Orders)

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

    result = await db.execute(query)

    if order_id or limit == 1:
        return result.scalar_one_or_none()
    else:
        return result.scalars().all()


@handle_db_errors
async def update_status(db: AsyncSession,
                        order_id: int,
                        new_status: str
):
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





