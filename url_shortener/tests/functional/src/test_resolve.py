import http
import http.client

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url_mapping_id, expected_status, expected_url",
    [
        ("f47ac10b-58cc-4372-a567-0e02b2c3d479", http.client.FOUND, "http://auth-service:8000/test1"),
        ("9a42b832-1f47-4c95-841e-2ea6db01ef89", http.client.NOT_FOUND, None), # expired link
        ("9a42b832-1f47-4c95-841e-2ea6db01ef81", http.client.NOT_FOUND, None), # non-existent but valid uuid
        ("invalid-uuid", http.client.UNPROCESSABLE_ENTITY, None)
    ]
)
async def test_resolve(url_mapping_id, expected_url, expected_status, fetch): 
    # Act
    response = await fetch(f"/{url_mapping_id}")
    
    # Assert
    assert response.status == expected_status
    if response.status < 400:
        assert response.headers["Location"] == expected_url
