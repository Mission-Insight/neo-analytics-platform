import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.config import LOG_BACKUP_COUNT, LOG_LEVEL, LOG_MAX_BYTES

PROJECT_ROOT = Path(__file__).resolve().parents[1]

LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "neows.log"


def setup_logging() -> None:
    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    handler.setFormatter(formatter)

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        handlers=[handler],
    )
