from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.sql import func

from core.database import Base


class UrlMapping(Base):
    """Model for the url_mapping table."""
    
    __tablename__ = "url_mapping"
    __table_args__ = {"schema": "content"}
    
    id = Column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    raw_link = Column(String, nullable=False)
    expiry_date = Column(
        DateTime(timezone=True),
        nullable=False
    )
    created_at = Column(
        DateTime(timezone=True),
        default=func.current_timestamp(),
        nullable=False
    )
