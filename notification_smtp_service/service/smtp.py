import asyncio
import logging
from abc import ABC, abstractmethod
from email.message import EmailMessage
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any
from aiosmtplib.errors import SMTPConnectError

import aiosmtplib

from core.config import settings 
from exception.app import AppException


class EmailServiceABC(ABC):
    @abstractmethod
    async def connect(self):
        pass
    
    @abstractmethod
    async def send(self, email_message: EmailMessage) -> None:
        pass

    @abstractmethod
    def connected(self) -> bool:
        pass


class EmailService(EmailServiceABC):
    def __init__(self, host: str, port: int) -> None:
        self.smtp_host = host
        self.smtp_port = port
        self.default_sender: str = settings.smtp_default_sender

    async def connect(self):
        while True:
            try:
                server = aiosmtplib.SMTP(hostname=self.smtp_host, port=self.smtp_port)
                await server.connect()
                self.server = server
            except SMTPConnectError:
                logging.info('could not connect smtp server')
                await asyncio.sleep(settings.smtp_queue_reconnection_period)
            else:
                logging.info('connected smtp server successfully')
                break

    async def send(self, email_message: EmailMessage) -> None:
        if not self.connected():
            raise AppException('need to connect a server')
        await self.server.sendmail(email_message['From'], email_message['To'], email_message.as_string())

    async def close(self):
        if not self.connected():
            raise AppException('need to connect a server')
        self.server.close()

    def connected(self):
        return self.server.is_connected


@asynccontextmanager    
async def get_email_service() -> AsyncGenerator[EmailServiceABC, Any]:
    email_service = EmailService(
        settings.smtp_service_host,
        settings.smtp_service_port
    )
    await email_service.connect()
    try:
        yield email_service
    finally:
        await email_service.close()
