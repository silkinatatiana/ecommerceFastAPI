import time
from typing import AsyncGenerator, Optional, Annotated

from fastapi import FastAPI, Request, Query, Depends, Cookie
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.cors import CORSMiddleware
from loguru import logger
from contextlib import asynccontextmanager
import logging

from app.functions.main_func import parse_int_list, auth_user, handle_partial_request, build_full_page_context
from app.routers import category, products, auth, reviews, favorites, cart, orders, chats, messages
from app.routers.auth import auto_refresh_token
from database.db_depends import get_db
from database.db import Base, engine
from app.log.log import LOGGER
from config import Config

logger = LOGGER
logger.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


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

    if partial:
        response = await handle_partial_request(
            request, db, user_data, colors, built_in_memory, is_favorite
        )
        return templates.TemplateResponse(*response)

    context = await build_full_page_context(
        request, db, user_data, selected_category_ids,
        colors, built_in_memory, is_favorite
    )

    response = templates.TemplateResponse("index.html", context)

    if token and not user_data["is_authenticated"]:
        response.delete_cookie("token")

    return response
