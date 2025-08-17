import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    url = os.getenv('URL')
    SECRET_KEY = os.getenv('SECRET_KEY')
    ALGORITHM = os.getenv('ALGORITHM')
    minutes = 20
    API_HOST = os.getenv('API_HOST')
    API_PORT = os.getenv('API_PORT')


class Statuses:
    DESIGNED = 'Оформлен'
    ON_ASSEMBLY = 'На сборке'
    SENT = 'Отправлен'
    DELIVERED = 'Доставлен'
    COMPLETED = 'Завершен'
    CANCELLED = 'Отменен'
