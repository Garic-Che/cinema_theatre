import logging
import uuid
from abc import ABC, abstractmethod

from sqlalchemy import select, func
from sqlalchemy.orm import declarative_base, selectinload
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from core.config import settings

from schemas.entity import SubscriptionOut, UserSubscriptionOut, TransactionOut
from models.entity import Subscription, UserSubscription, Transaction
from db.base import Base

engine = create_async_engine(url=settings.dsn)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# Абстрактный репозиторий
class ISubscriptionRepository(ABC):
    @abstractmethod
    async def get_subscriptions(
        self, page: int, size: int, is_active: bool | None = None
    ) -> tuple[int, list[SubscriptionOut]]:
        pass

    @abstractmethod
    async def get_user_subscriptions(
        self,
        user_id: uuid.UUID,
        page: int,
        size: int,
    ) -> tuple[int, list[UserSubscriptionOut]]:
        pass

    @abstractmethod
    async def get_transactions_by_subscription(
        self, user_subscription_id: uuid.UUID
    ) -> list[TransactionOut]:
        pass


class SubscriptionRepository(ISubscriptionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_subscriptions(
        self, page: int, size: int, is_active: bool | None = None
    ) -> tuple[int, list[SubscriptionOut]]:
        stmt = select(Subscription)

        if is_active is not None:
            stmt = stmt.where(Subscription.actual == is_active)

        # Получаем общее количество
        count_stmt = select(func.count()).select_from(Subscription)
        if is_active is not None:
            count_stmt = count_stmt.where(Subscription.actual == is_active)

        total = (await self.session.execute(count_stmt)).scalar_one()

        # Добавляем пагинацию
        stmt = (
            stmt.order_by(Subscription.created.desc())
            .offset((page - 1) * size)
            .limit(size)
        )

        result = await self.session.execute(stmt)
        subscriptions = [
            SubscriptionOut.model_validate(subscription)  # Новый метод в Pydantic v2
            for subscription in result.scalars()
        ]

        return total, subscriptions

    async def get_user_subscriptions(
        self,
        user_id: uuid.UUID,
        page: int,
        size: int,
    ) -> tuple[int, list[UserSubscriptionOut]]:
        stmt = (
            select(UserSubscription)
            .where(UserSubscription.user_id == user_id)
            .options(selectinload(UserSubscription.subscription))
        )

        count_stmt = select(func.count()).where(UserSubscription.user_id == user_id)
        total = (await self.session.execute(count_stmt)).scalar_one()

        result = await self.session.execute(
            stmt.order_by(UserSubscription.created.desc())
            .offset((page - 1) * size)
            .limit(size)
        )

        return total, [
            UserSubscriptionOut.model_validate(sub) for sub in result.scalars()
        ]

    async def get_transactions_by_subscription(
            self, user_subscription_id: uuid.UUID
    ) -> list[TransactionOut]:
        # Логируем начало выполнения
        logging.info("Starting query for transactions with user_subscription_id: %s", user_subscription_id)

        # Формируем запрос
        stmt = select(Transaction).where(
            Transaction.user_subscription_id == user_subscription_id
        )
        logging.info("SQL statement: %s", str(stmt))

        # Выполняем запрос
        result = await self.session.execute(stmt)

        # Получаем сырые результаты
        raw_results = result.scalars().all()
        logging.info("Found %d transactions for subscription %s", len(raw_results), user_subscription_id)

        if not raw_results:
            logging.warning("No transactions found for subscription %s", user_subscription_id)

        # Преобразуем и валидируем результаты
        transactions = []
        for t in raw_results:
            try:
                validated = TransactionOut.model_validate(t)
                transactions.append(validated)
                logging.debug("Validated transaction: %s", validated)
            except Exception as e:
                logging.error("Validation error for transaction %s: %s", t.id, str(e))

        logging.info("Returning %d valid transactions", len(transactions))
        return transactions


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def create_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def purge_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
