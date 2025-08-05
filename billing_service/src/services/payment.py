from uuid import UUID
from typing import Annotated
from abc import ABC, abstractmethod

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from yookassa import Payment, Configuration
from yookassa.domain.exceptions import NotFoundError

from core.config import settings
from db.postgres import get_db
from utils.mapping import YooKassaPaymentMapper, get_payment_mapper
from schemas.service import PaymentData, ServicePaymentResponse, OperationStatus, TransactionType, AutopaymentData
from models.entity import UserSubscription, Transaction
from services.transaction import TransactionServiceABC, get_transaction_service


Configuration.configure(settings.account_id, settings.secret_key)


class PaymentServiceABC(ABC):
    @abstractmethod
    def create_payment(self, payment: PaymentData) -> ServicePaymentResponse:
        pass

    @abstractmethod
    async def get_payment(self, transaction_id: str) -> ServicePaymentResponse | None:
        pass

    @abstractmethod
    async def commit_subs_payment(self, tsn_id: UUID, tsn_type: TransactionType, user_subs: UserSubscription, payment: ServicePaymentResponse):
        pass

    @abstractmethod
    def create_autopayment(self, autopayment: AutopaymentData) -> ServicePaymentResponse:
        pass


class YooKassaPaymentService(PaymentServiceABC):
    def __init__(
        self, 
        session: AsyncSession,
        mapper: YooKassaPaymentMapper,
        transaction_service: TransactionServiceABC,
    ):
        self.session = session
        self.mapper = mapper   
        self.transaction_service = transaction_service
    
    def create_payment(self, payment: PaymentData) -> ServicePaymentResponse:
        yoo_payment = self.mapper.map_payment(payment)
        payment = Payment.create(yoo_payment, payment.idempotency_key)
        return self.mapper.map_payment_response(payment)
    
    async def get_payment(self, transaction_id: str) -> ServicePaymentResponse | None:
        transaction = await self.transaction_service.get_transaction(transaction_id)
        try:
            payment = Payment.find_one(transaction.payment_id)
        except NotFoundError:
            return None
        else:
            return self.mapper.map_payment_response(payment)

    async def commit_subs_payment(self, tsn_id: UUID, tsn_type: TransactionType, user_subs: UserSubscription, payment: ServicePaymentResponse):
        payment_transaction = Transaction(
            id = tsn_id,
            user_id=user_subs.user_id,
            payment_id=payment.payment_id,
            amount=user_subs.subscription.amount,
            currency=user_subs.subscription.currency,
            status_code=OperationStatus.PROCESSING,
            transaction_type=tsn_type,
            user_subscription=user_subs,
        )
        self.session.add_all([user_subs, payment_transaction])
        await self.session.commit()

    def create_autopayment(self, autopayment: AutopaymentData) -> ServicePaymentResponse:
        yoo_autopayment = self.mapper.map_autopayment(autopayment)
        autopayment_response = Payment.create(yoo_autopayment, autopayment.idempotency_key)
        return self.mapper.map_payment_response(autopayment_response)


def get_payment_service(
        session: Annotated[AsyncSession, Depends(get_db)],
        transaction_service: Annotated[TransactionServiceABC, Depends(get_transaction_service)],
) -> PaymentServiceABC:
    payment_mapper = get_payment_mapper()
    return YooKassaPaymentService(session, payment_mapper, transaction_service)
