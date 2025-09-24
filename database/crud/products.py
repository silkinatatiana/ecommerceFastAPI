# from fastapi import HTTPException, status
# from sqlalchemy import select, update
# from sqlalchemy.exc import SQLAlchemyError
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from app.models import Product
#
# # product = await db.scalar(select(Product).where(Product.id == product_id))
#
# # query = select(Product).where(Product.category_id == category_id)
# # count_query = select(func.count()).select_from(Product).where(Product.category_id == category_id)
# #
# # if colors:
# #     colors_list = [color.strip() for color in colors.split(',')]
# #     color_conditions = Product.color.in_(colors_list)
# #     query = query.where(color_conditions)
# #     count_query = count_query.where(color_conditions)
# #
# # if built_in_memory:
# #     built_in_memory_list = [memory.strip() for memory in built_in_memory.split(',')]
# #     memory_conditions = Product.built_in_memory_capacity.in_(built_in_memory_list)
# #     query = query.where(memory_conditions)
# #     count_query = count_query.where(memory_conditions)
# #
# # total_count = await db.scalar(count_query)
#
# # offset = (page - 1) * per_page
# # query = query.offset(offset).limit(per_page)
# #
# # products_result = await db.scalars(query)
# # products = products_result.all()
# #
# # if favorites:
# #     favorite_products = await db.scalars(select(Favorites).where(Favorites.user_id == user_id))
# #     favorite_products_ids = {fp.product_id for fp in favorite_products}
# #     products = [prod for prod in products if prod.id in favorite_products_ids]
# #     total_count = len(products)
#
#
# # product = await db.scalar(
# #     select(Product)
# #     .options(joinedload(Product.category))
# #     .options(joinedload(Product.reviews).joinedload(Review.user))
# #     .where(Product.id == product_id)
# # )
#
# #
# # recommended_products = await db.scalars(
# #     select(Product)
# #     .where(Product.category_id == product.category_id)
# #     .where(Product.id != product.id)
# # )
#
# # product = await db.get(Product, cart_data.product_id) # TODO ???
# # TODO из функции add_product_to_cart
#
#
#
# async def get_product(
#         db: AsyncSession,
#         product_id: int = None,
#         product_ids: list = None,
#         category_id: int = None,
#         colors: list = None,
#         built_in_memory: list = None,
#         sort_asc: bool = False,
#         sort_desc: bool = False):
#     try:
#         query = select(Product)
#
#         if category_id:
#             categ_ids = [int(categ_id) for categ_id in category_id.split(",")]
#             query = query.where(Product.category_id.in_(categ_ids))
#
#         if product_id:
#             query = query.where(Product.id == product_id)
#
#         if product_ids:
#             ids_list = [int(id_) for id_ in product_ids.split(",")]
#             query = query.where(Product.id.in_(ids_list))
#
#         if colors:
#             query = query.where(Product.color.in_(colors.split(",")))
#
#         if built_in_memory:
#             query = query.where(Product.built_in_memory_capacity.in_(built_in_memory.split(",")))
#
#         result = await db.execute(query)
#         products = result.scalars().all()
#         return products or []
#
#         if chat_id or limit == 1:
#             result = await db.scalar(query)
#
#         else:
#             chats = await db.execute(query)
#             result = chats.scalars().all()
#
#         return result
#
#     except SQLAlchemyError as e:
#         await db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Ошибка базы данных: {str(e)}"
#         )
#
#     except Exception as e:
#         await db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Не удалось выполнить запрос в БД: {str(e)}"
#         )
#
#
#
# #TODO создать продукт
#
# # product = Product(
# #     **product_data.dict(exclude_unset=True),
# #     supplier_id=1  # когда добавлю ЛК, это поле будет браться из таблицы user
# # )
# #
# # db.add(product)
# # await db.commit()
# # await db.refresh(product)
#
