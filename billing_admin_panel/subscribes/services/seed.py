import uuid
from datetime import timedelta
from django.utils import timezone
from subscribes.models import Subscription, UserSubscription, Transaction

def seed_data():
    # Создаем подписки в схеме content
    sub1 = Subscription.objects.create(
        id=uuid.uuid4(),
        role_id=uuid.uuid4(),
        name="Basic Plan",
        description="Basic access",
        amount=9.99,
        currency="USD",
        period=30,
        actual=True,
        created=timezone.now(),
        modified=timezone.now(),
    )

    sub2 = Subscription.objects.create(
        id=uuid.uuid4(),
        role_id=uuid.uuid4(),
        name="Pro Plan",
        description="Extended access",
        amount=19.99,
        currency="USD",
        period=30,
        actual=True,
        created=timezone.now(),
        modified=timezone.now(),
    )

    # Создаем user_subscription в схеме content
    user_id = uuid.uuid4()
    user_sub = UserSubscription.objects.create(
        id=uuid.uuid4(),
        user_id=user_id,
        subscription_id=sub1.id,  # Используем subscription_id вместо subscription
        auto_pay_id="autopay_123",
        expires=timezone.now() + timedelta(days=30),
        created=timezone.now(),
        modified=timezone.now(),
    )

    # Создаем транзакции в схеме content
    Transaction.objects.create(
        id=uuid.uuid4(),
        user_id=user_id,
        payment_id=str(uuid.uuid4()),  # Гарантируем UUID v4 для payment_id
        user_subscription_id=user_sub.id,  # Используем user_subscription_id
        amount=9.99,
        currency="USD",
        status_code=200,
        transaction_type=1,
        starts=timezone.now(),
        ends=timezone.now() + timedelta(days=30),
        created=timezone.now(),
        modified=timezone.now(),
    )

    print("✅ Seeded data successfully with UUID v4 in content schema.")