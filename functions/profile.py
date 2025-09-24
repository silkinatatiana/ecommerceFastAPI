from app.config import Config
from models import Chats, Messages
from app.routers.orders import get_orders_by_user_id
from sqlalchemy import select


async def get_tab_by_section(section, templates, request, user, page, db, user_dict):
    return_dict = {
        "request": request,
        "user": user,
        "user_id": user.id,
        "config": Config.url,
        "is_authenticated": True,
        "shop_name": Config.shop_name,
        "descr": Config.descr,
    }

    dict_tab = {
        'security_tab': 'profile/security.html',
        'orders_tab': 'profile/orders.html',
        'profile_tab': 'profile/profile.html',
        'chats_tab': 'profile/chats_list.html'
    }

    if section == 'orders_tab':
        orders_data = await get_orders_by_user_id(user_dict['id'], page, 5, db)
        return_dict.update({'orders_data': orders_data})

    elif section == 'chats_tab':
        try:
            limit = 10
            offset = (page - 1) * limit

            query = (
                select(Chats)
                .where(Chats.user_id == user.id)
                .order_by(Chats.created_at.desc())
                .offset(offset)
                .limit(limit + 1)
            )
            result = await db.execute(query)
            chats_with_extra = result.scalars().all()

            has_more = len(chats_with_extra) > limit
            chats = chats_with_extra[:limit]

            for chat in chats:
                last_msg_query = (
                    select(Messages)
                    .where(Messages.chat_id == chat.id)
                    .order_by(Messages.created_at.desc())
                    .limit(1)
                )
                chat.last_message = await db.scalar(last_msg_query)

            return_dict.update({
                'chats': chats,
                'page': page,
                'has_more': has_more,
                'next_page': page + 1 if has_more else None
            })

        except Exception as e:
            print(f"Ошибка при загрузке чатов: {e}")
            return_dict.update({
                'chats': [],
                'page': page,
                'has_more': False,
                'next_page': None
            })

    return templates.TemplateResponse(dict_tab[section], return_dict)