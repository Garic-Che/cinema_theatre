from uuid import UUID
from typing import Annotated
from abc import ABC, abstractmethod
from datetime import datetime

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_db
from models.entity import Subscription, UserSubscription
from exceptions.billing import AppException


class SubscriptionServiceABC(ABC):
    @abstractmethod
    async def get_subs_by_role_id(self, role_id: UUID) -> Subscription:
        pass

    @abstractmethod
    async def get_or_create_subs_for_user(self, user_id: UUID, subscription_id: UUID) -> UserSubscription:
        pass

    @abstractmethod
    async def get_subs_by_id(self, subs_id: UUID) -> Subscription:
        pass

    @abstractmethod
    async def get_user_subs_by_id(self, user_subs_id: UUID) -> UserSubscription:
        pass


class SubscriptionService(SubscriptionServiceABC):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_subs_by_role_id(self, role_id: UUID) -> Subscription:
        stmt = select(Subscription).where(Subscription.role_id == role_id).limit(1)
        result = await self.session.execute(stmt)
        
        if not (subs := result.scalar()):
            raise AppException("No subscription matches role_id passed")
        return subs
    
    async def get_or_create_subs_for_user(self, user_id: UUID, subscription_id: UUID) -> UserSubscription:
        subs = await self.get_subs_by_id(subscription_id)
        
        stmt = select(UserSubscription).where(
            (UserSubscription.subscription_id == subs.id) & (UserSubscription.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        
        if not (user_subs := result.scalar()):    
            user_subs = UserSubscription(
                user_id=user_id,
                subscription_id=subs.id,
                subscription=subs,
                expires=datetime.utcnow(),
            )
        return user_subs
    
    async def get_subs_by_id(self, subs_id: UUID) -> Subscription:
        if not (subs := await self.session.get(Subscription, subs_id)):
            raise AppException("No subscription found by id passed")
        return subs
    
    async def get_user_subs_by_id(self, user_subs_id: UUID) -> UserSubscription:
        stmt = select(UserSubscription).where(
            UserSubscription.id == user_subs_id
        ).limit(1).options(selectinload(UserSubscription.subscription))
        result = await self.session.execute(stmt) 

        if not (user_subs := result.scalar()):
            raise AppException("No user subsciption found for id provided")
        return user_subs



def get_subscription_service(
        session: Annotated[AsyncSession, Depends(get_db)]
) -> SubscriptionServiceABC:
    return SubscriptionService(session)
