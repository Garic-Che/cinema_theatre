from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from utils.authtorize_helpers import internal_auth_required, jwt_or_internal_auth_required
from services.billing import BillingServiceABC, get_billing_service
from schemas.entity import PaymentRequest, RefundRequest, AutopaymentRequest, PaymentMethodRequest


router = APIRouter()


@router.post(
    "/payment",
    summary="Subs payment",
)
@jwt_or_internal_auth_required
async def pay_for_subscription(
    request: Request,
    payment: PaymentRequest,
    service: Annotated[BillingServiceABC, Depends(get_billing_service)],
) -> JSONResponse:
    redirect_url = await service.pay_for_subscription(payment)
    return JSONResponse(content={"redirect_url": redirect_url})


@router.post(
    "/autopayment",
    summary="Autopayment",
)
@internal_auth_required
async def make_autopayment(
    request: Request,
    autopayment: AutopaymentRequest,
    service: Annotated[BillingServiceABC, Depends(get_billing_service)],
) -> JSONResponse:
    transaction_id = await service.make_autopayment(autopayment)
    return JSONResponse(content={"status": "success", "payment_id": transaction_id})


@router.post(
    "/refund",
    summary="Payment refund",
)
@internal_auth_required
async def refund_payment(
    request: Request,
    refund: RefundRequest,
    service: Annotated[BillingServiceABC, Depends(get_billing_service)],
) -> JSONResponse:
    await service.refund_payment(refund)
    return JSONResponse(content={"result": "refunded successfully"})


@router.post(
    "/autopayment-subscribe",
    summary="Subscribe to autopayments",
)
@jwt_or_internal_auth_required
async def subscribe_to_autopayments(
    request: Request,
    payment_method: PaymentMethodRequest,
    service: Annotated[BillingServiceABC, Depends(get_billing_service)],
) -> JSONResponse:
    confirmation_url = await service.create_payment_method(payment_method)
    return JSONResponse(content={"confirmation_url": confirmation_url})
    

@router.post(
    "/autopayment-unsubscribe",
    summary="Unsubscribe from autopayments",
)
@jwt_or_internal_auth_required
async def unsubscribe_from_autopayments(
    request: Request,
    payment_method: PaymentMethodRequest,
    service: Annotated[BillingServiceABC, Depends(get_billing_service)],
) -> JSONResponse:
    await service.remove_payment_method(payment_method)
    return {"status": "success"}
