import jwt
from core.config import settings


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token.replace("Bearer ", ""),
            settings.auth_secret_key,
            algorithms=[settings.algorithm],
        )
        return payload
    except Exception as err:
        return None
