import pytest
import pytest_asyncio
from datetime import datetime, timedelta
import sys
import os
from dotenv import load_dotenv

# Добавляем путь к src в PYTHONPATH для корректных импортов
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "src"))
sys.path.insert(0, src_path)
# Берем глобальные переменные из .env
load_dotenv()

from check_transactions import check_transactions
from delete_expired_subscription import delete_expired_subscription
from models.entity import (
    Transaction,
    Subscription,
    UserSubscription,
)
from schemas.model import (
    StatusCode,
    TransactionType,
    PaymentStatus,
)


@pytest_asyncio.fixture
def subscription():
    return Subscription(
        id="sub1",
        role_id="role1",
        name="Test",
        description="Test sub",
        amount=100.0,
        actual=True,
        currency="RUB",
        period=30,
    )


@pytest.fixture
def mock_services(mocker, subscription):
    """Фикстура для моков всех внешних сервисов"""
    # Мокаем все внешние сервисы
    mock_billing = mocker.patch("check_transactions.billing_service_engine")
    mock_notify = mocker.patch(
        "check_transactions.notification_service_engine"
    )
    mock_auth = mocker.patch("check_transactions.auth_service_engine")
    mock_get_db = mocker.patch("check_transactions.get_db")

    # Мокаем методы billing_service_engine
    mocker.patch(
        "check_transactions.billing_service_engine.check_payment",
        new_callable=mocker.AsyncMock,
        return_value=PaymentStatus(
            status=StatusCode.COMPLETED, payment_id="pay1"
        ),
    )
    # Мокаем методы notification_service_engine
    mocker.patch(
        "check_transactions.notification_service_engine.send_notification",
        new_callable=mocker.AsyncMock,
        return_value=None,
    )
    # Мокаем методы auth_service_engine
    mocker.patch(
        "check_transactions.auth_service_engine.assign_role",
        new_callable=mocker.AsyncMock,
        return_value=None,
    )
    mocker.patch(
        "check_transactions.auth_service_engine.revoke_role",
        new_callable=mocker.AsyncMock,
        return_value=None,
    )

    # Мокаем сессию и DBEngine
    class MockSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    def db_engine_factory(transaction, user_subscription):
        class MockDBEngine:
            def __init__(self, session):
                pass

            async def get_transactions_with_status_code(self, status_code):
                return [transaction]

            async def get_expired_subscriptions(self):
                return [user_subscription]

            async def get_role_id_by_subscription_id(self, subscription_id):
                return "role1"

            async def update_transaction_status(self, *a, **kw):
                pass

            async def get_user_subscription_by_id(self, _):
                return user_subscription

            async def get_subscription_by_id(self, _):
                return subscription

            async def update_user_subscription(self, *a, **kw):
                pass

            async def update_transaction(self, *a, **kw):
                pass

        return MockDBEngine

    mock_get_db.return_value = MockSession()
    return {
        "billing": mock_billing,
        "notify": mock_notify,
        "auth": mock_auth,
        "get_db": mock_get_db,
        "db_engine_factory": db_engine_factory,
    }


@pytest.fixture
def mock_services_delete_expired_subscription(mocker, subscription):
    """Фикстура для моков всех внешних сервисов"""
    # Мокаем все внешние сервисы
    mock_auth = mocker.patch("delete_expired_subscription.auth_service_engine")
    mock_get_db = mocker.patch("delete_expired_subscription.get_db")
    mock_redis = mocker.patch("delete_expired_subscription.redis_engine")

    # Мокаем методы auth_service_engine
    mocker.patch(
        "delete_expired_subscription.auth_service_engine.revoke_role",
        new_callable=mocker.AsyncMock,
        return_value=None,
    )
    mocker.patch(
        "delete_expired_subscription.redis_engine.get",
        return_value=False,
    )

    # Мокаем сессию и DBEngine
    class MockSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    def db_engine_factory(transaction, user_subscription):
        class MockDBEngine:
            def __init__(self, session):
                pass

            async def get_transactions_with_status_code(self, status_code):
                return [transaction]

            async def get_expired_subscriptions(self):
                return [user_subscription]

            async def get_role_id_by_subscription_id(self, subscription_id):
                return "role1"

            async def update_transaction_status(self, *a, **kw):
                pass

            async def get_user_subscription_by_id(self, _):
                return user_subscription

            async def get_subscription_by_id(self, _):
                return subscription

            async def update_user_subscription(self, *a, **kw):
                pass

            async def update_transaction(self, *a, **kw):
                pass

        return MockDBEngine

    mock_get_db.return_value = MockSession()
    return {
        "auth": mock_auth,
        "get_db": mock_get_db,
        "db_engine_factory": db_engine_factory,
        "redis_engine": mock_redis,
    }


@pytest.mark.asyncio
async def test_assign_role_on_success_transaction(
    mock_services, subscription, monkeypatch
):
    # Создаем данные для успешной транзакции
    transaction = Transaction(
        id="tx1",
        user_id="user1",
        payment_id="pay1",
        user_subscription_id="usub1",
        amount=100.0,
        currency="RUB",
        status_code=StatusCode.PROCESSING,
        transaction_type=TransactionType.PAYMENT,
        starts=datetime.now() - timedelta(minutes=5),
        ends=datetime.now() - timedelta(minutes=5),
        created=datetime.now() - timedelta(minutes=5),
    )

    user_subscription = UserSubscription(
        id="usub1",
        user_id="user1",
        subscription_id="sub1",
        expires=datetime.now() + timedelta(days=1),
    )

    db_engine = mock_services["db_engine_factory"](
        transaction, user_subscription
    )
    monkeypatch.setattr("check_transactions.DBEngine", db_engine)

    await check_transactions()

    # Проверяем, что assign_role был вызван
    mock_services["auth"].assign_role.assert_called_once_with("user1", "role1")
    # Проверяем, что отправлено уведомление
    mock_services["notify"].send_notification.assert_called()


@pytest.mark.asyncio
async def test_revoke_role_on_expired_subscription(
    mock_services_delete_expired_subscription, subscription, monkeypatch
):
    # Создаем данные для просроченной подписки
    transaction = Transaction(
        id="tx2",
        user_id="user2",
        payment_id="pay2",
        user_subscription_id="usub2",
        amount=50.0,
        currency="RUB",
        status_code=StatusCode.COMPLETED,
        transaction_type=TransactionType.PAYMENT,
        starts=datetime.now() - timedelta(days=30),
        ends=datetime.now() - timedelta(hours=1),
        created=datetime.now() - timedelta(days=30),
    )

    user_subscription = UserSubscription(
        id="usub2",
        user_id="user2",
        subscription_id="sub1",
        expires=datetime.now() - timedelta(hours=1),
    )

    db_engine = mock_services_delete_expired_subscription["db_engine_factory"](
        transaction, user_subscription
    )
    monkeypatch.setattr("delete_expired_subscription.DBEngine", db_engine)

    await delete_expired_subscription()

    # Проверяем, что revoke_role был вызван
    mock_services_delete_expired_subscription[
        "auth"
    ].revoke_role.assert_called_once_with("user2", "role1")
