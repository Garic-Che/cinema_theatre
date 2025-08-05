from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from uuid import UUID

from pydantic import HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.link import UrlMapping
from core.database import get_db_session
from core.config import settings


class LinkRepositoryABC(ABC):
    @abstractmethod
    async def create_link_mapping(self, raw_link_id: HttpUrl) -> str:
        pass

    @abstractmethod
    async def get_link_mapping(self, short_link_id: UUID) -> UrlMapping:
        pass


class LinkRepository(LinkRepositoryABC):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_link_mapping(self, raw_link: HttpUrl) -> str:
        url_mapping = UrlMapping(
            raw_link=str(raw_link),
            expiry_date=(datetime.now(timezone.utc) + timedelta(days=settings.LINK_EXPIRY_PERIOD_IN_DAYS)),
        )
        self.session.add(url_mapping)
        await self.session.flush()
        await self.session.commit()
        return f'{settings.url_shortener_base_url}/{url_mapping.id}'

    async def get_link_mapping(self, short_link_id: UUID) -> UrlMapping:
        stmt = select(UrlMapping).where(UrlMapping.id == short_link_id)
        result = await self.session.scalars(stmt)
        return result.first()


async def get_link_db_repository() -> LinkRepositoryABC:
    return LinkRepository(await anext(get_db_session()))
