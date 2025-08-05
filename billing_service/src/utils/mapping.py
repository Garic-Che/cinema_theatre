from typing import Any

from yookassa.payment import PaymentResponse
from yookassa.refund import RefundResponse
from pydash import get

from schemas.service import OperationStatus, PaymentData, RefundData, ServicePaymentResponse, ServiceRefundResponse, AutopaymentData, ServicePaymentMethodResponse
from exceptions.billing import AppException
from utils.yookassa import QueryBuilder
from core.config import settings


class YooKassaStatusMapper:
    def map_status(self, payment: PaymentResponse) -> OperationStatus:
        status = payment.status
        if status == "pending":
            return OperationStatus.PROCESSING
        elif status == "succeeded":
            return OperationStatus.COMPLETED
        elif status == "canceled":
            return OperationStatus.FAILED
        else:
            raise AppException("Unprocessable status")

  
class YooKassaPaymentMethodStatusMapper:
    def map_status(self, payment_method: dict[str, Any]) -> OperationStatus:
        status = payment_method.get("status")
        if status == "pending":
            return OperationStatus.PROCESSING
        elif status == "active":
            return OperationStatus.COMPLETED
        elif status == "inactive":
            return OperationStatus.FAILED
        else:
            raise AppException("Unprocessable status")


class YooKassaPaymentMapper:
    def __init__(self, status_mapper: YooKassaStatusMapper):
        self.status_mapper = status_mapper
    
    def map_payment(self, payment: PaymentData) -> dict[str, Any]:
        redirect_url = f"{settings.billing_url_base}/api/v1/state/payment/{payment.idempotency_key}"

        query_builder = QueryBuilder()
        query_builder.add_payment_defaults()
        query_builder.add_amount(payment.amount, payment.currency)
        query_builder.add_redirect_confirmation(redirect_url)
        
        return query_builder.build()

    def map_payment_response(self, response: PaymentResponse) -> ServicePaymentResponse:
        return ServicePaymentResponse(
            payment_id=response.id,
            status=self.status_mapper.map_status(response),
            confirmation_url=get(response, "confirmation.confirmation_url"),
            payment_method_id=get(response, "payment_method.id"),
        )
    
    def map_autopayment(self, autopayment: AutopaymentData) -> dict[str, Any]:
        query_builder = QueryBuilder()
        query_builder.add_amount(autopayment.amount, autopayment.currency)
        query_builder.add_capture(True)
        query_builder.add_payment_method(autopayment.payment_method_id)

        return query_builder.build()


class YooKassaRefundMapper:
    def __init__(self, status_mapper: YooKassaStatusMapper):
        self.status_mapper = status_mapper

    def map_refund(self, refund: RefundData) -> dict[str, Any]:
        query_builder = QueryBuilder()
        query_builder.add_amount(refund.amount, refund.currency)
        query_builder.add_payment_id(refund.payment_id)

        return query_builder.build()

    def map_refund_response(self, response: RefundResponse) -> ServiceRefundResponse:
        return ServiceRefundResponse(
            status=self.status_mapper.map_status(response),
            payment_id=response.payment_id,
            refund_id=response.id,
            amount=get(response, "amount.value"),
            currency=get(response, "amount.currency"),
        )
    

class YooKassaPaymentMethodMapper:
    def __init__(self, status_mapper: YooKassaPaymentMethodStatusMapper):
        self.status_mapper = status_mapper

    def map_payment_method_response(self, response: dict[str, Any]) -> ServicePaymentMethodResponse:
        return ServicePaymentMethodResponse(
            payment_method_id=response.get("id"),
            status=self.status_mapper.map_status(response),
            confirmation_url=get(response, "confirmation.confirmation_url"),
        )
        

def get_payment_mapper() -> YooKassaPaymentMapper:
    return YooKassaPaymentMapper(YooKassaStatusMapper())


def get_refund_mapper() -> YooKassaRefundMapper:
    return YooKassaRefundMapper(YooKassaStatusMapper())


def get_payment_method_mapper() -> YooKassaPaymentMethodMapper:
    return YooKassaPaymentMethodMapper(YooKassaPaymentMethodStatusMapper())
