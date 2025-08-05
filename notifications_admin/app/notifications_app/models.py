import uuid
from django.db import models
from django.utils import timezone


class UuidCreatedMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(default=timezone.now)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TemplateDB(UuidCreatedMixin):
    template = models.TextField(null=False)
    template_type = models.CharField(max_length=255, default="")

    class Meta:
        db_table = 'content"."template'
        verbose_name = "Шаблон"
        verbose_name_plural = "Шаблоны"

    def __str__(self):
        return f"{self.template_type} ({self.id})"


class ContentDB(UuidCreatedMixin):
    key = models.CharField(max_length=255, null=False)
    value = models.TextField(null=False)

    class Meta:
        db_table = 'content"."content'
        verbose_name = "Контент"
        verbose_name_plural = "Контент"

    def __str__(self):
        return self.key


class NotificationDB(UuidCreatedMixin):
    SEND_BY_CHOICES = [
        ("email", "Email"),
        ("websocket", "WebSocket"),
    ]

    template = models.ForeignKey(
        TemplateDB, on_delete=models.CASCADE, db_column="template_id"
    )
    content_id = models.CharField(max_length=255, null=True, blank=True)
    sent = models.BooleanField(default=False)
    send_by = models.CharField(
        max_length=10,
        choices=SEND_BY_CHOICES,
        default="email",
        verbose_name="Способ отправки",
    )
    to_id = models.CharField(
        max_length=255,
        verbose_name="Получатель",
        help_text="ID пользователя или 'all' для всех",
    )

    class Meta:
        db_table = 'content"."notification'
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"

    def __str__(self):
        return f"Уведомление {self.id} ({self.get_send_by_display()})"


class ScheduleEventDB(UuidCreatedMixin):
    SEND_BY_CHOICES = [
        ("email", "Email"),
        ("websocket", "WebSocket"),
    ]

    template = models.ForeignKey(
        TemplateDB, on_delete=models.CASCADE, db_column="template_id"
    )
    period = models.IntegerField(null=False, verbose_name="Период (сек)")
    next_send = models.DateTimeField(null=False, verbose_name="Следующая отправка")
    once = models.BooleanField(default=False, verbose_name="Одноразовая")
    receiver_group_name = models.CharField(
        max_length=255, default="all", verbose_name="Группа получателей"
    )
    send_by = models.CharField(
        max_length=10,
        choices=SEND_BY_CHOICES,
        default="email",
        verbose_name="Способ отправки",
    )

    class Meta:
        db_table = 'content"."schedule_notification'
        verbose_name = "Запланированная рассылка"
        verbose_name_plural = "Запланированные рассылки"

    def __str__(self):
        return f"Рассылка {self.id} ({self.get_send_by_display()})"
