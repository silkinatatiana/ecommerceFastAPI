# TODO получить все отзывы

# reviews = await db.scalars(select(Review))
# return reviews.all() or []



# TODO получить все отзывы по товару

# reviews = await db.scalars(
#     select(Review)
#     .where(Review.product_id == product.id)
# )
# return reviews.all()

# TODO получить отзыв по id

# review = await db.scalar(select(Review).where(Review.id == review_id))



# TODO CREATE

# review = Review(
#     user_id=review_data.user_id,
#     product_id=product_id,
#     comment=review_data.comment,
#     grade=review_data.grade,
#     photo_urls=review_data.photo_urls or []
# )
# db.add(review)
# await db.commit()
# await db.refresh(review)