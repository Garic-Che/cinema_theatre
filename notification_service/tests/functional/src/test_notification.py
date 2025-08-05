from http import HTTPStatus

import pytest

from tests.functional.settings import test_settings
from tests.functional.testdata.notification_data import (
    generate_notification_data,
)


# запись уведомления
@pytest.mark.parametrize(
    "notification_data, expected_answer",
    [
        (generate_notification_data(), HTTPStatus.OK),
        (generate_notification_data(to_id=""), HTTPStatus.BAD_REQUEST),
        (generate_notification_data(send_by=""), HTTPStatus.BAD_REQUEST),
        (
            generate_notification_data(content_key="test", content_data=""),
            HTTPStatus.OK,
        ),
        (
            generate_notification_data(content_key="", content_data=""),
            HTTPStatus.NOT_FOUND,
        ),
    ],
)
@pytest.mark.asyncio
async def test_notification(
    make_post_request,
    rabbit_get_data,
    notification_data,
    expected_answer,
):
    response = await make_post_request(
        path="/api/v1/notification",
        body=notification_data,
    )

    message = rabbit_get_data(test_settings)

    assert response["status"] == expected_answer
    if expected_answer != HTTPStatus.OK:
        return
    # assert message
