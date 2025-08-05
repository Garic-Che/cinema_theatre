from uuid import UUID

from fastapi import APIRouter, Depends, Query,Request
from sqlalchemy.ext.asyncio import AsyncSession

from utils.authtorize_helpers import jwt_or_internal_auth_required
from db.postgres import get_db, ISubscriptionRepository, SubscriptionRepository
from schemas.entity import (
    PaginatedSubscriptions,
    PaginatedSubscriptions,
    PaginatedUserSubscriptions,
    TransactionsList,
)
from services.information_service import ISubscriptionService, SubscriptionService


router = APIRouter()


# Зависимости
async def get_subscription_repository(
    session: AsyncSession = Depends(get_db),  # get_db из postgres.py
) -> ISubscriptionRepository:
    return SubscriptionRepository(session)


async def get_subscription_service(
    repository: ISubscriptionRepository = Depends(get_subscription_repository),
) -> ISubscriptionService:
    return SubscriptionService(repository)


# Эндпоинт
@router.get(
    "/subscriptions",
    response_model=PaginatedSubscriptions,
    summary="Получить список подписок",
    description="Возвращает список подписок с пагинацией и фильтрацией по активности",
)
async def list_subscriptions(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(10, ge=1, le=100, description="Размер страницы"),
    is_active: bool | None = Query(
        None, description="Фильтр по активности (true/false)"
    ),
    service: ISubscriptionService = Depends(get_subscription_service),
) -> PaginatedSubscriptions:
    return await service.list_subscriptions(page, size, is_active)


@router.get(
    "/subscriptions/user/{user_id}",
    response_model=PaginatedUserSubscriptions,
    summary="Подписки пользователя",
    response_description="Список подписок с пагинацией",
)
@jwt_or_internal_auth_required
async def get_user_subscriptions(
    request: Request,
    user_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    service: ISubscriptionService = Depends(get_subscription_service),
) -> PaginatedUserSubscriptions:
    return await service.list_user_subscriptions(user_id, page, size)


@router.get(
    "/transactions/{user_subscription_id}",
    response_model=TransactionsList,
    summary="Транзакции подписки",
    response_description="Список всех транзакций по подписке",
)
@jwt_or_internal_auth_required
async def get_subscription_transactions(
    request: Request,
    user_subscription_id: UUID,
    service: ISubscriptionService = Depends(get_subscription_service),
) -> TransactionsList:
    return await service.list_transactions(user_subscription_id)
