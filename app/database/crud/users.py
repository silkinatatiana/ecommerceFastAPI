# TODO получить пользователя по role == 'seller'

# query_employee_ids = select(User).where(User.role == 'seller')
#         result = await db.execute(query_employee_ids)
#         employee_ids = result.scalars().all()
#
#

# TODO получить пользователя по id

#         employee = await db.scalar(select(User).where(User.id == chat.employee_id))


# TODO получить пользователя по id

#         current_user = await db.scalar(select(User).where(User.id == user_id))

# user = await db.scalar(select(User).where(User.id == user_id))


# user = await authenticate_user(db, form_data.username, form_data.password) #TODO????




# user = await db.scalar(select(User).where(User.id == user_dict['id']))
# response = await get_tab_by_section(section, templates, request, user, page, db, user_dict)



#TODO CREATE

# await db.execute(insert(User).values(
#     first_name=first_name,
#     last_name=last_name,
#     username=username,
#     email=email,
#     hashed_password=bcrypt_context.hash(password))
# )
# await db.commit()



#TODO UPDATE

# update_data = {}
#     if profile_update.first_name is not None:
#         update_data['first_name'] = profile_update.first_name
#     if profile_update.last_name is not None:
#         update_data['last_name'] = profile_update.last_name
#     if profile_update.email is not None:
#         update_data['email'] = profile_update.email
#
#     if not update_data:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail='Не указаны данные для обновления'
#         )
#
#     query = update(User).where(User.id == user['id']).values(**update_data)
#
#     try:
#         await db.execute(query)
#         await db.commit()





# user = await db.scalar(select(User).where(User.id == data_user['id']))
#
#         if not verify_password(plain_password=data.new_password,
#                                hashed_password=user.hashed_password):
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail='Неправильный пароль'
#             )
#         query = update(User).where(User.id == data_user['id']).values(hashed_password=bcrypt_context.hash(data.new_password))
#         await db.execute(query)
#         await db.commit()



