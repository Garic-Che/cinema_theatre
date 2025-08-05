from django.apps import AppConfig
from django.conf import settings
from django.db.utils import ProgrammingError, OperationalError

class SubscribesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "subscribes"

    def ready(self):
        # Только если DEBUG = True
        if settings.DEBUG:
            try:
                from .services.seed import seed_data
                from subscribes.models import Subscription

                # Проверка: если в таблице нет ни одной подписки — создаем данные
                if not Subscription.objects.exists():
                    seed_data()
            except (ProgrammingError, OperationalError):
                # Таблиц еще нет (например, после миграций) — пропускаем
                pass