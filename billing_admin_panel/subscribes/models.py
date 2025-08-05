# billing/models.py

import uuid
from django.db import models


class Subscription(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role_id     = models.UUIDField()
    name        = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    amount      = models.FloatField()
    currency    = models.CharField(max_length=255)
    period      = models.PositiveIntegerField()
    actual      = models.BooleanField(default=True)
    created     = models.DateTimeField(auto_now_add=True)
    modified    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = '"content"."subscription"'
        managed = False

    def __str__(self):
        return f"{self.name} — {self.amount} {self.currency}"


class UserSubscription(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id      = models.UUIDField()
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        db_column='subscription_id',
        related_name='user_subscriptions'
    )
    auto_pay_id   = models.CharField(max_length=255)
    expires       = models.DateTimeField()
    created       = models.DateTimeField(auto_now_add=True)
    modified      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = '"content"."user_subscription"'
        managed = False

    def __str__(self):
        return f"{self.user_id} — {self.subscription.name}"


class Transaction(models.Model):
    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id             = models.UUIDField()
    payment_id          = models.CharField(max_length=255)
    user_subscription   = models.ForeignKey(
        UserSubscription,
        on_delete=models.SET_NULL,
        null=True,
        db_column='user_subscription_id',
        related_name='transactions'
    )
    amount              = models.FloatField()
    currency            = models.CharField(max_length=255)
    status_code         = models.IntegerField()
    transaction_type    = models.IntegerField()
    starts              = models.DateTimeField(blank=True, null=True)
    ends                = models.DateTimeField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = '"content"."transaction"'
        managed = False

    def __str__(self):
        return f"{self.payment_id} ({self.amount} {self.currency})"
