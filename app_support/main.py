from math import ceil
from typing import Optional, List
from datetime import datetime
from functools import partial

from fastapi import FastAPI, Request, Query, Depends, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.staticfiles import StaticFiles

import app_support
from app_support.functions.main_func import get_sort_column, build_pagination_url, build_sort_url, to_date_str
from models import Orders, User
from functions.auth_func import get_current_user
from app_support.routers import orders, auth, chats, messages
from database.db_depends import get_db
from app_support.config import Config, Statuses


class NoCacheStaticFiles(StaticFiles):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        return response


app = FastAPI()
templates = Jinja2Templates(directory="app_support/templates")
app.mount("/static", NoCacheStaticFiles(directory="app_support/static"), name="static")


app.include_router(orders.router)
app.include_router(auth.router)
app.include_router(chats.router)
app.include_router(messages.router)


@app.get('/', response_class=HTMLResponse)
async def get_main_page(request: Request,
                        db: AsyncSession = Depends(get_db),
                        token: Optional[str] = Cookie(None, alias='token'),
                        status: Optional[List[str]] = Query(None),
                        user_id: Optional[List[int]] = Query(None),
                        order_id: Optional[List[int]] = Query(None),
                        date_start: Optional[str] = None,
                        date_end: Optional[str] = None,
                        sum_from: Optional[float] = None,
                        sum_to: Optional[float] = None,
                        sort_by: str = Query("date"),
                        sort_order: str = Query("desc", regex="^(asc|desc)$"),
                        page: int = Query(1, ge=1)
):
    if not token:
        return RedirectResponse(url='/auth/create')

    current_employee = await get_current_user(token=token)
    if not current_employee:
        return RedirectResponse(url='/auth/create')

    if current_employee['role'] != 'seller' and not current_employee['is_admin']:
        return RedirectResponse(url='/auth/create')

    all_statuses = [
        value for attr, value in vars(Statuses).items()
        if attr.isupper() and not attr.startswith('__')
    ]

    result = await db.execute(select(Orders.user_id).distinct())
    users_ids = result.scalars().all()

    if users_ids:
        users_result = await db.execute(select(User).where(User.id.in_(users_ids)))
        unique_users = users_result.scalars().all()
        user_dict = {user.id: user for user in unique_users}
    else:
        user_dict = {}

    all_orders_ids_result = await db.execute(select(Orders.id))
    all_order_ids = [r[0] for r in all_orders_ids_result.fetchall()]
    all_order_ids = sorted(all_order_ids, reverse=True)[:100]

    stmt = select(Orders)

    if order_id:
        stmt = stmt.where(Orders.id.in_(order_id))
    if user_id:
        stmt = stmt.where(Orders.user_id.in_(user_id))
    if status:
        valid_statuses = [s for s in status if s in all_statuses]
        if valid_statuses:
            stmt = stmt.where(Orders.status.in_(valid_statuses))

    date_start_dt = None
    date_end_dt = None
    if date_start:
        try:
            date_start_dt = datetime.fromisoformat(date_start + "T00:00:00")
            stmt = stmt.where(Orders.date >= date_start_dt)
        except ValueError:
            pass
    if date_end:
        try:
            date_end_dt = datetime.fromisoformat(date_end + "T23:59:59")
            stmt = stmt.where(Orders.date <= date_end_dt)
        except ValueError:
            pass

    if sum_from is not None:
        stmt = stmt.where(Orders.summa >= sum_from)
    if sum_to is not None:
        stmt = stmt.where(Orders.summa <= sum_to)

    sort_col = get_sort_column(sort_by)

    if sort_order == "asc":
        stmt = stmt.order_by(sort_col.asc())
    else:
        stmt = stmt.order_by(sort_col.desc())

    count_stmt = select(func.count()).select_from(Orders)
    if stmt.whereclause is not None:
        count_stmt = count_stmt.where(stmt.whereclause)
    total_count = (await db.execute(count_stmt)).scalar()
    total_pages = ceil(total_count / Config.PAGE_SIZE) if total_count else 1

    stmt = stmt.offset((page - 1) * Config.PAGE_SIZE).limit(Config.PAGE_SIZE)
    orders = (await db.execute(stmt)).scalars().all()

    date_start_date = to_date_str(date_start_dt)
    date_end_date = to_date_str(date_end_dt)

    pagination_func = partial(
        build_pagination_url,
        order_id=order_id,
        user_id=user_id,
        status=status,
        date_start=date_start,
        date_end=date_end,
        sum_from=sum_from,
        sum_to=sum_to,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page
    )

    sort_func = partial(
        build_sort_url,
        order_id=order_id,
        user_id=user_id,
        status=status,
        date_start=date_start,
        date_end=date_end,
        sum_from=sum_from,
        sum_to=sum_to,
    )

    return templates.TemplateResponse('orders/orders.html', {
        "request": request,
        "shop_name": Config.shop_name,
        "descr": Config.descr,
        "orders": orders,
        "user_dict": user_dict,
        "unique_users": unique_users,
        "unique_statuses": all_statuses,
        "all_order_ids": all_order_ids,
        "order_ids": order_id or [],
        "user_ids": user_id or [],
        "status": status or [],
        "date_start_date": date_start_date,
        "date_end_date": date_end_date,
        "sum_from": sum_from,
        "sum_to": sum_to,
        "current_sort_by": sort_by,
        "current_sort_order": sort_order,
        "page": page,
        "total_pages": total_pages,
        "is_authenticated": current_employee is not None,
        "build_pagination_url": pagination_func,
        "build_sort_url": sort_func
    })