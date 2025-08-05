import uuid
import pytest
from http import HTTPStatus
from httpx import AsyncClient
from unittest.mock import patch


# Тест для создания автоплатежа
@pytest.mark.asyncio
@patch("services.billing.BillingService.make_autopayment")
async def test_make_autopayment(
    mock_make_autopayment,
    async_client: AsyncClient,
    db_session,
    user_subscription_factory,
    subscription_factory,
):
    subscription = await subscription_factory(db_session)
    user_subs = await user_subscription_factory(
        db_session, subscription=subscription, auto_pay_id="test_payment_method"
    )

    # Настройка моков
    transaction_id = uuid.uuid4()
    mock_make_autopayment.return_value = str(transaction_id)

    response = await async_client.post(
        "/api/v1/billing/autopayment",
        json={"user_subscription_id": str(user_subs.id)},
        headers={"X-Internal-Auth": "INTERNAL_BILLING_SECRET_KEY"},
    )

    # Проверки
    if response.status_code != HTTPStatus.OK:
        print(f"Error response: {response.text}")
    assert response.status_code == HTTPStatus.OK
    response_data = response.json()
    assert "payment_id" in response_data
    assert response_data["payment_id"] == str(transaction_id)


@pytest.mark.asyncio
@patch("services.billing.BillingService.create_payment_method")
async def test_subscribe_to_autopayments(
    mock_create_payment_method,
    async_client: AsyncClient,
    db_session,
    user_subscription_factory,
    subscription_factory,
):
    subscription = await subscription_factory(db_session)
    user_subs = await user_subscription_factory(db_session, subscription=subscription)

    # Настройка моков
    mock_create_payment_method.return_value = "https://confirmation.url"

    response = await async_client.post(
        "/api/v1/billing/autopayment-subscribe",
        json={"user_subscription_id": str(user_subs.id)},
        headers={"X-Internal-Auth": "INTERNAL_BILLING_SECRET_KEY"},
    )

    # Проверки
    assert response.status_code == HTTPStatus.OK
    response_data = response.json()
    assert ("confirmation_url" in response_data) 
    assert response_data["confirmation_url"].startswith("https://")


# Тест для получения списка подписок
@pytest.mark.asyncio
async def test_list_subscriptions(
    async_client: AsyncClient, db_session, subscription_factory
):
    sub1 = await subscription_factory(db_session, name="Test", actual=True)
    sub2 = await subscription_factory(db_session, name="Basic", actual=False)

    response = await async_client.get(
        "/api/v1/subs_information/subscriptions?is_active=true&page=1&size=10",
        headers={"X-Internal-Auth": "INTERNAL_BILLING_SECRET_KEY"},
    )

    # Проверки
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Test"

    response = await async_client.get(
        "/api/v1/subs_information/subscriptions?page=1&size=10",
        headers={"X-Internal-Auth": "INTERNAL_BILLING_SECRET_KEY"},
    )

    # Проверки
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
