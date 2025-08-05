from uuid import uuid4, UUID
from typing import Annotated
from abc import ABC, abstractmethod

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_db
from models.entity import Transaction, UserSubscription
from services.payment import PaymentServiceABC, get_payment_service
from services.refund import RefundServiceABC, get_refund_service
from services.subscription import SubscriptionServiceABC, get_subscription_service
from services.transaction import TransactionServiceABC, get_transaction_service
from exceptions.billing import AppException
from schemas.entity import PaymentRequest, RefundRequest, PaymentMethodRequest, AutopaymentRequest
from schemas.service import TransactionType, RefundData, PaymentData, OperationStatus, AutopaymentData, PaymentMethodData
from services.payment_method import PaymentMethodServiceABC, get_payment_method_service


class BillingServiceABC(ABC):
    @abstractmethod
    async def pay_for_subscription(self, payment: PaymentRequest) -> str:
        pass

    @abstractmethod
    async def refund_payment(self, refund: RefundRequest) -> None:
        pass

    @abstractmethod
    async def make_autopayment(self, autopayment: AutopaymentRequest) -> UUID:
        pass

    @abstractmethod
    async def create_payment_method(self, payment_method: PaymentMethodRequest) -> str:
        pass

    @abstractmethod
    async def remove_payment_method(self, payment_method: PaymentMethodRequest) -> None:
        pass


class BillingService(BillingServiceABC):
    def __init__(
        self,
        session: AsyncSession,
        payment_service: PaymentServiceABC,
        refund_service: RefundServiceABC,
        subs_service: SubscriptionServiceABC,
        tsn_service: TransactionServiceABC,
        payment_method_service: PaymentMethodServiceABC,
    ):
        self.session = session
        self.payment_service = payment_service
        self.subs_service = subs_service
        self.refund_service = refund_service
        self.tsn_service = tsn_service
        self.payment_method_service = payment_method_service

    async def pay_for_subscription(self, subs_request: PaymentRequest) -> str:
        subs = await self.subs_service.get_subs_by_id(subs_request.subscription_id)
        transaction_id = uuid4()
        payment = self.payment_service.create_payment(PaymentData(
            **subs.__dict__, idempotency_key=transaction_id,
        ))
        user_subs = await self.subs_service.get_or_create_subs_for_user(
            subs_request.user_id, subs_request.subscription_id,
        )
        await self.payment_service.commit_subs_payment(
            transaction_id, TransactionType.PAYMENT, user_subs, payment
        )
        return payment.confirmation_url

    async def refund_payment(self, refund: RefundRequest) -> None:
        transaction_to_refund = await self.tsn_service.get_transaction(refund.transaction_id)
        self._validate_cancelling_transaction(refund, transaction_to_refund)
        transaction_id = uuid4()
        refund_response= self.refund_service.create_refund(RefundData(
            amount=refund.amount,
            currency=refund.currency,
            idempotency_key=transaction_id,
            payment_id=transaction_to_refund.payment_id,
            user_id=refund.user_id,
        ))
        await self.refund_service.commit_refund(transaction_id, transaction_to_refund, refund_response)

    def _validate_cancelling_transaction(
            self, 
            refund: RefundRequest, 
            transaction_to_refund: Transaction
    ) -> None:
        if transaction_to_refund.status_code != OperationStatus.COMPLETED:
            raise AppException("Only completed transactions can be refunded")
        
        if transaction_to_refund.transaction_type == TransactionType.REFUND:
            raise AppException("Only payment transactions can be refunded")
        
        if transaction_to_refund.currency != refund.currency:
            raise AppException("Source and target currencies do not match")
        
    async def make_autopayment(self, autopayment: AutopaymentRequest) -> str:
        user_subs = await self.subs_service.get_user_subs_by_id(autopayment.user_subscription_id)
        self._validate_autopayment_user_subs(user_subs)
        transaction_id = uuid4()
        response = self.payment_service.create_autopayment(AutopaymentData(
            amount=user_subs.subscription.amount,
            currency=user_subs.subscription.currency,
            user_id=user_subs.user_id,
            payment_method_id=user_subs.auto_pay_id,
            idempotency_key=transaction_id,
        ))
        await self.payment_service.commit_subs_payment(
            transaction_id, TransactionType.AUTOPAYMENT, user_subs, response
        )
        return str(transaction_id)
    
    def _validate_autopayment_user_subs(self, user_subs: UserSubscription) -> None:
        if not user_subs.auto_pay_id:
            raise AppException("User subscription passed does not have payment method set")

    async def create_payment_method(self, payment_method: PaymentMethodRequest) -> str:
        user_subs = await self.subs_service.get_user_subs_by_id(payment_method.user_subscription_id)
        transaction_id = uuid4()
        response = await self.payment_method_service.create_payment_method(PaymentMethodData(
            idempotency_key=str(transaction_id),
        ))
        await self.payment_method_service.commit_payment_method(
            transaction_id, TransactionType.PAYMENT_METHOD_ADD, user_subs, response.payment_method_id
        )
        return response.confirmation_url

    async def remove_payment_method(self, payment_method: PaymentMethodRequest) -> None:
        user_subs = await self.subs_service.get_user_subs_by_id(payment_method.user_subscription_id)
        if not user_subs.auto_pay_id:
            raise AppException("User subscription provided does not have payment id")
        transaction_id = uuid4()
        await self.payment_method_service.commit_payment_method(
            transaction_id, TransactionType.PAYMENT_METHOD_REMOVE, user_subs, user_subs.auto_pay_id
        )

def get_billing_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    payment_service: Annotated[PaymentServiceABC, Depends(get_payment_service)],
    refund_service: Annotated[RefundServiceABC, Depends(get_refund_service)],
    subs_service: Annotated[SubscriptionServiceABC, Depends(get_subscription_service)],
    transaction_service: Annotated[TransactionServiceABC, Depends(get_transaction_service)],
    payment_method_service: Annotated[PaymentMethodServiceABC, Depends(get_payment_method_service)],
) -> BillingServiceABC:
    return BillingService(
        session,
        payment_service,
        refund_service,
        subs_service,
        transaction_service,
        payment_method_service,
    )
