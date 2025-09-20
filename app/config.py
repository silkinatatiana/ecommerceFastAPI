import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    url = os.getenv('URL')
    SECRET_KEY = os.getenv('SECRET_KEY')
    ALGORITHM = os.getenv('ALGORITHM')
    minutes = 1
    API_HOST = os.getenv('API_HOST')
    API_PORT = os.getenv('API_PORT')
    shop_name = os.getenv('SHOP_NAME')
    descr = os.getenv('DESCR')


class Statuses:
    DESIGNED = 'Оформлен'
    ON_ASSEMBLY = 'На сборке'
    SENT = 'Отправлен'
    DELIVERED = 'Доставлен'
    COMPLETED = 'Завершен'
    CANCELLED = 'Отменен'
