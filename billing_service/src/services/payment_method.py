from typing import Any, Annotated
from uuid import UUID
from abc import ABC, abstractmethod

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_db
from repositories.payment_method import PaymentMethodRepositoryABC, get_payment_method_repository
from utils.mapping import YooKassaPaymentMethodMapper, get_payment_method_mapper
from schemas.service import ServicePaymentMethodResponse, OperationStatus, TransactionType, PaymentMethodData
from models.entity import UserSubscription, Transaction
from services.transaction import TransactionServiceABC, get_transaction_service


NO_AMOUNT = 0
NO_CURRENCY = ""


class PaymentMethodServiceABC(ABC):
    @abstractmethod
    async def create_payment_method(self, payment_method: PaymentMethodData) -> ServicePaymentMethodResponse:
        pass

    @abstractmethod
    async def commit_payment_method(self, tsn_id: UUID, tsn_type: TransactionType, user_subs: UserSubscription, payment_method_id: UUID) -> None:
        pass

    @abstractmethod
    async def get_payment_method(self, transaction_id: str) -> ServicePaymentMethodResponse:
        pass


class YooKassaPaymentMethodService:
    def __init__(
        self,
        session: AsyncSession,
        payment_method_repository: PaymentMethodRepositoryABC,
        payment_method_mapper: YooKassaPaymentMethodMapper,
        transaction_service: TransactionServiceABC,
    ):
        self.session = session
        self.payment_method_repository = payment_method_repository
        self.payment_method_mapper = payment_method_mapper
        self.transaction_service = transaction_service

    async def create_payment_method(self, payment_method: PaymentMethodData) -> ServicePaymentMethodResponse:
        raw_response = await self.payment_method_repository.create_payment_method(payment_method)
        return self.payment_method_mapper.map_payment_method_response(raw_response)
    
    async def get_payment_method(self, transaction_id: str) -> ServicePaymentMethodResponse:
        transaction = await self.transaction_service.get_transaction(transaction_id)
        response = await self.payment_method_repository.get_payment_method(transaction.payment_id)
        return self.payment_method_mapper.map_payment_method_response(response)

    async def commit_payment_method(self, tsn_id: UUID, tsn_type: TransactionType, user_subs: UserSubscription, payment_method_id: UUID) -> None:
        payment_transaction = Transaction(
            id=tsn_id,
            user_id=user_subs.user_id,
            payment_id=payment_method_id,
            amount=NO_AMOUNT,
            currency=NO_CURRENCY,
            status_code=OperationStatus.PROCESSING,
            transaction_type=tsn_type,
            user_subscription=user_subs,
        )
        self.session.add(payment_transaction)
        await self.session.commit()
    

def get_payment_method_service(
        session: Annotated[AsyncSession, Depends(get_db)],
        transaction_service: Annotated[TransactionServiceABC, Depends(get_transaction_service)],
) -> PaymentMethodServiceABC:
    return YooKassaPaymentMethodService(
        session,
        get_payment_method_repository(),
        get_payment_method_mapper(),
        transaction_service,
    )
