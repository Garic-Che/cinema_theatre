# src/core/logging.py

import logging
import sys
import json
from datetime import datetime
from logging.config import dictConfig
import os

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        # Добавляем информацию об исключении, если есть
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging(sentry_dsn: str | None = None, log_level: str = "INFO"):
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JsonFormatter,
            },
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": sys.stdout,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": log_level,
        },
        "loggers": {
            "uvicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
            "app": {"handlers": ["console"], "level": log_level, "propagate": False},
        },
    }

    dictConfig(LOGGING_CONFIG)

# Инициализация логирования при импорте модуля
setup_logging(
    sentry_dsn=os.getenv("SENTRY_DSN_NOTIFICATION"),
    log_level=os.getenv("LOG_LEVEL", "INFO"),
)

# Экспортируем основной логгер
logger = logging.getLogger("app")
