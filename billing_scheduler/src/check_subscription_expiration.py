import logging

from db.postgres import get_db
from core.config import settings
from schemas.model import Notification
from db.notification_service_engine import notification_service_engine
from db.billing_service_engine import billing_service_engine
from db.db_engine import DBEngine
from db.redis_engine import redis_engine, ExpirationNotification


async def check_subscription_expiration():
    """Проверка срока действия подписки
    и отправка уведомления о его истечении
    или совершение автоматической оплаты"""
    logging.debug("Проверка срока действия подписки")
    async with get_db() as session:
        db_engine = DBEngine(session)
        # Получаем подписки, срок действия которых истекает в ближайшие days дней
        user_subscriptions = await db_engine.user_subscription_soon_expiration(
            days=settings.subscription_soon_expiration_days
        )
        logging.debug("Найдено %d подписок", len(user_subscriptions))
    for user_subscription in user_subscriptions:
        if user_subscription.auto_pay_id:
            # Если у пользователя выбран автоплатеж,
            # то совершаем автоматическую оплату
            if not redis_engine.get(
                f"subscription_auto_pay_{user_subscription.id}_{user_subscription.expires.timestamp()}"
            ):
                await billing_service_engine.make_payment(user_subscription.id)
                redis_engine.set(
                    f"subscription_auto_pay_{user_subscription.id}_{user_subscription.expires.timestamp()}",
                    ExpirationNotification.SENT,
                    ex=settings.transaction_timeout_minutes * 60,
                )
        else:
            # Если у пользователя не выбран автоплатеж,
            # то отправляем уведомление о скором истечении подписки.
            # Если уведомление уже было отправлено, то пропускаем.
            if not redis_engine.get(
                f"subscription_expiration_{user_subscription.id}_{user_subscription.expires.timestamp()}"
            ):
                logging.debug(
                    "Отправка уведомления о скором истечении подписки для пользователя %s",
                    user_subscription.user_id,
                )
                await notification_service_engine.send_notification(
                    Notification(
                        to_id=str(user_subscription.user_id),
                        content_key="subscription_expiration",
                        content_data=user_subscription.expires.isoformat(),
                    )
                )
                redis_engine.set(
                    f"subscription_expiration_{user_subscription.id}_{user_subscription.expires.timestamp()}",
                    ExpirationNotification.SENT,
                )
