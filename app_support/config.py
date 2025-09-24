class Config:
    Statuses = None
    url = 'http://127.0.0.1:8001'
    minutes = 1
    API_PORT = 8001
    shop_name = 'PEAR'
    descr = 'Магазин техники и электроники'
    SECRET_KEY = 'a7c3da68e483259507f3857aa85a9379e0cde15a7e4aebd846f957651c748628'
    ALGORITHM = 'HS256'


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