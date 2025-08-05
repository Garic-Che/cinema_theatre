from aiologger import Logger
from aiologger.handlers.streams import AsyncStreamHandler
from aiologger.formatters.base import Formatter

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DEFAULT_HANDLERS = ["console"]

# Создаем форматтер
formatter = Formatter(fmt=LOG_FORMAT)

# Создаем и настраиваем логгер
logger = Logger(name="websocket_service")

# Добавляем обработчики
if "console" in LOG_DEFAULT_HANDLERS:
    console_handler = AsyncStreamHandler()
    console_handler.formatter = formatter
    logger.add_handler(console_handler)

# Функция для получения логгера (опционально)
def get_logger():
    return logger