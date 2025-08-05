from pydantic import BaseModel, Field
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    Integer,
    ForeignKey,
    UUID,
)
import uuid

from db.postgres import Base

# Указываем схему для всех таблиц
SCHEMA = "content"


class UuidCreatedMixin:
    __table_args__ = {"schema": SCHEMA}

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Notification(BaseModel):
    to_id: str = Field(..., min_length=1)  # id пользователя, которому отправляется уведомление или имя рассылки ("all")
    send_by: str = Field(..., min_length=1)  # способ отправки уведомления ("email", "websocket")
    content_key: str = Field(..., min_length=1)  # ключ контента / тип шаблона
    content_data: str = ""  # данные контента


class NotificationId(BaseModel):
    notification_id: str = ""


class TemplateDB(UuidCreatedMixin, Base):
    __tablename__ = "template"

    template = Column(String, nullable=False)
    template_type = Column(String, default="")


class ContentDB(UuidCreatedMixin, Base):
    __tablename__ = "content"

    key = Column(String, nullable=False)
    value = Column(String, nullable=False)


class NotificationDB(UuidCreatedMixin, Base):
    __tablename__ = "notification"

    template_id = Column(
        UUID,
        ForeignKey(f"{SCHEMA}.template.id", ondelete="CASCADE"),
        nullable=False,
    )
    content_id = Column(String, nullable=True)
    sent = Column(Boolean, default=False)


class ScheduleEventDB(UuidCreatedMixin, Base):
    __tablename__ = "schedule_notification"

    template_id = Column(
        UUID,
        ForeignKey(f"{SCHEMA}.template.id", ondelete="CASCADE"),
        nullable=False,
    )
    period = Column(Integer, nullable=False)
    next_send = Column(DateTime, nullable=False)
    once = Column(Boolean, default=False)
    receiver_group_name = Column(String, default="all")
