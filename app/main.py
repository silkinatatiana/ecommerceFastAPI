import time
from typing import AsyncGenerator, Optional, Annotated

from fastapi import FastAPI, Request, Query, Depends, Cookie
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path

from config import Config
from app.functions.main_func import parse_int_list, auth_user, handle_partial_request, build_full_page_context
from app.routers import category, products, auth, reviews, favorites, cart, orders, chats, messages
from app.routers.auth import auto_refresh_token
from database.db import engine, Base
from database.db_depends import get_db
from general_functions.product_func import get_recommend_product_ids
from redis_client import init_redis

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
LOGGER.propagate = False

if LOGGER.handlers:
    LOGGER.handlers.clear()


class ColorFormatter(logging.Formatter):
    colors = {
        'INFO': '\033[92m',
        'WARNING': '\033[93m',
        'ERROR': '\033[91m',
        'RESET': '\033[0m'
    }

    def format(self, record):
        color = self.colors.get(record.levelname, self.colors['RESET'])
        message = super().format(record)
        return f"{color}{message}{self.colors['RESET']}"


console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(ColorFormatter('%(asctime)s - %(levelname)s - %(message)s'))
LOGGER.addHandler(console_handler)


if not Config.TESTING:
    LOG_DIR = Path("logs")
    LOG_DIR.mkdir(exist_ok=True)
    LOG_FILE = LOG_DIR / "all_logs.log"

    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    LOGGER.addHandler(file_handler)

logger = LOGGER


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        async with engine.begin() as conn:
            #  TODO тогда сначала build. Добавить Celery  и Flowers в docker-compose (обновить requirements.txt)
            #  TODO создать таску в селери, которая будет формировать json {user_id: recommend_ids}
            await conn.run_sync(Base.metadata.create_all)

        redis_client = await init_redis()
        app.state.redis = redis_client
        yield

    finally:
        await redis_client.aclose()
        try:
            await engine.dispose()
        except Exception as e:
            print(f"⚠️ DB shutdown error: {e}")


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


@app.get('/', response_class=HTMLResponse)
async def get_main_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Optional[str] = Cookie(None, alias='token'),
    category_id: Optional[str] = Query(None),
    colors: Optional[str] = Query(None),
    built_in_memory: Optional[str] = Query(None),
    is_favorite: bool = Query(False),
    partial: bool = Query(False)
):
    user_data = await auth_user(token, db)
    selected_category_ids = parse_int_list(category_id)
    recommend_product_ids = await get_recommend_product_ids(db=db, user_id=user_data["user_id"])

    if partial:
        response = await handle_partial_request(
            request, db, user_data, colors, built_in_memory, is_favorite
        )
        return templates.TemplateResponse(*response)

    context = await build_full_page_context(
        request, db, user_data, selected_category_ids, recommend_product_ids,
        colors, built_in_memory, is_favorite
    )

    response = templates.TemplateResponse("index.html", context)

    if token and not user_data["is_authenticated"]:
        response.delete_cookie("token")

    return response