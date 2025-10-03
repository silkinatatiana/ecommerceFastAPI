from typing import Optional
from datetime import datetime
from urllib.parse import urlencode

from models import Orders


def get_sort_column(sort_by: str):
    mapping = {
        "id": Orders.id,
        "user": Orders.user_id,
        "date": Orders.date,
        "status": Orders.status,
        "summa": Orders.summa,
    }
    return mapping.get(sort_by, Orders.date)


def build_pagination_url(order_id=None,
                         user_id=None,
                         status=None,
                         date_start=None,
                         date_end=None,
                         sum_from=None,
                         sum_to=None,
                         sort_by="date",
                         sort_order="desc",
                         page=1,
                         **overrides
):
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


def build_sort_url(new_sort_by: str,
                   new_order: str,
                   order_id=None,
                   user_id=None,
                   status=None,
                   date_start=None,
                   date_end=None,
                   sum_from=None,
                   sum_to=None
):
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


def to_date_str(dt: Optional[datetime]) -> str:
    if dt:
        return dt.strftime('%Y-%m-%d')
    return ""