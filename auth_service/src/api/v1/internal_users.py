from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, Request

from utils.authtorize_helpers import (
    internal_auth_required,
)
from services.user import UserService, get_user_service
from api.v1.schemes import (
    Users,
    User,
)

router = APIRouter()


@router.get(
    "/group/{group_name}",
    response_model=Users,
    summary="Получение пользователей по группе рассылки",
)
@internal_auth_required
async def get_group_users(
    request: Request,
    group_name: str,
    service: UserService = Depends(get_user_service),
) -> Users:
    # TODO
    return Users(ids=[])


@router.get(
    "/roles/{roles}",
    response_model=Users,
    summary="Получение пользователей по ролям",
)
@internal_auth_required
async def get_roles_users(
    request: Request,
    roles: str,
    service: UserService = Depends(get_user_service),
) -> Users:
    # TODO
    return Users(ids=[])


@router.get(
    "/{user_id}",
    response_model=User,
    summary="Получение пользователя по id",
)
@internal_auth_required
async def get_user_by_id(
    request: Request,
    user_id: str,
    service: UserService = Depends(get_user_service),
) -> User:
    user = service.get_user_profile_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="User not found"
        )

    return User(
        id=user.id,
        login=user.login,
        email=user.email,
        created=user.created,
    )
