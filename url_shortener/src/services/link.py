from abc import ABC, abstractmethod
from datetime import datetime, timezone
from uuid import UUID

from pydantic import HttpUrl

from repository.link import LinkRepositoryABC, get_link_db_repository
from exceptions.link import AppException


class LinkServiceABC(ABC):
    @abstractmethod
    async def shorten(self, raw_link: HttpUrl) -> str:
        pass

    @abstractmethod
    async def resolve(self, short_link_id: UUID) -> str:
        pass


class LinkService(LinkServiceABC):
    def __init__(self, repository: LinkRepositoryABC):
        self.repository = repository

    async def shorten(self, short_link_id: UUID) -> str:
        shortened_link = await self.repository.create_link_mapping(short_link_id)
        if not shortened_link:
            return None
        return shortened_link

    async def resolve(self, short_link: HttpUrl) -> str:
        url_mapping = await self.repository.get_link_mapping(short_link)
        if not url_mapping:
            raise AppException(message="The link does not exist")
        if url_mapping.expiry_date <= datetime.now(timezone.utc):
            raise AppException(message="The link got stale")
        return url_mapping.raw_link
        

async def get_link_service() -> LinkServiceABC:
    return LinkService(await get_link_db_repository())
