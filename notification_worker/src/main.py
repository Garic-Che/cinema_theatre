import json
import logging
import asyncio
from typing import Dict, Any
import datetime

from aio_pika import IncomingMessage, Message, DeliveryMode
from aio_pika.abc import AbstractChannel, AbstractQueue
import backoff
from aio_pika.exceptions import (
    AMQPConnectionError,
    AMQPChannelError,
    AMQPException,
    QueueEmpty,
    ChannelInvalidStateError,
)

from core.config import settings
from db.db_engine import get_db_engine
from db.rabbitmq import RabbitMQConnectionPool


class NotificationWorker:
    def __init__(self):
        self.connection = None
        self.db_engine = None
        self.connection_pool = RabbitMQConnectionPool()

    @classmethod
    async def create(cls):
        """Асинхронный конструктор для создания экземпляра класса"""
        instance = cls()
        await instance.connection_pool.initialize()
        instance.connection = (
            await instance.connection_pool.acquire_connection()
        )
        instance.db_engine = await get_db_engine()
        return instance

    @backoff.on_exception(
        backoff.expo,
        exception=(
            ConnectionError,
            ConnectionRefusedError,
            ConnectionResetError,
            TimeoutError,
        ),
        max_time=60,
    )
    async def process_message(self, message: IncomingMessage) -> None:
        """Обработка входящего сообщения"""
        try:
            async with message.process():
                body = message.body.decode()
                logging.info(f"Получено сообщение: {body}")

                # Парсим входящее JSON-сообщение
                try:
                    data = json.loads(body)
                except json.JSONDecodeError as e:
                    # Отправляем в Dead Letter Queue
                    error_message = f"Invalid JSON format: {str(e)}"
                    logging.error(error_message)
                    await self.send_to_dlq(message, error_message)
                    return

                notification_id = data.get("notification_id")
                to_id = data.get("to_id")
                send_by = data.get("send_by")
                if not (notification_id and to_id and send_by):
                    error_message = f"Missing required fields: {body}"
                    logging.error(error_message)
                    await self.send_to_dlq(message, error_message)
                    return

                # Читаем, заполняем и сохраняем шаблон
                template, contents = await self.db_engine.get_data_from_db(
                    notification_id
                )
                filled_template = await self.db_engine.fill_template(
                    template, contents
                )
                if filled_template:
                    await self.db_engine.save_filled_template_to_db(
                        filled_template, notification_id
                    )
                if contents:
                    await self.db_engine.delete_contents_from_db(contents)

                if not filled_template:
                    error_message = "Empty template"
                    logging.error(error_message)
                    await self.send_to_dlq(message, error_message)
                    return

                # Определяем очередь для отправки и отправляем сообщение
                queue_name = (
                    settings.queue_for_smtp
                    if send_by == "email"
                    else settings.queue_for_websocket
                )
                await self.send_notification(
                    queue_name,
                    {
                        "notification_id": notification_id,
                        "to_id": to_id,
                    },
                )
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            logging.error(error_message)
            await self.send_to_dlq(message, error_message)

    @backoff.on_exception(
        backoff.expo,
        exception=(
            ConnectionError,
            ConnectionRefusedError,
            ConnectionResetError,
            TimeoutError,
            AMQPConnectionError,
            AMQPChannelError,
            AMQPException,
            QueueEmpty,
            ChannelInvalidStateError,
        ),
        max_time=60,
    )
    async def send_notification(
        self, queue_name: str, message_data: Dict[str, Any]
    ) -> None:
        """Отправка уведомления в указанную очередь"""
        async with self.connection_pool.get_connection() as connection:
            async with connection.channel() as channel:
                await channel.declare_queue(
                    queue_name,
                    durable=True,
                    arguments={
                        "x-dead-letter-exchange": "",
                        "x-dead-letter-routing-key": f"{queue_name}{settings.dlq_ending}",
                    },
                )

                message = Message(
                    body=json.dumps(message_data).encode(),
                    delivery_mode=DeliveryMode.PERSISTENT,
                )

                await channel.default_exchange.publish(
                    message, routing_key=queue_name
                )
                logging.info(f"Сообщение отправлено в очередь {queue_name}")

    @backoff.on_exception(
        backoff.expo,
        exception=(
            ConnectionError,
            ConnectionRefusedError,
            ConnectionResetError,
            TimeoutError,
            AMQPConnectionError,
            AMQPChannelError,
            AMQPException,
            QueueEmpty,
            ChannelInvalidStateError,
        ),
        max_time=60,
    )
    async def setup_queues(
        self, channel: AbstractChannel
    ) -> Dict[str, AbstractQueue]:
        """Настройка очередей"""
        queues = {}

        # Создаем очереди
        for queue_name in [
            settings.queue_for_worker,
            settings.queue_for_smtp,
            settings.queue_for_websocket,
        ]:
            # Создаем DLQ
            dlq_name = f"{queue_name}{settings.dlq_ending}"
            dlq = await channel.declare_queue(dlq_name, durable=True)
            queues[dlq_name] = dlq
            # Создаем основную очередь с привязкой к DLQ
            queue = await channel.declare_queue(
                queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "",
                    "x-dead-letter-routing-key": dlq_name,
                },
            )
            queues[queue_name] = queue

        return queues

    async def send_to_dlq(
        self, original_message: IncomingMessage, error_message: str
    ) -> None:
        """Отправка сообщения в Dead Letter Queue"""
        async with self.connection_pool.get_connection() as connection:
            async with connection.channel() as channel:
                dlq_name = f"{settings.queue_for_worker}{settings.dlq_ending}"
                await channel.declare_queue(dlq_name, durable=True)

                dlq_message = {
                    "original_message": original_message.body.decode(),
                    "error_message": error_message,
                    "timestamp": str(datetime.datetime.now()),
                }

                message = Message(
                    body=json.dumps(dlq_message).encode(),
                    delivery_mode=DeliveryMode.PERSISTENT,
                )

                await channel.default_exchange.publish(
                    message, routing_key=dlq_name
                )
                logging.info(f"Сообщение отправлено в DLQ: {dlq_name}")

    async def main(self) -> None:
        """Основная функция"""
        try:
            async with self.connection:
                channel = await self.connection.channel()
                queues = await self.setup_queues(channel)

                # Начинаем слушать очередь worker
                await queues[settings.queue_for_worker].consume(
                    self.process_message
                )

                logging.info("Worker started")
                try:
                    # Держим соединение активным
                    await asyncio.Future()
                except asyncio.CancelledError:
                    logging.info("Worker stopped")
        finally:
            # Возвращаем соединение в пул
            await self.connection_pool.release_connection(self.connection)
            # Закрываем пул соединений при завершении работы
            await self.connection_pool.close()


async def run_worker():
    worker = await NotificationWorker.create()
    await worker.main()


if __name__ == "__main__":
    asyncio.run(run_worker())
