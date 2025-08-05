import httpx
import logging
import uuid

from core.config import settings, Settings
from schemas.model import (
    AutopaymentRequest,
    Refund,
    PaymentStatus,
    RefundStatus,
    SubscriptionPaymentStatus,
    StatusCode,
)


class BillingServiceEngine:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def make_payment(
        self, user_subscription_id: str | uuid.UUID
    ) -> dict | None:
        """Совершение автоматической оплаты"""
        url = (
            f"{self.settings.billing_service_url}/api/v1/payment/autopayment/"
        )
        logging.debug(
            "Запрос на автоматическую оплату подписки %s по адресу %s",
            user_subscription_id,
            url,
        )
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=AutopaymentRequest(
                    user_subscription_id=str(user_subscription_id),
                ).model_dump(),
                headers={
                    "X-Internal-Auth": self.settings.internal_billing_secret_key
                },
            )
            logging.debug("Данные от BillingService: %s", response)
            try:
                response_data = response.json()
                return response_data
            except Exception as e:
                logging.error(
                    "Ошибка при получении данных от BillingService: %s", e
                )
                return None

    async def refund_transaction(
        self,
        user_id: str | uuid.UUID,
        payment_id: str | uuid.UUID,
        amount: float,
        currency: str = "RUB",
    ) -> dict | None:
        """Возврат транзакции"""
        url = f"{self.settings.billing_service_url}/api/v1/refund/"
        logging.debug("Возврат транзакции %s по адресу %s", payment_id, url)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=Refund(
                    user_id=str(user_id),
                    payment_id=str(payment_id),
                    amount=amount,
                    currency=currency,
                ).model_dump(),
                headers={
                    "X-Internal-Auth": self.settings.internal_billing_secret_key
                },
            )
            logging.debug("Данные от BillingService: %s", response)
            try:
                response_data = response.json()
                return response_data
            except Exception as e:
                logging.error(
                    "Ошибка при получении данных от BillingService: %s", e
                )
                return None

    async def check_payment(
        self, transaction_id: str | uuid.UUID
    ) -> PaymentStatus | None:
        """Проверка статуса платежа"""
        transaction_id = str(transaction_id)
        url = f"{self.settings.billing_service_url}/api/v1/state/payment/{transaction_id}"
        logging.debug(
            "Проверка статуса платежа по транзакции %s по адресу %s",
            transaction_id,
            url,
        )
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    headers={
                        "X-Internal-Auth": self.settings.internal_billing_secret_key
                    },
                )
                response.raise_for_status()  # Вызовет исключение для 4xx/5xx статусов
                return PaymentStatus(**response.json())
            except httpx.HTTPStatusError as e:
                logging.error(
                    "HTTP ошибка при проверке платежа %s: %s - %s",
                    transaction_id,
                    e.response.status_code,
                    e.response.text,
                )
                return None
            except Exception as e:
                logging.error(
                    "Ошибка при проверке платежа %s: %s", transaction_id, e
                )
                return None

    async def check_refund(
        self, transaction_id: str | uuid.UUID
    ) -> RefundStatus | None:
        """Проверка статуса возврата"""
        transaction_id = str(transaction_id)
        url = f"{self.settings.billing_service_url}/api/v1/state/refund/{transaction_id}"
        logging.debug(
            "Проверка статуса возврата по транзакции %s по адресу %s",
            transaction_id,
            url,
        )
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    headers={
                        "X-Internal-Auth": self.settings.internal_billing_secret_key
                    },
                )
                response.raise_for_status()
                return RefundStatus(**response.json())
            except httpx.HTTPStatusError as e:
                logging.error(
                    "HTTP ошибка при проверке возврата %s: %s - %s",
                    transaction_id,
                    e.response.status_code,
                    e.response.text,
                )
                return None
            except Exception as e:
                logging.error(
                    "Ошибка при проверке возврата %s: %s", transaction_id, e
                )
                return None

    async def check_subscription_payment(
        self, transaction_id: str | uuid.UUID
    ) -> SubscriptionPaymentStatus | None:
        """Проверка статуса транзакции подписки на автоплатеж"""
        transaction_id = str(transaction_id)
        url = f"{self.settings.billing_service_url}/api/v1/state/payment-method/{transaction_id}"
        logging.debug(
            "Проверка статуса подписки на автоплатеж %s по адресу %s",
            transaction_id,
            url,
        )
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    headers={
                        "X-Internal-Auth": self.settings.internal_billing_secret_key
                    },
                )
                response.raise_for_status()
                response_data = response.json()
                status_to_code = {
                    "active": StatusCode.COMPLETED,
                    "inactive": StatusCode.FAILED,
                    "pending": StatusCode.PROCESSING,
                }
                status_code = (
                    StatusCode.PROCESSING
                    if not response_data["status"]
                    else status_to_code[response_data["status"]]
                )
                return SubscriptionPaymentStatus(
                    status=status_code,
                    auto_pay_id=response_data["id"],
                )
            except httpx.HTTPStatusError as e:
                logging.error(
                    "HTTP ошибка при проверке подписки на автоплатеж %s: %s - %s",
                    transaction_id,
                    e.response.status_code,
                    e.response.text,
                )
                return None
            except Exception as e:
                logging.error(
                    "Ошибка при проверке подписки на автоплатеж %s: %s",
                    transaction_id,
                    e,
                )
                return None


billing_service_engine = BillingServiceEngine(settings)
