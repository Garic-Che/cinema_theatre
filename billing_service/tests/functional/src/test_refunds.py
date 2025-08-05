import pytest
from datetime import datetime, timedelta
from http import HTTPStatus
from httpx import AsyncClient
from schemas.service import OperationStatus, TransactionType
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.asyncio
@patch("services.refund.YooKassaRefundService.create_refund")
@patch(
    "services.transaction.TransactionService.get_transaction", new_callable=AsyncMock
)
@pytest.mark.parametrize(
    "original_status,expected_status",
    [
        # (OperationStatus.COMPLETED.value, HTTPStatus.OK),
        (OperationStatus.PROCESSING.value, HTTPStatus.BAD_REQUEST),
        (OperationStatus.FAILED.value, HTTPStatus.BAD_REQUEST),
    ],
)
async def test_refund_payment(
    mock_get_transaction,
    mock_refund_create,
    async_client: AsyncClient,
    db_session,
    subscription_factory,
    user_subscription_factory,
    transaction_factory,
    original_status,
    expected_status,
):
    # Настройка моков
    if expected_status == HTTPStatus.OK:
        mock_refund = MagicMock()
        mock_refund.id = "ref123"
        mock_refund.status = "succeeded"
        mock_refund.amount = 100.0
        mock_refund.currency = "RUB"
        mock_refund_create.return_value = mock_refund

    subscription = await subscription_factory(db_session)
    user_subs = await user_subscription_factory(
        db_session,
        subscription=subscription,
        expires=datetime.utcnow() + timedelta(days=30),
    )

    transaction = await transaction_factory(
        db_session,
        user_subscription=user_subs,
        status_code=original_status,
        transaction_type=TransactionType.PAYMENT.value,
        payment_id="pay123",
        idempotence_key="key123",
    )

    # Настройка моков
    mock_get_transaction.return_value = transaction

    response = await async_client.post(
        "/api/v1/billing/refund",
        json={
            "user_id": str(transaction.user_id),
            "transaction_id": str(transaction.id),
            "amount": 100.0,
            "currency": "RUB",
        },
        headers={"X-Internal-Auth": "INTERNAL_BILLING_SECRET_KEY"},
    )

    # Проверки
    if response.status_code != expected_status:
        print(f"Error response: {response.text}")
    assert response.status_code == expected_status
    if expected_status == HTTPStatus.OK:
        assert "transaction_id" in response.json()
