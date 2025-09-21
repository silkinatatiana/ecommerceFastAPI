# query = await db.execute(
#     select(Cart, Product)
#     .join(Product, Cart.product_id == Product.id)
#     .where(Cart.user_id == user_id)
# )

# product = await db.get(Product, cart_data.product_id) # TODO ???


# cart_item = await db.execute(
#             select(Cart)
#             .where(Cart.user_id == user_id)
#             .where(Cart.product_id == cart_data.product_id)
#         )
#         cart_item = cart_item.scalar_one_or_none()
#
#         if cart_item:
#             cart_item.count += cart_data.count
#         else:
#             cart_item = Cart(
#                 user_id=user_id,
#                 product_id=cart_data.product_id,
#                 count=cart_data.count
#             )
#             db.add(cart_item)
#             await db.commit()


# cart_item = await db.scalar(
#             select(Cart)
#             .where(Cart.user_id == user_id)
#             .where(Cart.product_id == cart_data.product_id)
#         )




# if cart_data.add:
#     result = await update_quantity_cart_add(cart_data=cart_data, cart_item=cart_item, db=db)
# else:
#     result = await update_quantity_cart_reduce(cart_data=cart_data, cart_item=cart_item, db=db)
# return result


# cart_item = await db.scalar(
#     select(Cart)
#     .where(Cart.user_id == user_id)
#     .where(Cart.product_id == product_id)
# )
# await db.delete(cart_item)
# await db.commit()




# result = await db.execute(
#     delete(Cart).where(Cart.user_id == user_id)
# )
# await db.commit()



