import os

LOG_LEVEL = "DEBUG" if os.getenv("DEBUG", "False") == "True" else "INFO"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s - %(levelname)s - %(name)s: %(message)s",
            "json_ensure_ascii": False
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout",
        }
    },
    "loggers": {"": {"handlers": ["console"], "level": LOG_LEVEL}},
}
