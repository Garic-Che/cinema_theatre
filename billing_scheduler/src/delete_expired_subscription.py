import logging

from db.postgres import get_db
from db.db_engine import DBEngine
from db.auth_service_engine import auth_service_engine
from db.redis_engine import redis_engine


async def delete_expired_subscription():
    """Удаление просроченных подписок
    и соответствующих им ролей пользователей"""
    logging.debug("Удаление просроченных подписок")
    async with get_db() as session:
        db_engine = DBEngine(session)
        user_subscriptions = await db_engine.get_expired_subscriptions()
        logging.debug(
            "Найдено %d просроченных подписок", len(user_subscriptions)
        )
        for user_subscription in user_subscriptions:
            if not redis_engine.get(
                f"subscription_expired_{user_subscription.id}_{user_subscription.expires.timestamp()}"
            ):
                logging.debug("Просроченная подписка %s", user_subscription.id)
                role_id = await db_engine.get_role_id_by_subscription_id(
                    user_subscription.subscription_id
                )
                if not role_id:
                    logging.debug(
                        "Роль для подписки %s не найдена", user_subscription.id
                    )
                    continue
                await auth_service_engine.revoke_role(
                    user_subscription.user_id, role_id
                )
                redis_engine.set(
                    f"subscription_expired_{user_subscription.id}_{user_subscription.expires.timestamp()}",
                    "1",
                )
