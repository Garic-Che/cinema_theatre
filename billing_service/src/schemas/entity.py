from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, UUID4, Field


class Message(BaseModel):
    detail: str = ""


class PaymentRequest(BaseModel):
    user_id: UUID4
    subscription_id: UUID4


class AutopaymentRequest(BaseModel):
    user_subscription_id: UUID4


class PaymentMethodRequest(BaseModel):
    user_subscription_id: UUID4


class RefundRequest(BaseModel):
    user_id: UUID4
    transaction_id: UUID4
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str


# Модель для подписки
class SubscriptionOut(BaseModel):
    id: UUID4
    role_id: UUID4
    name: str
    description: str | None = None
    amount: float
    currency: str
    period: int
    actual: bool
    created: datetime
    modified: datetime

    class Config:
        from_attributes = True

# Модель для пагинированного ответа
class PaginatedSubscriptions(BaseModel):
    total: int
    page: int
    size: int
    items: list[SubscriptionOut]


class UserSubscriptionOut(BaseModel):
    id: UUID4
    created: datetime
    modified: datetime
    user_id: UUID4
    auto_pay_id: str | None
    subscription_id: UUID4
    expires: datetime
    subscription: 'SubscriptionOut'

    class Config:
        from_attributes = True

class TransactionOut(BaseModel):
    id: UUID4
    payment_id: str
    amount: float
    currency: str
    status_code: int
    transaction_type: int
    created: datetime
    starts: datetime | None
    ends: datetime | None

    class Config:
        from_attributes = True

class PaginatedUserSubscriptions(BaseModel):
    total: int
    page: int
    size: int
    items: list[UserSubscriptionOut]

class TransactionsList(BaseModel):
    items: list[TransactionOut]