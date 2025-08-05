from functools import wraps
from http import HTTPStatus
from fastapi import HTTPException, Request

from core.config import settings


def check_auth_header(request: Request) -> bool:
    """Проверка заголовка авторизации"""
    auth_header = request.headers.get("X-Internal-Auth")

    if not auth_header:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Authentication required",
        )

    if auth_header != settings.internal_billing_secret_key:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Invalid authentication",
        )
    return True


def internal_auth_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get("request")
        if not request:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Request is not provided",
            )

        check_auth_header(request)

        return await func(*args, **kwargs)

    return wrapper


def jwt_or_internal_auth_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get("request")
        if not request:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Request is not provided",
            )

        # Проверяем внутреннюю аутентификацию
        try:
            check_auth_header(request)
            return await func(*args, **kwargs)
        except HTTPException as internal_auth_error:
            # Если внутренняя аутентификация не прошла, проверяем JWT
            if not kwargs.get("user"):  # Предполагается, что JWT проверяется где-то ещё
                raise HTTPException(
                    status_code=HTTPStatus.UNAUTHORIZED,
                    detail="Unauthorized: neither internal auth nor JWT provided",
                )
            return await func(*args, **kwargs)

    return wrapper
