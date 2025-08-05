from typing import Annotated
from uuid import UUID
from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession
from yookassa import Refund
from yookassa.domain.exceptions import NotFoundError
from yookassa.domain.exceptions.bad_request_error import BadRequestError
from fastapi import Depends

from db.postgres import get_db
from exceptions.billing import AppException
from schemas.service import RefundData, ServiceRefundResponse, OperationStatus, TransactionType
from utils.mapping import get_refund_mapper, YooKassaRefundMapper
from models.entity import Transaction
from services.transaction import TransactionServiceABC, get_transaction_service


class RefundServiceABC(ABC):
    @abstractmethod
    def create_refund(self, refund: RefundData) -> ServiceRefundResponse:
        pass

    @abstractmethod
    async def get_refund(self, transaction_id: str) -> ServiceRefundResponse | None:
        pass

    @abstractmethod
    async def commit_refund(self, tsn_id: UUID, tsn_to_refund: Transaction, refund: ServiceRefundResponse) -> None:
        pass


class YooKassaRefundService(RefundServiceABC):
    def __init__(
            self, 
            session: AsyncSession, 
            mapper: YooKassaRefundMapper,
            transaction_service: TransactionServiceABC
        ):
        self.session = session
        self.mapper = mapper  
        self.transaction_service = transaction_service 

    def create_refund(self, refund: RefundData) -> ServiceRefundResponse:
        yoo_refund = self.mapper.map_refund(refund)
        try:
            refund_response = Refund.create(yoo_refund, refund.idempotency_key)
        except BadRequestError as e:
            raise AppException(e.content.get('description'))
        else:
            return self.mapper.map_refund_response(refund_response)

    async def get_refund(self, transaction_id: str) -> ServiceRefundResponse | None:
        transaction = await self.transaction_service.get_transaction(transaction_id)
        try:
            refund = Refund.find_one(transaction.payment_id)
        except NotFoundError:
            return None
        else:
            return self.mapper.map_refund_response(refund)
        
    async def commit_refund(self, tsn_id: UUID, tsn_to_refund: Transaction, refund: ServiceRefundResponse) -> None:
        refund_transaction = Transaction(
            id=tsn_id,
            user_id=tsn_to_refund.user_id,
            payment_id=refund.refund_id,
            amount=refund.amount,
            currency=refund.currency,
            status_code=OperationStatus.PROCESSING,
            transaction_type=TransactionType.REFUND,
            user_subscription=tsn_to_refund.user_subscription,
        )
        self.session.add(refund_transaction)
        await self.session.commit()
        

def get_refund_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    transaction_service: Annotated[TransactionServiceABC, Depends(get_transaction_service)],
) -> RefundServiceABC:
    refund_mapper = get_refund_mapper()
    return YooKassaRefundService(session, refund_mapper, transaction_service)
