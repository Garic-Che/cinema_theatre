import pytest
from http import HTTPStatus
from datetime import datetime, timedelta
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock
from schemas.service import (
    OperationStatus, 
    TransactionType, 
    ServicePaymentResponse, 
    ServicePaymentMethodResponse
    )


@pytest.mark.asyncio
async def test_handle_validation_error(async_client: AsyncClient):
    # с неверными данными
    response = await async_client.post(
        "/api/v1/billing/payment",
        json={"invalid": "data"},
        headers={"X-Internal-Auth": "INTERNAL_BILLING_SECRET_KEY"}
    )
    
    # Проверки
    assert "detail" in response.json()


@pytest.mark.asyncio
@patch('services.payment.YooKassaPaymentService.create_payment')
@patch('services.subscription.SubscriptionService.get_subs_by_id', new_callable=AsyncMock)
@patch('services.subscription.SubscriptionService.get_or_create_subs_for_user', new_callable=AsyncMock)
@pytest.mark.parametrize("amount,currency,expected_status", [
    (100.0, "RUB", HTTPStatus.OK),
    (50.0, "RUB", HTTPStatus.OK),
    # (0, "RUB", HTTPStatus.BAD_REQUEST),
])
async def test_pay_for_subscription(
    mock_get_or_create_subs,
    mock_get_subs,
    mock_payment_create,
    async_client: AsyncClient,
    db_session,
    subscription_factory,
    user_subscription_factory,
    amount,
    currency,
    expected_status
):
    # Настройка моков
    if expected_status == HTTPStatus.OK:
        mock_payment_response = MagicMock()
        mock_payment_response.confirmation_url = 'https://redirect.url'
        mock_payment_create.return_value = mock_payment_response

    subscription = await subscription_factory(
        db_session,
        amount=amount,
        currency=currency
    )

    user_subs = await user_subscription_factory(
        db_session,
        subscription=subscription,
        expires=datetime.utcnow() + timedelta(days=30)
    )

    # Настройка моков
    mock_get_subs.return_value = subscription
    mock_get_or_create_subs.return_value = user_subs

    user_id = str(user_subs.user_id)

    response = await async_client.post(
        "/api/v1/billing/payment",
        json={
            "user_id": user_id,
            "subscription_id": str(subscription.id)
        },
        headers={"X-Internal-Auth": "INTERNAL_BILLING_SECRET_KEY"}
    )

    # Проверки
    if response.status_code != expected_status:
        print(f"Error response: {response.text}")
    assert response.status_code == expected_status
    if expected_status == HTTPStatus.OK:
        response_data = response.json()
        assert "redirect_url" in response_data
        assert response_data["redirect_url"].startswith("https://")


# Тест для получения состояния платежа
@pytest.mark.asyncio
@patch('services.payment.YooKassaPaymentService.get_payment', new_callable=AsyncMock)
async def test_get_payment_state(
    mock_get_payment,
    async_client: AsyncClient,
    db_session,
    subscription_factory,
    user_subscription_factory,
    transaction_factory
):
    subscription = await subscription_factory(db_session)
    user_subs = await user_subscription_factory(db_session, subscription=subscription)
    
    transaction = await transaction_factory(
        db_session,
        user_subscription=user_subs,
        transaction_type=TransactionType.PAYMENT.value,
        payment_id="test_payment_id"
    )
    
    assert transaction.transaction_type == TransactionType.PAYMENT.value
    
    # Настройка моков
    mock_payment = ServicePaymentResponse(
        payment_id='pay123',
        status=OperationStatus.COMPLETED.value,
        confirmation_url='https://example.com',
        payment_method_id='pm123',
        amount=100.0,
        currency='RUB'
    )
    mock_get_payment.return_value = mock_payment
    
    response = await async_client.get(
        f"/api/v1/state/payment/{transaction.id}",
        headers={"X-Internal-Auth": "INTERNAL_BILLING_SECRET_KEY"}
    )
    
    # Проверки
    assert response.status_code == HTTPStatus.OK
    response_data = response.json()
    assert response_data["status"] == "completed"
    assert response_data["payment_id"] == "pay123"


# Тест для получения состояния метода оплаты
@pytest.mark.asyncio
@patch('services.payment_method.YooKassaPaymentMethodService.get_payment_method')
async def test_get_payment_method_state(
    mock_get_payment_method,
    async_client: AsyncClient,
    db_session,
    subscription_factory,
    user_subscription_factory,
    transaction_factory
):
    subscription = await subscription_factory(db_session)
    user_subs = await user_subscription_factory(db_session, subscription=subscription)
    
    transaction = await transaction_factory(
        db_session,
        user_subscription=user_subs,
        transaction_type=TransactionType.PAYMENT_METHOD_ADD.value
    )
    
    assert transaction.transaction_type == TransactionType.PAYMENT_METHOD_ADD.value
    
    # Настройка моков
    mock_payment_method = ServicePaymentMethodResponse(
        status=OperationStatus.COMPLETED.value,
        confirmation_url='https://example.com',
        payment_method_id='pm123',
        amount=100.0,
        currency='RUB'
    )
    mock_get_payment_method.return_value = mock_payment_method
    
    response = await async_client.get(
        f"/api/v1/state/payment-method/{transaction.id}",
        headers={"X-Internal-Auth": "INTERNAL_BILLING_SECRET_KEY"}
    )
    
    # Проверки
    assert response.status_code == HTTPStatus.OK
    response_data = response.json()
    assert response_data["status"] == "active"
    assert response_data["payment_method_id"] == "pm123"