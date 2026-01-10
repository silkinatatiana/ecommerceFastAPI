import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load bot-specific env first (if exists), then fallback to default .env
load_dotenv(dotenv_path=os.getenv("BOT_ENV_FILE", ".env.bot"), override=False)
load_dotenv(override=False)


def _clean(value: str | None) -> str:
    # Trim quotes/spaces that may be pasted into env
    if value is None:
        return ""
    return value.strip().strip('"').strip("'")


@dataclass
class BotConfig:
    TELEGRAM_BOT_TOKEN: str = _clean(os.getenv("TELEGRAM_BOT_TOKEN"))
    KAFKA_HOST: str = _clean(os.getenv("KAFKA_HOST")) or "kafka:9092"
    SUPPORT_TOPIC: str = _clean(os.getenv("SUPPORT_TOPIC")) or "user_auth_events"

