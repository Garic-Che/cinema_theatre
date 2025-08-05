import asyncio

from django.contrib import admin, messages
from django.conf import settings as billing_settings

from subscribes.models import Subscription, Transaction, UserSubscription
from subscribes.services.billing_engine import BillingServiceEngine

engine = BillingServiceEngine(billing_settings)

# === ACTIONS ===

@admin.action(description="Совершить оплату")
def make_payment_action(modeladmin, request, queryset):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for obj in queryset:
        user_id = str(obj.user_id)
        subscription_id = str(obj.subscription.id) if obj.subscription else None

        if not subscription_id:
            messages.warning(request, f"Нет подписки у UserSubscription {obj.id}")
            continue

        result = loop.run_until_complete(
            engine.make_payment(user_id=user_id, subscription_id=subscription_id)
        )
        if result:
            messages.success(request, f"Оплата прошла: {result}")
        else:
            messages.error(request, f"Ошибка при оплате для user_id={user_id}")

@admin.action(description="Сделать возврат")
def refund_action(modeladmin, request, queryset):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for obj in queryset:
        result = loop.run_until_complete(
            engine.refund_transaction(
                user_id=str(obj.user_id),
                payment_id=str(obj.payment_id),
                amount=obj.amount,
                currency=obj.currency or "RUB"
            )
        )
        if result:
            messages.success(request, f"Возврат сделан: {result}")
        else:
            messages.error(request, f"Ошибка при возврате платежа {obj.payment_id}")


# === INLINES ===

class TransactionInline(admin.TabularInline):
    model = Transaction
    fields = ('payment_id', 'user_id', 'amount', 'currency', 'status_code', 'transaction_type', 'created')
    readonly_fields = ('created',)
    extra = 0
    show_change_link = True


class UserSubscriptionInline(admin.TabularInline):
    model = UserSubscription
    fields = ('user_id', 'auto_pay_id', 'expires', 'created')
    readonly_fields = ('created',)
    extra = 0
    show_change_link = True


# === ADMINS ===

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'currency', 'period', 'actual', 'created', 'modified')
    list_filter = ('currency', 'actual')
    search_fields = ('name', 'description')
    readonly_fields = ('created', 'modified')
    inlines = [UserSubscriptionInline]


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id','user_id', 'subscription_id','subscription', 'expires', 'auto_pay_id', 'created')
    list_filter = ('subscription',)
    search_fields = ('auto_pay_id',)
    readonly_fields = ('created', 'modified')
    inlines = [TransactionInline]
    actions = [make_payment_action]  # оплата возможна отсюда


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'user_id', 'user_subscription_id','user_subscription', 'amount', 'currency', 'status_code', 'transaction_type', 'created')
    list_filter = ('status_code', 'transaction_type', 'currency', 'created')
    search_fields = ('payment_id',)
    readonly_fields = ('created', 'modified')
    actions = [refund_action]  # возврат отсюда
