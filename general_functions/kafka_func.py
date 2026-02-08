from database.crud.users import get_user


async def get_chat_ids(db) -> list:
    from app.main import logger

    support_users = await get_user(db=db, role="support")
    chat_ids = [
        user.tg_id
        for user in support_users
        if user.is_verified and user.tg_id is not None
    ]

    logger.info(f"Retrieved chat_ids from DB: {chat_ids}")
    return chat_ids