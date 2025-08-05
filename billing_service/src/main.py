from http import HTTPStatus
from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import ORJSONResponse

from api.v1 import payments, information, state
from core.config import settings


app = FastAPI(
    title=settings.billing_project_name,
    description=settings.billing_project_description,
    version=settings.billing_project_version,
    docs_url="/api/v1/billing/openapi",
    openapi_url="/api/v1/billing/openapi.json",
    default_response_class=ORJSONResponse,
)

@app.get("/api/v1/billing/health", response_model=dict)
async def health_check():
    return {"status": "OK"}

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    return ORJSONResponse(
        status_code=HTTPStatus.BAD_REQUEST,
        content={"message": str(exc)},
    )

app.include_router(state.router, prefix="/api/v1/state", tags=["state"])
app.include_router(payments.router, prefix="/api/v1/billing", tags=["billing"])
app.include_router(information.router, prefix="/api/v1/subs_information", tags=["subs_information"])


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Your API",
        version="1.0.0",
        description="API description",
        routes=app.routes,
    )

    # Добавляем схемы безопасности
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token authorization"
        },
        "InternalAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-Internal-Auth",
            "description": "Internal service authentication"
        }
    }

    # Применяем security только к нужным путям
    secured_paths = [
        "/api/v1/subs_information/subscriptions/user/{user_id}",
        "/api/v1/subs_information/transactions/{user_subscription_id}"
    ]

    for path, item in openapi_schema["paths"].items():
        if path in secured_paths:
            for method in item.values():
                method["security"] = [{"Bearer": []}, {"InternalAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi