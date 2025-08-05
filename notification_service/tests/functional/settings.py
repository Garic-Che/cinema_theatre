from pydantic_settings import BaseSettings

from tests.functional.utils.helpers import (
    DBSettings,
    RabbitMQSettings,
    ServiceSettings,
)


db_settings = DBSettings()
rabbitmq_settings = RabbitMQSettings()
service_settings = ServiceSettings()


class TestSettings(BaseSettings):
    rabbit_queue: str = "notification_worker"


test_settings = TestSettings(rabbit_queue="notification_worker")
