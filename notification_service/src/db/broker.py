from aio_pika import connect_robust, Connection, Channel, Queue, Message
from typing import AsyncGenerator

from core.config import settings


class RabbitMQBroker:
    def __init__(self):
        self.host: str = settings.notification_broker_host
        self.port: int = settings.notification_broker_port
        self.username: str = settings.notification_broker_username
        self.password: str = settings.notification_broker_password
        self.connection_url: str = (
            f"amqp://{self.username}:{self.password}@{self.host}:{self.port}/"
        )
        self.connection: Connection | None = None
        self.channel: Channel | None = None

    async def connect(self):
        """Установка соединения с RabbitMQ"""
        self.connection = await connect_robust(self.connection_url)
        self.channel = await self.connection.channel()

    async def declare_queue(
        self, queue: str, arguments: dict | None = None
    ) -> Queue:
        """Объявление очереди"""
        if not self.channel:
            await self.connect()

        # Создаем exchange
        await self.channel.declare_exchange(queue, type="direct", durable=True)
        # Создаем очередь
        queue_obj = await self.channel.declare_queue(
            queue, durable=True, arguments=arguments
        )
        await queue_obj.bind(exchange=queue, routing_key=queue)
        return queue_obj

    async def send_message(self, queue: str, message: str):
        """Отправка сообщения в очередь"""
        if not self.channel:
            await self.connect()

        await self.declare_queue(
            queue,
            arguments={
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": f"{queue}{settings.dlq_ending}",
            },
        )

        exchange = await self.channel.get_exchange(queue)
        await exchange.publish(
            Message(body=message.encode()),
            routing_key=queue,
        )

    async def close(self):
        """Закрытие соединения"""
        if self.connection:
            await self.connection.close()


async def get_broker() -> AsyncGenerator[RabbitMQBroker, None]:
    """
    Асинхронный генератор для внедрения зависимости RabbitMQBroker.
    """
    broker = RabbitMQBroker()
    try:
        await broker.connect()
        yield broker
    finally:
        await broker.close()
