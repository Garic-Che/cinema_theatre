import uuid


def generate_notification_data(
    to_id: str = str(uuid.uuid4()),
    send_by: str = "email",
    content_key: str = "test/key",
    content_data: str = "test_data",
):
    notification_data = {
        "to_id": to_id,
        "send_by": send_by,
        "content_key": content_key,
        "content_data": content_data,
    }
    return notification_data
