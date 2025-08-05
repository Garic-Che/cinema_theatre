from functools import wraps
import logging
import datetime
from http import HTTPStatus
from fastapi import HTTPException, Request, Response

from core.config import settings


def check_privilege(privilege: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            service = kwargs.get("service")
            if not await service.auth_engine.have_privilege(
                request.cookies.get("access_token"), privilege
            ):
                raise HTTPException(
                    status_code=HTTPStatus.UNAUTHORIZED,
                    detail="User unauthorized",
                )
            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def check_access_token(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        service = kwargs.get("service")
        # Проверяем наличие access_token
        access_token = request.cookies.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Access token is missing",
            )

        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Refresh token is missing",
            )

        # Логика обновления токена, если access_token истек

        # Если токен истек, обновляем его
        if service.auth_engine.decode_access_token_into_exp(
            access_token
        ) < int(datetime.datetime.utcnow().timestamp()):
            response = Response()
            await service.user_update_access(request, response)

            logging.info(
                "User updated access token\nNew access token: %s",
                request.cookies.get("access_token"),
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=HTTPStatus.UNAUTHORIZED,
                    detail="Failed to refresh access token",
                )
        else:
            logging.info("Users access token is not expired")
        # Вызываем оригинальный метод после проверки и обновления токена
        return await func(request, *args, **kwargs)

    return wrapper


def validate_user(login: str):
    # Валидация нового логина
    if not login.strip():
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="New login cannot be empty",
        )

    # Проверка минимальной длины логина
    if len(login) < 4:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Login must be at least 4 characters",
        )


def validate_password(password: str):
    # Проверка минимальной длины пароля
    if not password.strip():
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="New password cannot be empty",
        )

    # Проверка минимальной длины пароля
    if len(password) < 8:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Password must be at least 4 characters",
        )


def internal_auth_required(func):
    @wraps(func)
    async def decorated_function(*args, **kwargs):
        if "request" in kwargs:
            request = kwargs["request"]
        else:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Request is not provided",
            )

        # Проверка заголовка авторизации
        auth_header = request.headers.get("X-Internal-Auth")

        if not auth_header:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Authentication required",
            )

        if not auth_header == settings.internal_auth_secret_key:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail="Invalid authentication",
            )

        return await func(*args, **kwargs)

    return decorated_function


def check_privilege_or_internal_auth(privilege: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            service = kwargs.get("service")
            if (
                request.headers.get("X-Internal-Auth")
                == settings.internal_auth_secret_key
                or await service.auth_engine.have_privilege(
                    request.cookies.get("access_token"), privilege
                )
            ):
                return await func(request, *args, **kwargs)
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="User unauthorized",
            )

        return wrapper

    return decorator
