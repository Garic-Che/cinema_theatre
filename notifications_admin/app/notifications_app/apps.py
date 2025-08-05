from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class NotificationsAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications_app"
    verbose_name = _("notifications_app")
