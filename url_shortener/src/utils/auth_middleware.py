from http import HTTPStatus
from functools import wraps

from fastapi import HTTPException

from core.config import settings


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

        if not auth_header == settings.URL_SHORTENER_API_SECRET_KEY:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail="Invalid authentication",
            )

        return await func(*args, **kwargs)

    return decorated_function
