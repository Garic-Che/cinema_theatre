from decimal import Decimal
from enum import IntEnum

from pydantic import BaseModel, UUID4


class BaseOperationModel(BaseModel):
    amount: Decimal
    currency: str | None = None
    idempotency_key: UUID4 | None = None
    user_id: UUID4 | None = None


class PaymentData(BaseOperationModel):
    pass


class RefundData(BaseOperationModel):
    payment_id: str


class AutopaymentData(BaseOperationModel):
    payment_method_id: str


class PaymentMethodData(BaseModel):
    idempotency_key: str | None = None
    payment_method_id: str | None = None


class OperationStatus(IntEnum):
    PROCESSING = 1
    COMPLETED = 2
    FAILED = 3


class TransactionType(IntEnum):
    PAYMENT = 0
    AUTOPAYMENT = 1
    REFUND = 2
    PAYMENT_METHOD_ADD = 3
    PAYMENT_METHOD_REMOVE = 4


class BaseResponseModel(BaseModel):
    status: OperationStatus
    payment_id: str


class ServicePaymentResponse(BaseResponseModel):
    confirmation_url: str | None = None
    payment_method_id: str | None = None


class ServiceRefundResponse(BaseResponseModel):
    refund_id: str
    amount: Decimal | None = None
    currency: str | None = None


class ServicePaymentMethodResponse(BaseModel):
    status: OperationStatus
    payment_method_id: str | None = None
    confirmation_url: str | None = None
    