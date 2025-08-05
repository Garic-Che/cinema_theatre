import http
import http.client
from typing import Annotated
from uuid import UUID

from pydantic import HttpUrl
from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import RedirectResponse, JSONResponse

from services.link import LinkServiceABC, get_link_service
from exceptions.link import AppException
from core.config import settings
from utils.auth_middleware import internal_auth_required

router = APIRouter()


@router.get("/{link_id}")
@internal_auth_required
async def resolve_link(
    link_id: UUID,
    request: Request,
    link_service: Annotated[LinkServiceABC, Depends(get_link_service)],
):
    try:
        original_link = await link_service.resolve(link_id)
    except AppException as e:
        return JSONResponse(
            status_code=http.client.NOT_FOUND,
            content={"message": str(e)},
        )
    else:
        return RedirectResponse(url=original_link, status_code=http.client.FOUND)


@router.post("/")
@internal_auth_required
async def shorten_link(
    raw_link: Annotated[HttpUrl, Body(embed=True)],
    request: Request,
    link_service: Annotated[LinkServiceABC, Depends(get_link_service)],
):
    try:
        if raw_link.host not in settings.hosts_allowed_to_shorten:
            raise AppException(f'{raw_link.host} is not whitelisted in the url-shortener service')
        short_link = await link_service.shorten(raw_link)
    except AppException as e:
        return JSONResponse(
            status_code=http.client.BAD_REQUEST,
            content={"message": str(e)},
        )
    else:
        return {'result': short_link}
