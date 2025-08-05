from datetime import datetime
import uuid

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    UUID,
)

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
