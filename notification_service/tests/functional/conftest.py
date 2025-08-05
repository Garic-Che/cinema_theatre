from typing import Any
import aiohttp
import asyncio
import pytest
import pytest_asyncio
from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from tests.functional.settings import (
    TestSettings,
    rabbitmq_settings,
    db_settings,
    service_settings,
)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(name="rabbit_client", scope="session")
def rabbit_client():
    connection_params = ConnectionParameters(
        host=rabbitmq_settings.host,
        port=rabbitmq_settings.port,
        credentials=PlainCredentials(
            username=rabbitmq_settings.username,
            password=rabbitmq_settings.password,
        ),
    )
    connection = BlockingConnection(connection_params)
    yield connection
    try:
        connection.close()
    except RuntimeError:
        pass


@pytest.fixture(name="db_client", scope="session")
def db_client():
    engine = create_engine(db_settings.get_connection_url())
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    try:
        session.close()
    except RuntimeError:
        pass


@pytest.fixture(name="clear_db_content", autouse=True)
def clear_db_content(db_client):
    schema = "content"
    tables = [
        "content",
        "notification",
        "schedule_notification",
    ]
    for table in tables:
        db_client.execute(text(f"TRUNCATE TABLE {schema}.{table} CASCADE"))
    db_client.commit()
    yield


@pytest.fixture(name="rabbit_delete_data", autouse=True)
def rabbit_delete_data(rabbit_client):
    def inner(test_settings: TestSettings):
        channel = rabbit_client.channel()

        if channel.queue_declare(
            queue=test_settings.rabbit_queue, durable=True, auto_delete=False
        ):
            channel.queue_delete(queue=test_settings.rabbit_queue)

        channel.close()

    return inner


@pytest.fixture(name="rabbit_get_data")
def rabbit_get_data(rabbit_client):
    def inner(test_settings: TestSettings):
        channel = rabbit_client.channel()

        if channel.queue_declare(
            queue=test_settings.rabbit_queue, durable=True, auto_delete=False
        ):
            method_frame, header_frame, body = channel.basic_get(
                queue=test_settings.rabbit_queue
            )
            print(f"method_frame: {method_frame}")
            print(f"header_frame: {header_frame}")
            print(f"body: {body}")
            if method_frame:
                # Подтверждаем получение сообщения
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                # Декодируем тело сообщения из bytes в строку
                if body:
                    return body.decode("utf-8")

        channel.close()

    return inner


@pytest_asyncio.fixture(name="make_post_request")
def make_post_request():
    async def inner(
        path: str,
        body: dict[str, Any] = {},
    ):
        session = aiohttp.ClientSession()
        url = service_settings.get_host() + path

        # Подготовка параметров запроса
        request_params = {
            "json": body,
            "headers": {
                "X-Internal-Auth": service_settings.notification_api_secret_key
            },
        }

        print(f"Making POST request to {url} with params: {request_params}")

        async with session.post(url, **request_params) as response:
            try:
                response_body = await response.json()
            except:
                response_body = await response.text()

            status = response.status

            print(f"Response: status={status}, body={response_body}")

        await session.close()
        return {
            "body": response_body,
            "status": status,
        }

    return inner
