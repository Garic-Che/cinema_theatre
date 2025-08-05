import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
import sentry_sdk
from fastapi.openapi.utils import get_openapi
from fastapi.security import APIKeyHeader

from api.v1 import notifications
from core.config import settings
from db.broker import get_broker

sentry_sdk.init(dsn=settings.sentry_dsn_notification)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Код, выполняемый при запуске приложения
        broker_gen = get_broker()
        app.state.broker = await broker_gen.__anext__()
        # Создаем DLQ
        dlq_name = f"{settings.queue_for_worker}{settings.dlq_ending}"
        await app.state.broker.declare_queue(dlq_name)
        # Создаем основную очередь с привязкой к DLQ
        await app.state.broker.declare_queue(
            settings.queue_for_worker,
            arguments={
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": dlq_name,
            },
        )
        yield
    except Exception as e:
        logging.error(f"Lifespan error: {e}")
        raise
    finally:
        # Код, выполняемый при завершении работы приложения
        await app.state.broker.close()


app = FastAPI(
    title=settings.notification_project_name,
    description=settings.notification_project_description,
    version=settings.notification_project_version,
    docs_url="/api/v1/notification/openapi",
    openapi_url="/api/v1/notification/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# Добавляем схему безопасности
api_key_header = APIKeyHeader(name="X-Internal-Auth", auto_error=False)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Добавляем схему безопасности
    openapi_schema["components"] = {
        "securitySchemes": {
            "InternalAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-Internal-Auth",
            }
        },
        "schemas": {
            "Notification": {
                "type": "object",
                "properties": {
                    "to_id": {
                        "type": "string",
                        "format": "uuid",
                        "example": "123e4567-e89b-12d3-a456-426614174000",
                        "description": "id пользователя, которому отправляется уведомление или имя рассылки ('all')",
                    },
                    "send_by": {
                        "type": "string",
                        "example": "email",
                        "description": "способ отправки уведомления ('email', 'websocket')",
                    },
                    "content_key": {
                        "type": "string",
                        "example": "test/123e4567-e89b-12d3-a456-426614174000",
                        "description": "ключ контента или тип шаблона",
                    },
                    "content_data": {
                        "type": "string",
                        "example": "123e4567-e89b-12d3-a456-426614174000",
                        "description": "данные контента",
                    },
                },
                "required": [
                    "to_id",
                    "send_by",
                    "content_key",
                    "content_data",
                ],
            },
            "NotificationId": {
                "type": "object",
                "properties": {
                    "notification_id": {
                        "type": "string",
                        "format": "uuid",
                        "example": "123e4567-e89b-12d3-a456-426614174000",
                    }
                },
                "required": ["notification_id"],
            },
            "Message": {
                "type": "object",
                "properties": {"detail": {"type": "string"}},
                "required": ["detail"],
            },
            "Template": {
                "type": "object",
                "properties": {"template": {"type": "string"}},
            },
            "HTTPValidationError": {
                "type": "object",
                "properties": {
                    "detail": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "loc": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "msg": {"type": "string"},
                                "type": {"type": "string"},
                            },
                            "required": ["loc", "msg", "type"],
                        },
                    }
                },
            },
        },
    }

    # Применяем схему безопасности глобально
    openapi_schema["security"] = [{"InternalAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

app.include_router(
    notifications.router, prefix="/api/v1/notification", tags=["notification"]
)
