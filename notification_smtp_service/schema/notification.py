from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationData(BaseModel):
    notification_id: str
    to_id: str
    model_config = ConfigDict(extra="forbid")
