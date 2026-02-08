import json
import time
from contextlib import asynccontextmanager
from math import ceil
from typing import Optional, List, AsyncGenerator
from datetime import datetime
from functools import partial
import asyncio

from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI, Request, Query, Depends, Cookie
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import logging

from app.log.log import LOGGER
from app.routers.auth import auto_refresh_token
from app_support.consumer import (
    consume_orders,
    consume_support_change_orders_status,
    consume_support_verified,
)
from app_support.kafka_producer import KafkaEventPublisher
from app_support.functions.main_func import get_sort_column, build_pagination_url, build_sort_url, to_date_str
from models import Orders, User
from general_functions.auth_func import checking_access_rights
from app_support.routers import orders, auth, chats, messages
from database.db_depends import get_db
from config import Config, Statuses
from redis_client import init_redis

logger = LOGGER
logger.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    redis_client = await init_redis()
    app.state.redis = redis_client
    consumer = AIOKafkaConsumer(
        Config.ORDERS_TOPIC,
        bootstrap_servers=Config.KAFKA_HOST,
        group_id="orders-group",
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode('utf-8')),
    )

    support_consumer_verify = AIOKafkaConsumer(
        Config.TG_VERIFIED_TOPIC,
        bootstrap_servers=Config.KAFKA_HOST,
        group_id="support-bot-verified",
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode('utf-8')),
    )

    support_consumer_change_status = AIOKafkaConsumer(
        Config.CHANGE_STATUS_TOPIC_TO_SUPPORT,
        bootstrap_servers=Config.KAFKA_HOST,
        group_id="support-bot_change_status",
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode('utf-8')),
    )

    producer = KafkaEventPublisher()

    app.state.kafka_consumer = consumer
    app.state.kafka_support_consumer = support_consumer_verify
    app.state.kafka_support_change_status_consumer = support_consumer_change_status
    app.state.kafka_producer = producer
    consumer_task = None
    support_task_verify = None
    support_task_change = None

    try:
        await producer.start()
        await consumer.start()
        consumer_task = asyncio.create_task(consume_orders(consumer))
        app.state.kafka_consumer_task = consumer_task
        await support_consumer_verify.start()
        support_task_verify = asyncio.create_task(
            consume_support_verified(support_consumer_verify)
        )
        app.state.kafka_support_consumer_task = support_task_verify
        await support_consumer_change_status.start()
        support_task_change = asyncio.create_task(
            consume_support_change_orders_status(
                support_consumer_change_status,
            )
        )
        app.state.kafka_support_change_status_task = support_task_change
        yield
    except Exception as e:
        logger.exception(f"❌ Failed to start Kafka consumer: {e}")
        raise
    finally:
        if consumer_task and not consumer_task.done():
            logger.info("Cancelling consumer task...")
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                logger.info("Consumer task cancelled")
            except Exception as e:
                logger.exception(f"Error while cancelling task: {e}")

        if support_task_verify and not support_task_verify.done():
            logger.info("Cancelling support consumer task...")
            support_task_verify.cancel()
            try:
                await support_task_verify
            except asyncio.CancelledError:
                logger.info("Support consumer task cancelled")
            except Exception as e:
                logger.exception(f"Error while cancelling support task: {e}")

        if support_task_change and not support_task_change.done():
            logger.info("Cancelling support change-status consumer task...")
            support_task_change.cancel()
            try:
                await support_task_change
            except asyncio.CancelledError:
                logger.info("Support change-status consumer task cancelled")
            except Exception as e:
                logger.exception(f"Error while cancelling support change-status task: {e}")

        await producer.stop()
        await redis_client.aclose()
        await consumer.stop()
        await support_consumer_verify.stop()
        await support_consumer_change_status.stop()


class NoCacheStaticFiles(StaticFiles):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        return response


app = FastAPI(lifespan=lifespan, redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[Config.ALLOW_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="app_support/templates")
app.mount("/static", NoCacheStaticFiles(directory="app_support/static"), name="static")


app.include_router(orders.router)
app.include_router(auth.router)
app.include_router(chats.router)
app.include_router(messages.router)


app.middleware("http")(auto_refresh_token)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="My Support API",
        version="1.0.0",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "CookieAuth": {
            "type": "apiKey",
            "in": "cookie",
            "name": "token"
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if "security" not in method:
                method["security"] = [{"CookieAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            f"{request.method} {request.url.path} - "
            f"IP: {client_ip} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.2f}s"
        )
        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"ERROR: {request.method} {request.url.path} - "
            f"IP: {client_ip} - "
            f"Error: {str(e)} - "
            f"Time: {process_time:.2f}s"
        )
        raise


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
    try:
        current_employee = await checking_access_rights(token=token, roles=['support'])
    except Exception:
        return RedirectResponse(url='/auth/create')

    all_statuses = [
        value for attr, value in vars(Statuses).items()
        if attr.isupper() and not attr.startswith('__')
    ]

    result = await db.execute(select(Orders.user_id).distinct())
    users_ids = result.scalars().all()

    unique_users = []
    user_dict = {}

    if users_ids:
        users_result = await db.execute(select(User).where(User.id.in_(users_ids)))
        unique_users = users_result.scalars().all()
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