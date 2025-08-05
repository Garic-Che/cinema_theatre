import asyncio
from typing import List
from contextlib import asynccontextmanager

from aio_pika import connect_robust
from aio_pika.abc import AbstractConnection

from core.config import settings


class RabbitMQConnectionPool:
    def __init__(self, pool_size: int = 10):
        self.pool_size = pool_size
        self.connection_pool: List[AbstractConnection] = []
        self.pool_lock = asyncio.Lock()
        self.broker_url = settings.notification_broker_url
        self.active_connections = 0
        self.connection_available = asyncio.Event()
        self.connection_available.set()

    async def initialize(self) -> None:
        """Инициализация пула соединений"""
        for _ in range(self.pool_size):
            await self.new_connection_to_pull()

    async def new_connection_to_pull(self) -> None:
        """Создание нового соединения"""
        if self.active_connections >= self.pool_size:
            raise RuntimeError(
                "Достигнут лимит максимального количества соединений"
            )

        connection = await connect_robust(self.broker_url)
        self.connection_pool.append(connection)
        self.active_connections += 1

    async def acquire_connection(self) -> AbstractConnection:
        """Получение соединения из пула без контекстного менеджера"""
        while True:
            async with self.pool_lock:
                if self.connection_pool:
                    connection = self.connection_pool.pop()
                    if not self.connection_pool:
                        self.connection_available.clear()
                    return connection

                if self.active_connections >= self.pool_size:
                    # Если достигнут лимит соединений, ждем освобождения
                    self.connection_available.clear()

            # Ждем, пока не появится свободное соединение
            await self.connection_available.wait()

            # Пробуем создать новое соединение, если не достигнут лимит
            async with self.pool_lock:
                if self.active_connections < self.pool_size:
                    await self.new_connection_to_pull()
                    connection = self.connection_pool.pop()
                    if not self.connection_pool:
                        self.connection_available.clear()
                    return connection

    async def release_connection(self, connection: AbstractConnection) -> None:
        """Возврат соединения в пул"""
        async with self.pool_lock:
            self.connection_pool.append(connection)
            self.connection_available.set()

    @asynccontextmanager
    async def get_connection(self):
        """Получение соединения из пула с контекстным менеджером"""
        connection = await self.acquire_connection()
        try:
            yield connection
        finally:
            await self.release_connection(connection)

    async def close(self) -> None:
        """Закрытие всех соединений в пуле"""
        async with self.pool_lock:
            for connection in self.connection_pool:
                await connection.close()
            self.connection_pool.clear()
            self.active_connections = 0
            self.connection_available.set()
