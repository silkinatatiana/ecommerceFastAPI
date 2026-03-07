from fastapi import FastAPI
from sqladmin import Admin, ModelView
from starlette.responses import RedirectResponse

from database.db import engine
from models import (
    Cart,
    Category,
    Chats,
    Favorites,
    Messages,
    Product,
    User,
    Views,
)


app = FastAPI(title="E-commerce Admin")

admin = Admin(app=app, engine=engine)


@app.get("/")
async def root():
    return RedirectResponse(url="/admin")


class ProductAdmin(ModelView, model=Product):
    column_list = [
        Product.id,
        Product.name,
        Product.price,
        Product.verify,
        Product.supplier,
    ]
    column_formatters = {
        Product.price: lambda m, a: f"{m.price} руб",
        Product.supplier: lambda m, a: m.supplier.email,
    }

    column_formatters_detail = {
        Product.price: lambda m, a: f"{m.price:,} ₽".replace(",", " "),
        Product.supplier: lambda m, a: (
            f"{m.supplier.first_name} {m.supplier.last_name}"
        ),
    }
    form_excluded_columns = [Product.id, Product.verify]
    # form_readonly_columns = [Product.description]


# from wtforms import Form, StringField, validators
# from sqladmin import ModelView
#
#
# class ProductForm(Form):
#     name = StringField("Название", [
#         validators.DataRequired(),
#         validators.Length(min=3, max=100)
#     ])
#     price = StringField("Цена", [
#         validators.DataRequired(),
#         validators.Regexp(r'^\d+(\.\d{1,2})?$')
#     ])

# TODO сделать кастомную валидацию на длину имени пользоваля
# class ProductAdmin(ModelView, model=Product):
#     form = ProductForm
#
#     # Асинхронная валидация
#     async def on_model_change(self, data, model, is_created, request):
#         if data["price"] < 0:
#             raise ValueError("Цена не может быть отрицательной")
#
#         # Проверка уникальности
#         existing = await self.get_object_by_field("slug", data["slug"])
#         if existing and existing.id != model.id:
#             raise ValueError("Товар с таким slug уже существует")
#
#     async def after_model_change(self, data, model, is_created, request):
#         # Отправка события в Kafka после сохранения
#         await request.app.state.kafka_producer.send_product_updated(model)
#
#     async def on_model_delete(self, model, request):
#         # Проверка перед удалением
#         if model.orders.count() > 0:
#             raise ValueError("Нельзя удалить товар с заказами")


class UserAdmin(ModelView, model=User):
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

    column_searchable_list = [
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

    column_sortable_list = [
        User.id,
        User.first_name,
        User.last_name,
        User.username,
        User.email,
        User.tg_id,
        User.tg_username,
        User.role,
    ]
    column_default_sort = ("email", False)
    page_size = 20

    column_labels = {
        User.first_name: "Имя",
        User.last_name: "Фамилия",
    }
    form_columns = [
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

    # @action(
    #     name="make_admin",
    #     label="Сделать администратором",
    #     confirmation_message="Назначить выбранных пользователей администраторами?"
    # )
    # async def make_admin_action(self, request: Request):
    #     """Назначить администраторами выбранных пользователей"""
    #     pks = request.query_params.getlist("pks")
    #
    #     if not pks:
    #         # Если ничего не выбрано — редирект с ошибкой
    #         request.session["flash_error"] = "Не выбраны пользователи"
    #         return RedirectResponse(
    #             request.url_for("admin:list", identity=self.identity),
    #             status_code=302
    #         )
    #
    #     async with self.session_maker() as session:
    #         # Массовое обновление через SQLAlchemy 2.0
    #         stmt = (
    #             update(User)
    #             .where(User.id.in_(pks))# разобраться с аргументом и вынести в общий CRUD
    #             .values(is_admin=True)
    #         )
    #         result = await session.execute(stmt)
    #         await session.commit()
    #
    #         updated_count = result.rowcount
    #
    #     # Редирект с сообщением об успехе
    #     return RedirectResponse(
    #         request.url_for("admin:list", identity=self.identity),
    #         status_code=302
    #     )


class CategoryAdmin(ModelView, model=Category):
    column_list = [Category.id, Category.name]
    column_searchable_list = [Category.name]


class ViewsAdmin(ModelView, model=Views):
    column_list = [Views.id, Views.user_id, Views.product_id, Views.count_views]


class ChatsAdmin(ModelView, model=Chats):
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
    column_list = [Favorites.id, Favorites.user_id, Favorites.product_id]
    column_searchable_list = [Favorites.id, Favorites.user_id, Favorites.product_id]


class MessagesAdmin(ModelView, model=Messages):
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
    column_list = [Cart.id, Cart.user_id, Cart.product_id, Cart.count]
    column_searchable_list = [Cart.id, Cart.user_id, Cart.product_id, Cart.count]


# class SecureAdmin(Admin):
#     async def authenticate(self, request: Request) -> bool:
#         """Проверка доступа к админке"""
#         token = request.cookies.get("admin_token")
#         if not token:
#             return False
#
#         user = await verify_admin_token(token)
#         request.state.user = user
#         return user is not None and user.is_superuser
#
#     async def get_current_user(self, request: Request):
#         return getattr(request.state, "user", None)
#
#
# # Или через middleware
# admin = Admin(
#     app,
#     engine,
#     authentication_backend=MyAuthBackend(),  # Кастомный бэкенд
#     base_url="/secret-admin"  # Кастомный путь
# )

# TODO сделать авторизацию в админке

# class UserAdmin(ModelView, model=User):
#     # Права доступа
#     can_create = True
#     can_edit = True
#     can_delete = False  # Запрет удаления
#     can_view_details = True
#     can_export = True  # Экспорт в CSV/Excel
#
#     # Динамические права
#     def is_accessible(self, request: Request) -> bool:
#         user = request.state.user
#         return user and user.has_perm("users.view_user")
#
#     def can_edit(self, request: Request) -> bool:
#         user = request.state.user
#         # Нельзя редактировать суперпользователей
#         obj = self.get_object(request, request.path_params.get("pk"))
#         return not obj.is_superuser

# TODO добавить выгрузку в эксель

# class OrderAdmin(ModelView, model=Order):
#     # Экспорт в разные форматы
#     can_export = True
#     export_types = [ExportType.CSV, ExportType.EXCEL, ExportType.JSON]
#
#     # Кастомные колонки для экспорта
#     column_export_list = [Order.id, Order.user_id, Order.total, Order.created_at]
#
#     # Форматирование для экспорта
#     column_formatters_export = {
#         Order.total: lambda m, a: float(m.total),
#         Order.created_at: lambda m, a: m.created_at.isoformat()
#     }


# TODO сделать интеграцию с кафкой для создания товаров

# class ProductAdmin(ModelView, model=Product):
#     async def after_model_change(self, data, model, is_created, request):
#         # Доступ к вашим сервисам из lifespan
#         kafka = request.app.state.kafka_producer
#         redis = request.app.state.redis
#
#         # Инвалидация кэша
#         await redis.delete(f"product:{model.id}")
#
#         # Отправка события
#         await kafka.send({
#             "event": "product.updated" if not is_created else "product.created",
#             "id": model.id,
#             "data": {
#                 "name": model.name,
#                 "price": float(model.price)
#             }
#         })
#
#     async def on_model_delete(self, model, request):
#         redis = request.app.state.redis
#         await redis.delete(f"product:{model.id}")
#         await request.app.state.kafka_producer.send({
#             "event": "product.deleted",
#             "id": model.id
#         })

admin.add_view(UserAdmin)
admin.add_view(ProductAdmin)
admin.add_view(CategoryAdmin)
admin.add_view(ViewsAdmin)
admin.add_view(ChatsAdmin)
admin.add_view(FavoritesAdmin)
admin.add_view(MessagesAdmin)
admin.add_view(CartAdmin)
