from datetime import timedelta, datetime
import logging

from db.postgres import get_db
from db.db_engine import DBEngine
from schemas.model import (
    StatusCode,
    Notification,
    TransactionType as TT,
)
from models.entity import Transaction
from db.billing_service_engine import billing_service_engine
from db.notification_service_engine import notification_service_engine
from db.auth_service_engine import auth_service_engine
from core.config import settings


def calculate_delta_expires(
    transaction_amount: float,
    subscription_amount: float,
    subscription_period: int,
) -> int:
    """Расчет дельты срока действия подписки"""
    return int(subscription_period * transaction_amount / subscription_amount)


async def check_transactions():
    """Проверка транзакций"""
    logging.debug("Проверка транзакций")
    async with get_db() as session:
        db_engine = DBEngine(session)
        # Получаем транзакции из БД со статусом PROCESSING
        transactions = await db_engine.get_transactions_with_status_code(
            status_code=StatusCode.PROCESSING
        )
        logging.debug("Найдено %d транзакций", len(transactions))
        for transaction in transactions:
            # Если транзакция является удалением метода оплаты,
            # обновляем статус транзакции в БД на COMPLETED
            # и удаляем метод оплаты из подписки
            if transaction.transaction_type == TT.PAYMENT_METHOD_REMOVE:
                await complete_payment_method_remove_transaction(
                    transaction, db_engine
                )
                continue
            # Проверяем изменился ли статус транзакции в BillingService
            get_status = {
                TT.REFUND: billing_service_engine.check_refund,
                TT.PAYMENT: billing_service_engine.check_payment,
                TT.AUTOPAYMENT: billing_service_engine.check_payment,
                TT.PAYMENT_METHOD_ADD: billing_service_engine.check_subscription_payment,
            }
            status = await get_status[transaction.transaction_type](
                transaction.id
            )

            if status is None:
                logging.warning(
                    "Не удалось получить статус транзакции типа %s: %s",
                    transaction.transaction_type,
                    transaction.id,
                )
                continue

            status_code = status.status

            logging.debug(
                "Статус транзакции %s: %s", transaction.id, status_code
            )
            if status_code == StatusCode.COMPLETED:
                # Обновляем статус транзакции в БД на COMPLETED
                logging.debug("Успешная транзакция %s", transaction.id)
                if transaction.transaction_type == TT.REFUND:
                    await complete_transaction(
                        transaction, db_engine, status.payment_id
                    )
                elif transaction.transaction_type == TT.PAYMENT_METHOD_ADD:
                    await complete_ap_subscription_transaction(
                        transaction, db_engine, status.auto_pay_id
                    )
                else:
                    await complete_transaction(transaction, db_engine)
            elif status_code == StatusCode.FAILED:
                # Обновляем статус транзакции в БД на FAILED
                # и отправляем уведомление о неуспешной транзакции
                logging.debug("Неуспешная транзакция %s", transaction.id)
                await fail_transaction(transaction, db_engine)
            elif (
                transaction.created
                + timedelta(minutes=settings.transaction_timeout_minutes)
                < datetime.now()
            ):
                # Если транзакция не обновилась в течение timeout_minutes,
                # обновляем статус транзакции в БД на FAILED
                logging.debug("Таймаут транзакции %s", transaction.id)
                await timeout_transaction(transaction, db_engine)
            else:
                logging.debug("Транзакция %s не обновлена", transaction.id)


async def complete_payment_method_remove_transaction(
    transaction: Transaction, db_engine: DBEngine
):
    """Завершение транзакции удаления метода оплаты"""
    logging.debug("Транзакция на удаление метода оплаты: %s", transaction.id)
    await db_engine.update_user_subscription(
        transaction.user_subscription_id, {"auto_pay_id": None}
    )
    logging.debug(
        "Обновляем статус транзакции %s на COMPLETED", transaction.id
    )
    await db_engine.update_transaction_status(
        transaction.id, StatusCode.COMPLETED
    )


async def complete_ap_subscription_transaction(
    transaction: Transaction, db_engine: DBEngine, auto_pay_id: str
):
    """Завершение транзакции подписки на автоплатеж"""
    await db_engine.update_user_subscription(
        transaction.user_subscription_id, {"auto_pay_id": auto_pay_id}
    )
    logging.debug(
        "Обновляем статус транзакции %s на COMPLETED", transaction.id
    )
    await db_engine.update_transaction_status(
        transaction.id, StatusCode.COMPLETED
    )


async def complete_transaction(
    transaction: Transaction, db_engine: DBEngine, payment_id: str = ""
):
    """Завершение транзакции"""
    logging.debug(
        "Получаем пользовательскую подписку %s",
        transaction.user_subscription_id,
    )
    user_subscription = await db_engine.get_user_subscription_by_id(
        transaction.user_subscription_id
    )
    if not user_subscription:
        logging.debug(
            "Пользовательская подписка %s не найдена",
            transaction.user_subscription_id,
        )
        return
    logging.debug("Получаем подписку %s", user_subscription.subscription_id)
    subscription = await db_engine.get_subscription_by_id(
        user_subscription.subscription_id
    )
    if not subscription:
        logging.debug(
            "Подписка %s не найдена", user_subscription.subscription_id
        )
        return

    # Рассчитываем новый срок действия подписки
    expires_from = (
        user_subscription.expires
        if user_subscription.expires > datetime.now()
        else datetime.now()
    )
    sign = -1 if transaction.transaction_type == TT.REFUND else 1
    delta_expires = calculate_delta_expires(
        transaction.amount,
        subscription.amount,
        subscription.period,
    )
    new_expires = expires_from + sign * timedelta(
        days=delta_expires,
    )

    logging.debug("Новый срок действия подписки: %s", new_expires)
    # Обновляем срок действия подписки в БД
    await db_engine.update_user_subscription(
        user_subscription, {"expires": new_expires}
    )

    # Назначаем или лишаем роли пользователя
    # в зависимости от нового срока действия подписки
    if new_expires >= datetime.now():
        await auth_service_engine.assign_role(
            transaction.user_id, subscription.role_id
        )
    else:
        await auth_service_engine.revoke_role(
            transaction.user_id, subscription.role_id
        )

    if transaction.transaction_type == TT.REFUND:
        # Если транзакция является возвратом,
        # обновляем статус платежной транзакции в БД,
        # сдвигаем во времени следующие платежные транзакции
        logging.debug("Сдвигаем во времени следующие платежные транзакции")
        payment_transaction = await db_engine.get_transaction_by_id(payment_id)
        if payment_transaction:
            new_ends = payment_transaction.ends - timedelta(days=delta_expires)
            # Если новый конец действия транзакции меньше текущей даты,
            # корректируем дельту
            if new_ends < datetime.now():
                delta_correction = (datetime.now() - new_ends).days
                delta_expires -= delta_correction
                new_ends = datetime.now()
            logging.debug(
                "Обновляем статус платежной транзакции %s на REFUNDED",
                payment_transaction.id,
            )
            await db_engine.update_transaction(
                payment_transaction.id,
                {
                    "status_code": StatusCode.REFUNDED,
                    "ends": new_ends,
                },
            )
            logging.debug("Сдвигаем во времени следующие платежные транзакции")
            await db_engine.shift_back_in_time_next_payment_transactions(
                new_ends, delta_expires
            )
    else:
        # Если транзакция является платежом,
        # обновляем дату начала и конца действия транзакции
        logging.debug(
            "Обновляем дату начала и конца действия транзакции %s",
            transaction.id,
        )
        await db_engine.update_transaction(
            transaction.id,
            {
                "starts": new_expires - timedelta(days=delta_expires),
                "ends": new_expires,
            },
        )
    # Обновляем статус транзакции в БД на COMPLETED
    logging.debug(
        "Обновляем статус транзакции %s на COMPLETED", transaction.id
    )
    await db_engine.update_transaction_status(
        transaction.id, StatusCode.COMPLETED
    )
    # Отправляем уведомление о завершении транзакции
    await notification_service_engine.send_notification(
        Notification(
            to_id=str(transaction.user_id),
            content_key="transaction_completed",
            content_data=str(transaction.id),
        )
    )


async def fail_transaction(transaction: Transaction, db_engine: DBEngine):
    """Неуспешная транзакция"""
    # Обновляем статус транзакции в БД на FAILED
    await db_engine.update_transaction_status(
        transaction.id, StatusCode.FAILED
    )
    # Отправляем уведомление о неуспешной транзакции
    await notification_service_engine.send_notification(
        Notification(
            to_id=str(transaction.user_id),
            content_key="transaction_failed",
            content_data=str(transaction.id),
        )
    )


async def timeout_transaction(transaction: Transaction, db_engine: DBEngine):
    """Таймаут транзакции"""
    if not transaction.transaction_type == TT.REFUND:
        # Если транзакция не является возвратом,
        # выполняем возврат денег
        await billing_service_engine.refund_transaction(
            transaction.user_id,
            transaction.payment_id,
            transaction.amount,
            transaction.currency,
        )
    # Обновляем статус транзакции в БД на FAILED
    await db_engine.update_transaction_status(
        transaction.id, StatusCode.FAILED
    )
    # Отправляем уведомление о таймауте транзакции
    await notification_service_engine.send_notification(
        Notification(
            to_id=str(transaction.user_id),
            content_key="transaction_timeout",
            content_data=str(transaction.id),
        )
    )
