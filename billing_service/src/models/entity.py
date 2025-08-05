import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Text,
    ForeignKey,
    MetaData,
    Uuid,
    Float,
    Integer,
    Boolean,
    VARCHAR,
)
from sqlalchemy.orm import relationship

from db.base import Base

# Указываем схему для всех таблиц
SCHEMA = "content"


class UuidCreatedMixin:
    __table_args__ = {"schema": SCHEMA}

    id = Column(Uuid, primary_key=True, default=lambda: str(uuid.uuid4()))
    created = Column(DateTime, default=datetime.utcnow)
    modified = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class Transaction(UuidCreatedMixin, Base):
    __tablename__ = "transaction"

    user_id = Column(Uuid, nullable=False)
    payment_id = Column(VARCHAR(255), nullable=False)
    user_subscription_id = Column(
        Uuid, ForeignKey(f"{SCHEMA}.user_subscription.id"), nullable=True
    )
    amount = Column(Float, nullable=False)
    currency = Column(VARCHAR(255), nullable=False)
    status_code = Column(Integer, nullable=False)
    transaction_type = Column(Integer, nullable=False)
    user_subscription = relationship(
        "UserSubscription", back_populates="transactions"
    )
    starts = Column(DateTime, default=datetime.utcnow, nullable=True)
    ends = Column(DateTime, default=datetime.utcnow, nullable=True)

    def __repr__(self) -> str:
        return f"<Transaction {self.id}>"


class Subscription(UuidCreatedMixin, Base):
    __tablename__ = "subscription"

    role_id = Column(Uuid, nullable=False)
    name = Column(VARCHAR(255), nullable=False)
    description = Column(Text, nullable=True)
    amount = Column(Float, nullable=False)
    actual = Column(Boolean, nullable=False, default=True)
    currency = Column(VARCHAR(255), nullable=False)
    period = Column(Integer, nullable=False)
    user_subscriptions = relationship(
        "UserSubscription", back_populates="subscription"
    )

    def __repr__(self) -> str:
        return f"<Subscription {self.id}>"


class UserSubscription(UuidCreatedMixin, Base):
    __tablename__ = "user_subscription"

    user_id = Column(Uuid, nullable=False)
    auto_pay_id = Column(VARCHAR(255), nullable=True)
    subscription_id = Column(
        Uuid, ForeignKey(f"{SCHEMA}.subscription.id")
    )
    subscription = relationship(
        "Subscription", back_populates="user_subscriptions"
    )
    expires = Column(DateTime, nullable=False)
    transactions = relationship(
        "Transaction", back_populates="user_subscription"
    )

    def __repr__(self) -> str:
        return f"<UserSubscription {self.id}>"
