import logging
import httpx

from subscribes.schemas import PaymentRequestForm,RefundRequestForm


class BillingServiceEngine:
    def __init__(self, settings):
        self.settings = settings

    async def make_payment(self, user_id: str, subscription_id: str) -> dict | None:
        logging.debug(f"Запрос на оплату подписки {subscription_id} для пользователя {user_id}")
        url = f"{self.settings.BILLING_SERVICE_URL}/api/v1/billing/payment"

        form = PaymentRequestForm({
            'user_id': user_id,
            'subscription_id': subscription_id
        })

        if not form.is_valid():
            logging.error(f"Ошибка валидации: {form.errors}")
            return None

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    url,
                    json=form.cleaned_data,
                    headers={"X-Internal-Auth": self.settings.INTERNAL_BILLING_SECRET_KEY},
                )
                response.raise_for_status()
                return response.json()
        except httpx.ConnectTimeout:
            logging.error(f"[TIMEOUT] Не удалось подключиться к {url}")
        except httpx.HTTPStatusError as e:
            logging.error(f"[HTTP ERROR] {e.response.status_code} — {e.response.text}")
        except httpx.RequestError as e:
            logging.error(f"[REQUEST ERROR] {e}")
        except Exception as e:
            logging.error(f"[UNEXPECTED ERROR] {e}")
        return None

    async def refund_transaction(
            self, user_id: str, payment_id: str, amount: float, currency: str = "RUB"
    ) -> dict | None:
        logging.debug(f"Запрос на возврат по транзакции {payment_id}")
        url = f"{self.settings.BILLING_SERVICE_URL}/api/v1/billing/refund"

        form = RefundRequestForm({
            'user_id': user_id,
            'transaction_id': payment_id,
            'amount': amount,
            'currency': currency
        })

        if not form.is_valid():
            logging.error(f"Ошибка валидации: {form.errors}")
            return None

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                logging.debug(
                    f"""Запрос на возврат по транзакции {payment_id}, 
                    json={form.cleaned_data}, 
                    headers={{"X-Internal-Auth": {self.settings.INTERNAL_BILLING_SECRET_KEY}}}"""
                )
                response = await client.post(
                    url,
                    json=form.cleaned_data,
                    headers={"X-Internal-Auth": self.settings.INTERNAL_BILLING_SECRET_KEY},
                )
                try:
                    return response.json()
                except Exception as e:
                    logging.error(f"Ошибка: {e}")
                    return None
        except httpx.ConnectTimeout:
            logging.error(f"[TIMEOUT] Не удалось подключиться к {url}")
        except httpx.HTTPStatusError as e:
            logging.error(f"[HTTP ERROR] {e.response.status_code} — {e.response.text}")
        except httpx.RequestError as e:
            logging.error(f"[REQUEST ERROR] {e}")
        except Exception as e:
            logging.error(f"[UNEXPECTED ERROR] {e}")
        return None