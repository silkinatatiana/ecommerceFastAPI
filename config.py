import os
from datetime import timedelta

from dotenv import load_dotenv


load_dotenv()


class Config:
    url = os.getenv("URL")
    url_support = os.getenv("URL_SUPPORT")
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")
    minutes = 1
    API_HOST = os.getenv("API_HOST")
    API_PORT = os.getenv("API_PORT")
    API_PORT_SUPPORT = os.getenv("API_PORT_SUPPORT")
    ALLOW_ORIGIN = os.getenv("ALLOW_ORIGIN")
    shop_name = "PEAR"
    PAGE_SIZE = 10
    descr = os.getenv("DESCR")
    SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")
    timedelta_token = timedelta(minutes=5)
    timedelta_refresh_token = timedelta(days=7)
    token_auto_refresh_threshold = 1
    TESTING = os.getenv("TESTING", False)
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = os.getenv("REDIS_PORT")
    REDIS_DB = os.getenv("REDIS_DB")
    BROKER_URL = os.getenv("BROKER_URL")
    REDIS_RECOMMENDATIONS_KEY = "recommendations_all"
    RECOMMENDATIONS_TIME = 120
    SCHEDULE_REC_MIN = "*/1"

    KAFKA_HOST = os.getenv("KAFKA_HOST")

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    VERIFIED_TOPIC = os.getenv("VERIFIED_TOPIC")
    ORDERS_TOPIC = os.getenv("ORDERS_TOPIC")
    CHANGE_STATUS_TOPIC_TO_BOT = os.getenv("CHANGE_STATUS_TOPIC_TO_BOT")
    CHANGE_STATUS_TOPIC_TO_SUPPORT = os.getenv("CHANGE_STATUS_TOPIC_TO_SUPPORT")
    TG_VERIFIED_TOPIC = os.getenv("TG_VERIFIED_TOPIC")
    GOODS_TO_BOT_TOPIC = os.getenv("GOODS_TO_BOT_TOPIC")
    GOODS_VERIFY_DECISION_TOPIC = os.getenv("GOODS_VERIFY_DECISION_TOPIC")


class Statuses:
    DESIGNED = "Оформлен"
    ON_ASSEMBLY = "На сборке"
    SENT = "Отправлен"
    DELIVERED = "Доставлен"
    COMPLETED = "Завершен"
    CANCELLED = "Отменен"

    changing_statuses = {
        # new ----------> old
        "ON_ASSEMBLY": "Оформлен",
        "SENT": "На сборке",
        "DELIVERED": "Отправлен",
        "COMPLETED": "Доставлен",
        # Отмена должна быть доступна только из состояния "Оформлен"
        "CANCELLED": "Оформлен",
    }


class Topics:
    SUPPORT_KAFKA_TOPICS = (
        (Config.ORDERS_TOPIC, "support-order-created", "handle_order_created"),
        (
            Config.TG_VERIFIED_TOPIC,
            "support-bot-verified",
            "handle_telegram_verification_response",
        ),
        (
            Config.CHANGE_STATUS_TOPIC_TO_SUPPORT,
            "support-bot-change-status",
            "handle_order_status_change_request",
        ),
        (
            Config.GOODS_VERIFY_DECISION_TOPIC,
            "support-goods-verify-decision",
            "handle_goods_verify_decision",
        ),
    )

    BOT_KAFKA_TOPICS = (
        (Config.ORDERS_TOPIC, "bot-order-created", "_handle_order_created"),
        (Config.VERIFIED_TOPIC, "bot-verified", "_handle_verification_prompt"),
        (Config.CHANGE_STATUS_TOPIC_TO_BOT, "bot-change-status", "_handle_status_change_result"),
        (Config.GOODS_TO_BOT_TOPIC, "bot-goods-verify", "_handle_goods_verify"),
    )