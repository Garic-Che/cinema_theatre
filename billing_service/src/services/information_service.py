# Абстрактный сервис
import uuid
from abc import ABC, abstractmethod

from schemas.entity import PaginatedSubscriptions,PaginatedUserSubscriptions,TransactionsList

from db.postgres import ISubscriptionRepository



class ISubscriptionService(ABC):
    @abstractmethod
    async def list_subscriptions(
        self,
        page: int,
        size: int,
        is_active: bool | None = None
    ) -> PaginatedSubscriptions:
        pass

    @abstractmethod
    async def list_user_subscriptions(
            self,
            user_id: uuid.UUID,
            page: int,
            size: int
    ) -> PaginatedUserSubscriptions:
        pass

    @abstractmethod
    async def list_transactions(
            self,
            user_subscription_id: uuid.UUID
    ) -> TransactionsList:
        pass

class SubscriptionService(ISubscriptionService):
    def __init__(self, repository: ISubscriptionRepository):
        self.repository = repository

    async def list_subscriptions(
        self,
        page: int,
        size: int,
        is_active: bool | None = None
    ) -> PaginatedSubscriptions:
        total, items = await self.repository.get_subscriptions(page, size, is_active)
        return PaginatedSubscriptions(
            total=total,
            page=page,
            size=size,
            items=items
        )

    async def list_user_subscriptions(
            self,
            user_id: uuid.UUID,
            page: int,
            size: int
    ) -> PaginatedUserSubscriptions:
        total, items = await self.repository.get_user_subscriptions(user_id, page, size)
        return PaginatedUserSubscriptions(
            total=total,
            page=page,
            size=size,
            items=items
        )

    async def list_transactions(
            self,
            user_subscription_id: uuid.UUID
    ) -> TransactionsList:
        return TransactionsList(
            items=await self.repository.get_transactions_by_subscription(user_subscription_id)
        )