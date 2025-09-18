from app.config import Config
from app.routers.orders import get_orders_by_user_id


async def get_tab_by_section(section, templates, request, user, page, db, user_dict):
    return_dict = {
        "request": request,
        "user": user,
        "user_id": user.id,
        "config": Config.url,
        "is_authenticated": True
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

    return templates.TemplateResponse(dict_tab[section], return_dict)