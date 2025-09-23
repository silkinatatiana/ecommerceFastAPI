class Config:
    url = 'http://127.0.0.1:8001'
    minutes = 1
    API_PORT = 8001
    shop_name = 'PEAR'
    descr = 'Магазин техники и электроники'


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