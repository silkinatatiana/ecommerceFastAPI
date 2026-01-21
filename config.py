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
    TESTING = os.getenv('TESTING', False)
    REDIS_HOST = os.getenv('REDIS_HOST')
    REDIS_PORT = os.getenv('REDIS_PORT')
    REDIS_DB = os.getenv('REDIS_DB')
    BROKER_URL = os.getenv('BROKER_URL')
    REDIS_RECOMMENDATIONS_KEY = "recommendations_all"
    RECOMMENDATIONS_TIME = 120
    SCHEDULE_REC_MIN = "*/1"
    KAFKA_ORDERS_TOPIC = os.getenv('KAFKA_ORDERS_TOPIC')
    KAFKA_HOST = os.getenv('KAFKA_HOST')
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')
    VERIFICATED_TOPIC = os.getenv('VERIFICATED_TOPIC')
    TELEGRAM_ORDERS_TOPIC = os.getenv('TELEGRAM_ORDERS_TOPIC')
    SUPPORT_CHANGE_STATUS_TOPIC = os.getenv('SUPPORT_CHANGE_STATUS_TOPIC')


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
        # Отмена должна быть доступна из состояния "Оформлен"
        'CANCELLED': 'Оформлен'
    }
