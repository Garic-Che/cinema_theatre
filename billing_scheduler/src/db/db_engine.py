from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, update
from datetime import datetime, timedelta

from models.entity import Subscription, UserSubscription, Transaction
from core.config import settings
from schemas.model import TransactionType


class DBEngine:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_role_ids(self) -> list[str]:
        """Получение id ролей из подписок"""
        roles = await self.session.execute(
            select(Subscription.role_id).where(Subscription.actual)
        )
        return roles.scalars().all()

    async def update_by_role_id(self, role_id: str, data: dict):
        """Обновление подписок по id роли"""
        await self.session.execute(
            update(Subscription)
            .where(Subscription.role_id == role_id)
            .values(data)
        )
        await self.session.commit()

    async def get_expired_subscriptions(self) -> list[UserSubscription]:
        """Получение просроченных подписок"""
        expired_subscription = await self.session.execute(
            select(UserSubscription).where(
                (UserSubscription.expires < datetime.now())
                & (
                    UserSubscription.expires
                    > datetime.now()
                    - timedelta(
                        days=settings.subscription_soon_expiration_days
                    )
                )
            )
        )
        return expired_subscription.scalars().all()

    async def delete_user_subscriptions(
        self, user_subscriptions: list[UserSubscription]
    ):
        """Удаление подписок"""
        await self.session.execute(
            delete(UserSubscription).where(
                UserSubscription.id.in_(user_subscriptions)
            )
        )
        await self.session.commit()

    async def user_subscription_soon_expiration(
        self, days: int
    ) -> list[UserSubscription]:
        """Получение подписок, срок действия которых
        истекает в ближайшие days дней"""
        user_subscriptions = await self.session.execute(
            select(UserSubscription).where(
                (UserSubscription.expires >= datetime.now())
                & (
                    UserSubscription.expires
                    < datetime.now() + timedelta(days=days)
                )
            )
        )
        return user_subscriptions.scalars().all()

    async def get_role_id_by_subscription_id(
        self, subscription_id: str
    ) -> str:
        """Получение id роли по id подписки"""
        role_id = await self.session.execute(
            select(Subscription.role_id).where(
                Subscription.id == subscription_id
            )
        )
        return role_id.scalar_one_or_none()

    async def get_user_subscription_by_id(
        self, user_subscription_id: str
    ) -> UserSubscription:
        """Получение пользовательской подписки по id"""
        user_subscription = await self.session.execute(
            select(UserSubscription).where(
                UserSubscription.id == user_subscription_id
            )
        )
        return user_subscription.scalar_one_or_none()

    async def get_subscription_by_id(
        self, subscription_id: str
    ) -> Subscription:
        """Получение подписки по id подписки"""
        subscription = await self.session.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        return subscription.scalar_one_or_none()

    async def get_transactions_with_status_code(
        self, status_code: int
    ) -> list[Transaction]:
        """Получение транзакций с определенным статусом"""
        transactions = await self.session.execute(
            select(Transaction).where(Transaction.status_code == status_code)
        )
        return transactions.scalars().all()

    async def update_transaction_status(
        self, transaction_id: str, status_code: int
    ):
        """Обновление статуса транзакции"""
        await self.session.execute(
            update(Transaction)
            .where(Transaction.id == transaction_id)
            .values(status_code=status_code)
        )
        await self.session.commit()

    async def update_user_subscription(
        self, user_subscription: UserSubscription, params: dict
    ):
        """Обновление подписки"""
        await self.session.execute(
            update(UserSubscription)
            .where(UserSubscription.id == user_subscription.id)
            .values(**params)
        )
        await self.session.commit()

    async def update_transaction(self, transaction_id: str, params: dict):
        """Обновление статуса платежной транзакции по id платежа"""
        await self.session.execute(
            update(Transaction)
            .where(Transaction.id == transaction_id)
            .values(**params)
        )
        await self.session.commit()

    async def shift_back_in_time_next_payment_transactions(
        self, from_time: datetime, delta_expires: int
    ):
        """Сдвиг во времени следующих платежных транзакций
        после from_time (включительно) на delta_expires дней"""
        await self.session.execute(
            update(Transaction)
            .where(Transaction.starts >= from_time)
            .where(
                Transaction.transaction_type.in_(
                    [TransactionType.PAYMENT, TransactionType.AUTOPAYMENT]
                )
            )
            .values(
                starts=Transaction.starts + timedelta(days=delta_expires),
                ends=Transaction.ends + timedelta(days=delta_expires),
            )
        )
        await self.session.commit()

    async def get_transaction_by_id(self, transaction_id: str) -> Transaction:
        """Получение транзакции по id"""
        transaction = await self.session.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        return transaction.scalar_one_or_none()
