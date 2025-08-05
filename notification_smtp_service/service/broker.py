import logging
import asyncio
from typing import AsyncGenerator
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager

import aio_pika
from aio_pika.abc import AbstractChannel, AbstractConnection
from aio_pika.exceptions import AMQPConnectionError

from core.config import settings


class MessageBroker(ABC):
    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    def get_message(self, queue_name: str) -> AsyncGenerator[bytes, None]:
        pass


class RabbitMQBroker(MessageBroker):
    connection: AbstractConnection | None
    channel: AbstractChannel | None

    def __init__(self, url):
        self.url = url
        self.connection = None
        self.channel = None

    async def connect(self) -> None:
        while True:
            try:
                self.connection = await aio_pika.connect_robust(self.url)
                self.channel = await self.connection.channel()
            except AMQPConnectionError:
                period = settings.smtp_queue_reconnection_period
                logging.error(
                    f"error while connecting to smtp queue. reconnecting in {period} seconds"
                )
                await asyncio.sleep(period)
            else:
                logging.info("connected to smtp queue")
                break

    async def get_message(
        self, queue_name: str
    ) -> AsyncGenerator[bytes, None]:
        queue = await self.channel.declare_queue(
            queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": f"{queue_name}{settings.dlq_ending}",
            },
        )
        async for message in queue.iterator():
            async with message.process():
                yield message.body

    async def close(self):
        if self.connection:
            await self.connection.close()
        if self.channel:
            await self.channel.close()


@asynccontextmanager
async def get_message_broker():
    url = settings.get_rabbitmq_connection_string()
    message_broker = RabbitMQBroker(url)
    await message_broker.connect()
    try:
        yield message_broker
    finally:
        await message_broker.close()
