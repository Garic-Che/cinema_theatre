from http import client
from typing import Annotated

from fastapi import APIRouter, Depends, Request, HTTPException

from services.payment import PaymentServiceABC, get_payment_service
from services.refund import RefundServiceABC, get_refund_service
from services.payment_method import PaymentMethodServiceABC, get_payment_method_service
from utils.authtorize_helpers import jwt_or_internal_auth_required


router = APIRouter()


@router.get(
    "/payment/{transaction_id}",
    summary="Payment",
)
@jwt_or_internal_auth_required
async def get_payment(
    request: Request,
    transaction_id: str,
    service: Annotated[PaymentServiceABC, Depends(get_payment_service)],
):
    payment = await service.get_payment(transaction_id)
    if not payment:
        raise HTTPException(
            status_code=client.NOT_FOUND,
            detail="The transaction seems to relate to a refund",
        )
    return payment
    

@router.get(
    "/refund/{transaction_id}",
    summary="Refund",
)
@jwt_or_internal_auth_required
async def get_refund(
    request: Request,
    transaction_id: str,
    service: Annotated[RefundServiceABC, Depends(get_refund_service)],
):
    refund = await service.get_refund(transaction_id)
    if not refund:
        raise HTTPException(
            status_code=client.NOT_FOUND,
            detail="The transaction seems to relate to a payment",
        )
    return refund
    

@router.get(
    "/payment-method/{transaction_id}",
    summary="Payment method",
)
@jwt_or_internal_auth_required
async def get_payment_method(
    request: Request,
    transaction_id: str,
    service: Annotated[PaymentMethodServiceABC, Depends(get_payment_method_service)],
):
    payment_method = await service.get_payment_method(transaction_id)
    if not payment_method:
        raise HTTPException(
            status_code=client.NOT_FOUND,
        )
    return payment_method
