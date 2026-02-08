import logging
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from aiokafka import AIOKafkaProducer
from fastapi import Cookie, Depends, FastAPI, Query, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.cors import CORSMiddleware

import app.log.log  # noqa: F401
from app.functions.main_func import (
    auth_user,
    build_full_page_context,
    handle_partial_request,
    parse_int_list,
)
from app.routers import (
    auth,
    cart,
    category,
    chats,
    favorites,
    messages,
    orders,
    products,
    reviews,
)
from app.routers.auth import auto_refresh_token
from app_support.kafka_producer import KafkaEventPublisher
from config import Config
from database.db import Base, engine
from database.db_depends import get_db
from redis_client import init_redis


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    redis_client = None
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        redis_client = await init_redis()
        app.state.redis = redis_client

        await verification_publisher.start()
        app.state.kafka_producer = verification_publisher

        await producer.start()
        yield

    finally:
        if redis_client:
            await redis_client.aclose()
        try:
            await verification_publisher.stop()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to stop verification publisher: %s", exc)
        await producer.stop()
        try:
            await engine.dispose()
        except Exception as e:
            logger.error(f"⚠️ DB shutdown error: {e}")


class NoCacheStaticFiles(StaticFiles):
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
producer = AIOKafkaProducer(bootstrap_servers=Config.KAFKA_HOST)
verification_publisher = KafkaEventPublisher()
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", NoCacheStaticFiles(directory="app/static"), name="static")

app.include_router(products.router)
app.include_router(auth.router)
app.include_router(category.router)
app.include_router(reviews.router)
app.include_router(favorites.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(chats.router)
app.include_router(messages.router)

app.middleware("http")(auto_refresh_token)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="My client API",
        version="1.0.0",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "CookieAuth": {"type": "apiKey", "in": "cookie", "name": "token"}
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if "security" not in method:
                method["security"] = [{"CookieAuth": []}]
    app.openapi_schema = openapi_schema
    return openapi_schema


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


@app.get("/", response_class=HTMLResponse)
async def get_main_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    token: str | None = Cookie(None, alias="token"),
    category_id: str | None = Query(None),
    colors: str | None = Query(None),
    built_in_memory: str | None = Query(None),
    is_favorite: bool = Query(False),
    partial: bool = Query(False),
):
    user_data = await auth_user(token, db)
    selected_category_ids = parse_int_list(category_id)
    recommend_product_ids = []

    if token:
        try:
            async with httpx.AsyncClient(base_url=Config.url, timeout=3.0) as client:
                headers = {"Cookie": f"token={token}"}
                resp = await client.get("/products/recommendations", headers=headers)

                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        recommend_product_ids = data.get("ids", [])
                        if not isinstance(recommend_product_ids, list):
                            recommend_product_ids = []
                        recommend_product_ids = [
                            x for x in recommend_product_ids if isinstance(x, int)
                        ]
                    except Exception as e:
                        logger.warning(f"Failed to parse recommendations JSON: {e}")
                else:
                    logger.info(
                        f"Recommendations endpoint returned {resp.status_code} for user"
                    )

        except Exception as e:
            logger.warning(f"Error fetching recommendations: {e}")

    if partial:
        response = await handle_partial_request(
            request, db, user_data, colors, built_in_memory, is_favorite
        )
        return templates.TemplateResponse(*response)

    context = await build_full_page_context(
        request,
        db,
        user_data,
        selected_category_ids,
        recommend_product_ids,
        colors,
        built_in_memory,
        is_favorite,
    )

    response = templates.TemplateResponse("index.html", context)

    if token and not user_data["is_authenticated"]:
        response.delete_cookie("token")

    return response
