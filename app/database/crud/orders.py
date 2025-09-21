# total_count_result = await db.execute(
#             select(func.count()).select_from(Orders).where(Orders.user_id == user_id)
#         )
#         total_count = total_count_result.scalar()


# result = await db.execute(
#             select(Orders)
#             .where(Orders.user_id == user_id)
#             .order_by(desc(Orders.date))
#             .offset(offset)
#             .limit(per_page)
#         )
#         orders = result.scalars().all()


# order = await db.scalar(select(Orders).where(Orders.id == order_id))


# order_query = select(Orders).where(
#     (Orders.id == order_id) &
#     (Orders.user_id == user_id)
# )
# order_result = await db.execute(order_query)
# order = order_result.scalar_one_or_none()


# TODO UPDATE

# query = update(Orders).where(Orders.id == order_id).values(status=Statuses.CANCELLED)
# await db.execute(query)
# await db.commit()


# TODO CREATE

# order = Orders(
#     user_id=user_id,
#     products=products_data,
#     summa=total_sum
# )
# db.add(order)
# await db.flush()
# await db.commit()



