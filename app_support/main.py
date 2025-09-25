from math import ceil
from typing import Optional, List
from datetime import datetime
from urllib.parse import urlencode

from fastapi import FastAPI, Request, HTTPException, Query, Depends, Cookie
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.staticfiles import StaticFiles

from models import Orders, User
from functions.auth_func import get_current_user
from app_support.routers import orders, auth #chats, messages
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
# app.include_router(chats.router)
# app.include_router(messages.router)


@app.get('/', response_class=HTMLResponse)
async def get_main_page(request: Request, # TODO доступна только авторизованным + role == seller or is_admin == True
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
    current_employee = None
    if token:
        try:
            current_employee = await get_current_user(token=token)
        except HTTPException:
            current_employee = None

    all_statuses = [
        value for attr, value in vars(Statuses).items()
        if attr.isupper() and not attr.startswith('__')
    ]

    users_result = await db.execute(select(User))
    unique_users = users_result.scalars().all() # TODO выводить только тех юзеров, где есть заказы в crud с заказами
    user_dict = {user.id: user for user in unique_users}

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

    sort_column_map = { #TODO вынести в отдельную функцию 107-120
        "id": Orders.id,
        "user": Orders.user_id,
        "date": Orders.date,
        "status": Orders.status,
        "summa": Orders.summa,
    }
    sort_col = sort_column_map.get(sort_by, Orders.date)

    if sort_order == "asc":
        stmt = stmt.order_by(sort_col.asc())
    else:
        stmt = stmt.order_by(sort_col.desc())

    PAGE_SIZE = 10 # TODO вывести в отдельную переменную
    count_stmt = select(func.count()).select_from(Orders)
    if stmt.whereclause is not None:
        count_stmt = count_stmt.where(stmt.whereclause)
    total_count = (await db.execute(count_stmt)).scalar()
    total_pages = ceil(total_count / PAGE_SIZE) if total_count else 1

    stmt = stmt.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE)
    orders = (await db.execute(stmt)).scalars().all()

    def to_date_str(dt: Optional[datetime]) -> str:
        if dt:
            return dt.strftime('%Y-%m-%d')
        return ""

    date_start_date = to_date_str(date_start_dt)
    date_end_date = to_date_str(date_end_dt)

    def build_pagination_url(**overrides): # TODO вынести все функции из роута, если короткие - переписать в lambda
        params = {}
        if order_id: params['order_id'] = order_id
        if user_id: params['user_id'] = user_id
        if status: params['status'] = status
        if date_start: params['date_start'] = date_start
        if date_end: params['date_end'] = date_end
        if sum_from is not None: params['sum_from'] = str(sum_from)
        if sum_to is not None: params['sum_to'] = str(sum_to)
        params['sort_by'] = sort_by
        params['sort_order'] = sort_order
        params['page'] = overrides.get('page', page)

        clean = {k: v for k, v in params.items() if v is not None and v != ""}
        query = urlencode(clean, doseq=True)
        return f"/?{query}" if query else "/"

    def build_sort_url(new_sort_by: str, new_order: str):
        params = {}
        if order_id: params['order_id'] = order_id
        if user_id: params['user_id'] = user_id
        if status: params['status'] = status
        if date_start: params['date_start'] = date_start
        if date_end: params['date_end'] = date_end
        if sum_from is not None: params['sum_from'] = str(sum_from)
        if sum_to is not None: params['sum_to'] = str(sum_to)
        params['sort_by'] = new_sort_by
        params['sort_order'] = new_order
        params['page'] = 1

        clean = {k: v for k, v in params.items() if v is not None and v != ""}
        query = urlencode(clean, doseq=True)
        return f"/?{query}" if query else "/"

    return templates.TemplateResponse('orders.html', {
        "request": request,
        "shop_name": Config.shop_name, # TODO объединить в объекты по логике переменных
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
        "build_pagination_url": build_pagination_url,
        "build_sort_url": build_sort_url,
    })