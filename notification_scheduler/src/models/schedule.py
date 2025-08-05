from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.sql import func

from core.database import Base


class ScheduleNotification(Base):
    """Model for the schedule_notification table."""
    
    __tablename__ = "schedule_notification"
    __table_args__ = {"schema": "content"}
    
    id = Column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    template_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("content.template.id", ondelete="CASCADE"),
        nullable=False
    )
    period = Column(BigInteger, nullable=False)  # Period in seconds
    next_send = Column(DateTime(timezone=True), nullable=False)
    once = Column(Boolean, default=False, nullable=False)
    receiver_group_name = Column(String, default="all", nullable=False)
    created = Column(
        DateTime(timezone=True),
        default=func.current_timestamp(),
        nullable=False
    )
    modified = Column(
        DateTime(timezone=True),
        default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )
    
    def __repr__(self) -> str:
        return (
            f"<ScheduleNotification(id={self.id}, "
            f"template_id={self.template_id}, "
            f"next_send={self.next_send}, "
            f"receiver_group_name={self.receiver_group_name})>"
        )


class Template(Base):
    """Model for the template table."""
    
    __tablename__ = "template"
    __table_args__ = {"schema": "content"}
    
    id = Column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    template = Column(String, nullable=False)
    template_type = Column(String, default="", nullable=False)
    created = Column(
        DateTime(timezone=True),
        default=func.current_timestamp(),
        nullable=False
    )
    modified = Column(
        DateTime(timezone=True),
        default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )
    
    def __repr__(self) -> str:
        return (
            f"<Template(id={self.id}, "
            f"template_type={self.template_type})>"
        )