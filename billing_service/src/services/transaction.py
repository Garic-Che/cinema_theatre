from uuid import UUID
from abc import ABC, abstractmethod
from typing import Annotated

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from db.postgres import get_db
from models.entity import Transaction
from exceptions.billing import AppException


class TransactionServiceABC(ABC):
    @abstractmethod
    async def get_transaction(self, transaction_id: str) -> Transaction:
        pass


class TransactionService(TransactionServiceABC):
    def __init__(self, session: AsyncSession):
        self.session = session
   
    async def get_transaction(self, transaction_id: UUID) -> Transaction:
        stmt = select(Transaction).where(
            Transaction.id == transaction_id
        ).limit(1).options(selectinload(Transaction.user_subscription))
        result = await self.session.execute(stmt) 

        if not (transaction := result.scalar()):
            raise AppException("No transaction found with id provided")
        return transaction


def get_transaction_service(
        session: Annotated[AsyncSession, Depends(get_db)]
) -> TransactionServiceABC:
    return TransactionService(session)
