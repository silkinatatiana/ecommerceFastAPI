import io
import logging

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from openpyxl import Workbook
from sqladmin import Admin, ModelView, action
from sqladmin.authentication import AuthenticationBackend
from sqladmin.helpers import secure_filename
from starlette.middleware.sessions import SessionMiddleware
from urllib.parse import parse_qsl, urlencode, urlparse

from starlette.datastructures import MultiDict
from starlette.requests import Request
from starlette.responses import StreamingResponse
from starlette.responses import RedirectResponse
from wtforms import validators

from app.kafka.producer import KafkaEventPublisher
from database.crud.users import get_user, set_users_admin
from database.db import engine, async_session_maker
from config import Config
from general_functions.auth_func import (
    bcrypt_context,
    checking_access_rights,
    create_access_token,
    get_current_user,
)
from models import (
    Cart,
    Category,
    Chats,
    Favorites,
    Messages,
    Product,
    User,
    Views, Orders,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    kafka_producer = None

    try:
        if not Config.KAFKA_HOST or not Config.GOODS_TO_BOT_TOPIC:
            logger.warning(
                "[Admin] Kafka не настроена — задайте KAFKA_HOST и GOODS_TO_BOT_TOPIC. "
                "Сейчас: KAFKA_HOST=%r, GOODS_TO_BOT_TOPIC=%r",
                Config.KAFKA_HOST,
                Config.GOODS_TO_BOT_TOPIC,
            )
            app.state.kafka_producer = None
        else:
            kafka_producer = KafkaEventPublisher()
            await kafka_producer.start()
            app.state.kafka_producer = kafka_producer
    except Exception as e:
        logger.warning("[Admin] Kafka недоступна, события товаров не отправляются: %s", e)
        app.state.kafka_producer = None

    yield

    if kafka_producer:
        try:
            await kafka_producer.stop()
        except Exception as e:
            logger.warning("Ошибка остановки Kafka: %s", e)

app = FastAPI(title="E-commerce Admin", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=Config.SECRET_KEY)


class AdminAuthBackend(AuthenticationBackend):
    async def authenticate(self, request: Request) -> bool:
        token = request.cookies.get("token") or request.session.get("token")
        if not token:
            return False
        try:
            user_id = await checking_access_rights(token=token, roles=[])
            if user_id:
                user = await get_current_user(token)
                request.state.user = user
                return True
            return False
        except HTTPException:
            return False

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        if not username or not password:
            return False
        try:
            async with async_session_maker() as db:
                user = await get_user(db=db, username=username)
                if not user or not bcrypt_context.verify(password, user.hashed_password):
                    return False
                if not user.is_admin:
                    return False
                token = create_access_token(
                    username=user.username,
                    user_id=user.id,
                    role=user.role or "admin",
                    is_admin=True,
                )
                request.session["token"] = token
                return True
        except Exception:
            return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True


class ExcelExportMixin:
    """Добавляет выгрузку в Excel (xlsx) для ModelView."""

    async def export_data(self, data, export_type: str = "csv"):
        if export_type == "xlsx":
            return await self._export_xlsx(data)
        return await super().export_data(data, export_type=export_type)

    async def _export_xlsx(self, data):
        wb = Workbook()
        ws = wb.active
        ws.title = "Export"
        headers = list(self._export_prop_names)
        ws.append(headers)
        for row in data:
            vals = [
                await self.get_prop_value(row, name)
                for name in self._export_prop_names
            ]
            ws.append(vals)
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        filename = secure_filename(self.get_export_name(export_type="xlsx"))
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )


admin = Admin(
    app=app,
    engine=engine,
    authentication_backend=AdminAuthBackend(secret_key=Config.SECRET_KEY),
)


@app.get("/")
async def root():
    return RedirectResponse(url="/admin")


class ProductAdmin(ModelView, model=Product):
    name = "Товар"
    name_plural = "Товары"

    column_list = [
        Product.id,
        Product.name,
        Product.price,
        Product.verify,
        Product.supplier,
    ]
    column_formatters = {
        Product.price: lambda m, a: f"{m.price} руб",
        Product.supplier: lambda m, a: (m.supplier.email if m.supplier else ""),
    }
    column_formatters_detail = {
        Product.price: lambda m, a: f"{m.price:,} ₽".replace(",", " "),
        Product.supplier: lambda m, a: (
            f"{m.supplier.first_name} {m.supplier.last_name}"
            if m.supplier
            else ""
        ),
    }

    form_columns = [
        Product.name,
        Product.description,
        Product.category,
        Product.price,
        Product.color,
        Product.stock,
        Product.category_id,
        Product.supplier_id,
        Product.RAM_capacity,
        Product.built_in_memory_capacity,
        Product.screen,
        Product.cpu,
        Product.number_of_processor_cores,
        Product.number_of_graphics_cores,
    ]
    form_args = {
        "name": {
            "label": "Название",
            "validators": [validators.DataRequired(), validators.Length(min=3, max=10)],
        },
        "price": {
            "label": "Цена",
            "validators": [validators.DataRequired(), validators.NumberRange(min=0)],
        },
        "description": {
            "label": "Описание",
        },
        "category": {
            "label": "Категория",
        },
        "color": {
            "label": "Цвет",
        },
        "stock": {
            "label": "Количество",
        },
    }
    form_readonly_columns = [Product.description]

    async def on_model_change(self, data, model, is_created, request):
        if data.get("price", 0) < 0:
            raise ValueError("Цена не может быть отрицательной")

    async def after_model_change(self, data, model, is_created, request):
        event = "product.created" if is_created else "product.updated"
        await self._notify_product_change(request, model, event)

    async def on_model_delete(self, model, request):
        await self._notify_product_change(request, model, "product.deleted")

    async def _notify_product_change(self, request, model, event: str) -> None:
        main_app = getattr(self, "_admin_ref", None) and getattr(self._admin_ref, "app", None)
        kafka = getattr(main_app.state, "kafka_producer", None) if main_app else None

        if not kafka:
            logger.warning(
                "Kafka не подключена при старте админки — событие %s для товара %s не отправлено",
                event,
                model.id,
            )
            return
        try:
            if event == "product.deleted":
                await kafka.send_product_event(event, model.id)
            else:
                await kafka.send_product_event(
                    event,
                    model.id,
                    data={"name": model.name, "price": float(model.price or 0)},
                )
            logger.info("Событие %s для товара %s отправлено в %s", event, model.id, Config.GOODS_TO_BOT_TOPIC)
        except Exception as e:
            logger.warning("Не удалось отправить событие %s для товара %s: %s", event, model.id, e)


class CategoryAdmin(ModelView, model=Category):
    name = "Категория"
    name_plural = "Категории"

    column_list = [Category.id, Category.name]
    column_searchable_list = [Category.name]


class ViewsAdmin(ModelView, model=Views):
    name = "Просмотры"
    name_plural = "Просмотры"

    column_list = [Views.id, Views.user_id, Views.product_id, Views.count_views]


class ChatsAdmin(ModelView, model=Chats):
    name = "Чат"
    name_plural = "Чаты"

    column_list = [
        Chats.id,
        Chats.user_id,
        Chats.employee_id,
        Chats.topic,
        Chats.created_at,
        Chats.active,
    ]
    column_searchable_list = [
        Chats.id,
        Chats.user_id,
        Chats.employee_id,
        Chats.topic,
        Chats.created_at,
        Chats.active,
    ]


class FavoritesAdmin(ModelView, model=Favorites):
    name = "Избранное"
    name_plural = "Избранное"

    column_list = [Favorites.id, Favorites.user_id, Favorites.product_id]
    column_searchable_list = [Favorites.id, Favorites.user_id, Favorites.product_id]


class MessagesAdmin(ModelView, model=Messages):
    name = "Сообщение"
    name_plural = "Сообщения"

    column_list = [
        Messages.id,
        Messages.chat_id,
        Messages.message,
        Messages.sender_id,
        Messages.created_at,
    ]
    column_searchable_list = [
        Messages.id,
        Messages.chat_id,
        Messages.message,
        Messages.sender_id,
        Messages.created_at,
    ]


class CartAdmin(ModelView, model=Cart):
    name = "Корзина"
    name_plural = "Корзина"

    column_list = [Cart.id, Cart.user_id, Cart.product_id, Cart.count]
    column_searchable_list = [Cart.id, Cart.user_id, Cart.product_id, Cart.count]


class UserAdmin(ExcelExportMixin, ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    column_list = [
        User.id,
        User.first_name,
        User.last_name,
        User.username,
        User.email,
        User.tg_id,
        User.tg_username,
        User.is_verified,
        User.is_admin,
        User.role,
    ]
    column_export_list = [
        User.id,
        User.first_name,
        User.last_name,
        User.username,
        User.email,
        User.tg_id,
        User.tg_username,
        User.is_verified,
        User.is_admin,
        User.role,
    ]
    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = True
    can_export = True
    export_types = ["csv", "json", "xlsx"]

    def is_accessible(self, request: Request) -> bool:
        user = getattr(request.state, "user", None)
        return bool(user and user.get("is_admin"))

    def can_edit(self, request: Request) -> bool:
        pk = request.path_params.get("pk")
        if not pk:
            return True
        return True

    @action(
        name="make_admin",
        label="Сделать администратором",
        confirmation_message="Назначить выбранных пользователей администраторами?",
    )
    async def make_admin_action(self, request: Request):
        """Назначить администраторами выбранных пользователей."""
        params = request.query_params.get("pks", "")
        pks = [int(pk) for pk in params.split(",")] if params else []
        if not pks and request.query_params.getlist("pks"):
            pks = [int(pk) for pk in request.query_params.getlist("pks")]
        if pks:
            async with async_session_maker() as session:
                await set_users_admin(db=session, user_ids=pks)
        path = f"/admin/{self.identity}/list"
        referer = request.headers.get("referer") or ""
        try:
            referer_params = MultiDict(parse_qsl(urlparse(referer).query))
            if referer_params:
                path = f"{path}?{urlencode(list(referer_params.items()))}"
        except Exception:
            pass
        return RedirectResponse(url=path, status_code=302)


class OrderAdmin(ExcelExportMixin, ModelView, model=Orders):
    name = "Заказ"
    name_plural = "Заказы"
    column_list = [
        Orders.id,
        Orders.user_id,
        Orders.summa,
        Orders.date,
        Orders.status,
        Orders.slug,
    ]
    column_sortable_list = [Orders.id, Orders.date, Orders.summa, Orders.status]
    can_export = True
    export_types = ["csv", "json", "xlsx"]
    column_export_list = [
        Orders.id,
        Orders.user_id,
        Orders.summa,
        Orders.date,
        Orders.status,
        Orders.slug,
    ]


admin.add_view(UserAdmin)
admin.add_view(ProductAdmin)
admin.add_view(CategoryAdmin)
admin.add_view(ViewsAdmin)
admin.add_view(ChatsAdmin)
admin.add_view(FavoritesAdmin)
admin.add_view(MessagesAdmin)
admin.add_view(CartAdmin)
admin.add_view(OrderAdmin)
