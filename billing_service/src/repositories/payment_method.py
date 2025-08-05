import base64
from typing import Any
from abc import ABC, abstractmethod

import aiohttp

from core.config import settings
from utils.yookassa import QueryBuilder
from schemas.service import PaymentMethodData
from exceptions.billing import AppException


class PaymentMethodRepositoryABC(ABC):
    @abstractmethod
    async def create_payment_method(self, payment_method_data: PaymentMethodData) -> dict[str, Any]:
        pass

    @abstractmethod
    async def get_payment_method(self, payment_method_id: str) -> dict[str, Any]:
        pass


class YooKassaPaymentMethodRepository(PaymentMethodRepositoryABC):
    def __init__(self):
        self.auth = base64.b64encode(
            f"{settings.account_id}:{settings.secret_key}".encode()
        ).decode()
        self.base_url = f"{settings.yookassa_api_base}/v3/payment_methods"

    async def get_payment_method(self, payment_method_id: str) -> dict[str, Any]:
        headers = self._get_headers()
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/{payment_method_id}"
            async with session.get(url, headers=headers) as response:
                result = await response.json()
                self._handle_yookassa_errors(result)
                return result
                
    def _get_headers(self) -> dict[str, Any]:
        return {
            "Authorization": f"Basic {self.auth}",
            "Content-Type": "application/json",
        }

    def _handle_yookassa_errors(self, response: dict[str, Any]) -> None:
        response_type = response.get("type")
        if not response_type or response_type != "error":
            return
        error_code = response.get("code")
        if error_code == "not_found":
            raise AppException("Payment method was not found")
        else:
            raise AppException(f"Yookassa responded with {error_code}")

    async def create_payment_method(self, payment_method_data: PaymentMethodData) -> dict[str, Any]:
        headers = self._get_post_headers(payment_method_data)
        body = self._get_body(payment_method_data)
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, headers=headers, json=body) as response:
                result = await response.json()
                self._handle_yookassa_errors(result)
                return result
    
    def _get_post_headers(self, payment_method_data: PaymentMethodData) -> dict[str, Any]:
        default_headers = self._get_headers()
        default_headers["Idempotence-Key"] = payment_method_data.idempotency_key
        return default_headers
                
    def _get_body(self, payment_method_data: PaymentMethodData) -> dict[str, Any]:
        redirect_url = f"{settings.billing_url_base}/api/v1/state/payment/{payment_method_data.idempotency_key}"

        query_builder = QueryBuilder()
        query_builder.add_redirect_confirmation(redirect_url)
        query_builder.add_type("bank_card")
        return query_builder.build()


def get_payment_method_repository() -> PaymentMethodRepositoryABC:
    return YooKassaPaymentMethodRepository()
