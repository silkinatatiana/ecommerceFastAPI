import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    Statuses = None
    url = os.getenv('URL')
    url_support = os.getenv('URL_SUPPORT')
    SECRET_KEY = os.getenv('SECRET_KEY')
    ALGORITHM = os.getenv('ALGORITHM')
    minutes = 1
    API_HOST = os.getenv('API_HOST')
    API_PORT = os.getenv('API_PORT')
    API_PORT_SUPPORT = os.getenv('API_PORT_SUPPORT')
    ALLOW_ORIGIN = os.getenv('ALLOW_ORIGIN')
    shop_name = 'PEAR'
    PAGE_SIZE = 10
    descr = os.getenv('DESCR')
    SQLALCHEMY_DATABASE_URL = os.getenv('SQLALCHEMY_DATABASE_URL')
    timedelta_token = timedelta(minutes=5)
    timedelta_refresh_token = timedelta(days=7)
    token_auto_refresh_threshold = 1


class Statuses:
    DESIGNED = 'Оформлен'
    ON_ASSEMBLY = 'На сборке'
    SENT = 'Отправлен'
    DELIVERED = 'Доставлен'
    COMPLETED = 'Завершен'
    CANCELLED = 'Отменен'

    changing_statuses = {
        # new ----------> old
        'ON_ASSEMBLY': 'Оформлен',
        'SENT': 'На сборке',
        'DELIVERED': 'Отправлен',
        'COMPLETED': 'Доставлен',
        'CANCELLED': 'Оформлен'
    }
