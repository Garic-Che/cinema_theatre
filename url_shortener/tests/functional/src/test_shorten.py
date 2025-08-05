import http
import pytest
from uuid import uuid4

from ..settings import settings


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url_to_shorten, expected_status",
    [
        ("http://auth_service:8000/test1", http.client.OK),
        ("http://not_whitelisted:8000/test1", http.client.BAD_REQUEST),
        ("invalid_url", http.client.UNPROCESSABLE_ENTITY),
    ]
)
async def test_shorten(url_to_shorten, expected_status, post): 
    # Act
    status, response = await post("/", {"raw_link": url_to_shorten})

    # Assert
    assert status == expected_status
    if status < 400:
        short_url = response['result']
        assert short_url.startswith(settings.base_api_url)
        assert len(short_url) == len(f"{settings.base_api_url}/{uuid4()}")
