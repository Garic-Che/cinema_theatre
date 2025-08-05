import pytest
import aiohttp
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from .settings import settings 


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    engine = create_async_engine(settings.postgres_dsn, echo=True)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def async_session_factory(async_engine):
    async_session_maker = async_sessionmaker(
        async_engine, expire_on_commit=False, class_=AsyncSession
    )
    yield async_session_maker


@pytest.fixture(scope="function")
async def async_session_factory(async_sessionmaker):
    async with async_sessionmaker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def aiohttp_client():
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture
def fetch(aiohttp_client):
    async def _fetch(url_path):
        headers = {"X-Internal-Auth": f"{settings.shortener_service_secret}"}
        async with aiohttp_client.get(settings.base_api_url + url_path, headers=headers, allow_redirects=False) as response:
            return response
    return _fetch


@pytest.fixture
def post(aiohttp_client):
    async def _post(url_path, body: dict[str, str]):
        headers = {"X-Internal-Auth": f"{settings.shortener_service_secret}"}
        async with aiohttp_client.post(settings.base_api_url + url_path, headers=headers, json=body) as response:
            return (response.status, await response.json())
    return _post
