from redis import Redis
from core.config import settings


class ExpirationNotification:
    SENT: str = "1"
    NOT_SENT: str = ""


class RedisEngine:
    def __init__(self, redis: Redis):
        self.redis = redis

    def get(self, key: str) -> str:
        return self.redis.get(key)

    def set(
        self,
        key: str,
        value: str,
        ex: int = settings.subscription_soon_expiration_days * 24 * 60 * 60,
    ) -> None:
        self.redis.set(key, value, ex=ex)


redis_engine = RedisEngine(
    Redis(
        host=settings.billing_notification_redis_host,
        port=settings.redis_port,
        db=settings.billing_notification_redis_db,
    )
)
