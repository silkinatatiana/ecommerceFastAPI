from logging.handlers import RotatingFileHandler
import logging


LOGGER = logging.getLogger(__name__)


class ColorFormatter(logging.Formatter):
    colors = {
        'INFO': '\033[92m',
        'WARNING': '\033[93m',
        'ERROR': '\033[91m',
        'RESET': '\033[0m'
    }

    def format(self, record):
        color = self.colors.get(record.levelname, self.colors['RESET'])
        message = super().format(record)
        return f"{color}{message}{self.colors['RESET']}"


file_handler = RotatingFileHandler(
    'app/log/app.log',
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding='UTF-8'
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))

console_handler = logging.StreamHandler()
console_handler.setFormatter(ColorFormatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))

LOGGER.addHandler(file_handler)
LOGGER.addHandler(console_handler)

