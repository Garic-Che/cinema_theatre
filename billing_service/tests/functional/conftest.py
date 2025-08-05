import os
import sys
import pytest
import uuid
import pytest_asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from httpx import AsyncClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool
from schemas.service import OperationStatus, TransactionType

# Добавляем путь к src в PYTHONPATH для корректных импортов
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "src"))
sys.path.insert(0, src_path)
# Берем глобальные переменные из .env
load_dotenv()

from db.postgres import Base
from models.entity import Transaction, Subscription, UserSubscription, Base

load_dotenv()


# Фикстура для engine БД
@pytest_asyncio.fixture(scope="session")
async def db_engine():
    db_url = os.getenv("DB_URL")
    engine = create_async_engine(
        db_url.replace("postgresql", "postgresql+asyncpg"), poolclass=NullPool
    )
    yield engine
    await engine.dispose()


# Фикстура для БД
@pytest_asyncio.fixture
async def db_session(db_engine):
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

    session = async_session()
    try:
        yield session
    finally:
        await session.close()
        await db_engine.dispose()


# Фикстура для клиента
@pytest_asyncio.fixture
async def async_client():
    base_url = os.getenv("BILLING_SERVICE_URL")
    api_secret = os.getenv("BILLING_API_SECRET_KEY", "INTERNAL_BILLING_SECRET_KEY")

    async with AsyncClient(
        base_url=base_url, timeout=30, headers={"X-Internal-Auth": api_secret}
    ) as client:
        yield client


# Фабрики
@pytest.fixture
def subscription_factory():
    async def factory(db_session, **kwargs):
        subscription = Subscription(
            id=kwargs.get("id", uuid.uuid4()),
            role_id=kwargs.get("role_id", uuid.uuid4()),
            name=kwargs.get("name", "Test"),
            description=kwargs.get("description", "Test subscription"),
            amount=kwargs.get("amount", 100.0),
            currency=kwargs.get("currency", "RUB"),
            period=kwargs.get("period", 30),
            actual=kwargs.get("actual", True),
        )
        db_session.add(subscription)
        await db_session.commit()
        return subscription

    return factory


@pytest.fixture
def user_subscription_factory():
    async def factory(db_session, subscription=None, **kwargs):
        if subscription is None:
            subscription = await subscription_factory(db_session)

        user_subscription = UserSubscription(
            id=kwargs.get("id", uuid.uuid4()),
            user_id=kwargs.get("user_id", uuid.uuid4()),
            subscription_id=subscription.id,
            auto_pay_id=kwargs.get("auto_pay_id"),
            expires=kwargs.get("expires", datetime.utcnow() + timedelta(days=30))
        )
        db_session.add(user_subscription)
        await db_session.commit()
        return user_subscription

    return factory


@pytest.fixture
def transaction_factory():
    async def factory(db_session, user_subscription, **kwargs):
        transaction_type = kwargs.get("transaction_type")
        if isinstance(transaction_type, TransactionType):
            transaction_type = transaction_type.value

        transaction = Transaction(
            id=kwargs.get("id", uuid.uuid4()),
            user_id=user_subscription.user_id,
            payment_id=kwargs.get("payment_id", f"pay_{uuid.uuid4()}"),
            user_subscription_id=user_subscription.id,
            amount=kwargs.get("amount", 100.0),
            currency=kwargs.get("currency", "RUB"),
            status_code=kwargs.get("status_code", OperationStatus.PROCESSING.value),
            # transaction_type=kwargs.get("transaction_type", TransactionType.PAYMENT.value),
            transaction_type=transaction_type or TransactionType.PAYMENT.value,
            starts=kwargs.get("starts", datetime.utcnow()),
            ends=kwargs.get("ends", datetime.utcnow() + timedelta(days=30)),
        )
        db_session.add(transaction)
        await db_session.commit()
        return transaction

    return factory
