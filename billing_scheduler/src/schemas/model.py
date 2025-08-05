from enum import IntEnum
from pydantic import BaseModel


class StatusCode(IntEnum):
    PROCESSING: int = 1
    COMPLETED: int = 2
    FAILED: int = 3
    REFUNDED: int = 4


class TransactionType(IntEnum):
    PAYMENT: int = 0
    AUTOPAYMENT: int = 1
    REFUND: int = 2
    PAYMENT_METHOD_ADD: int = 3
    PAYMENT_METHOD_REMOVE: int = 4


class CommonID(BaseModel):
    id: str = ""


class AutopaymentRequest(BaseModel):
    user_subscription_id: str


class Refund(BaseModel):
    user_id: str = ""
    payment_id: str = ""
    amount: float = 0.0
    currency: str = ""


class PaymentStatus(BaseModel):
    status: StatusCode
    payment_id: str
    confirmation_url: str | None = None
    payment_method_id: str | None = None


class RefundStatus(BaseModel):
    status: StatusCode
    payment_id: str
    refund_id: str
    amount: float | None = None
    currency: str | None = None


class SubscriptionPaymentStatus(BaseModel):
    status: StatusCode
    auto_pay_id: str | None = None


class RoleWithID(CommonID):
    name: str = ""
    privilege_ids: list[str]


class Notification(BaseModel):
    to_id: str = ""
    send_by: str = "email"
    content_key: str = ""
    content_data: str = ""
