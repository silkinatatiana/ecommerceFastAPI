import logging
import sys
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "all_logs.log"
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

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
LOGGER.propagate = False

if LOGGER.handlers:
    LOGGER.handlers.clear()

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(ColorFormatter('%(asctime)s - %(levelname)s - %(message)s'))
LOGGER.addHandler(console_handler)

file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
LOGGER.addHandler(file_handler)