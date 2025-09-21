# result = await db.execute(
#     select(Favorites)
#     .where(Favorites.user_id == user_id)
# )
#
# favorites = result.scalars().all()



# existing_favorite = await db.execute(
#         select(Favorites)
#         .where(
#             Favorites.user_id == user_id,
#             Favorites.product_id == product_id
#         )
#     )
#     existing_favorite = existing_favorite.scalar_one_or_none()


#TODO CREATE

# new_favorite = Favorites(
#     user_id=user_id,
#     product_id=product_id
# )
#
# db.add(new_favorite)
# await db.commit()
# await db.refresh(new_favorite)



#TODO DELETE

# stmt = (
#             delete(Favorites).where(
#                 Favorites.user_id == user_id,
#                 Favorites.product_id == product_id,
#             )
#         )
#         result = await db.execute(stmt)
#         await db.commit()
#
#         if result.rowcount == 0:
#             return {'message': 'Товар удален из избранного'}
#         return None