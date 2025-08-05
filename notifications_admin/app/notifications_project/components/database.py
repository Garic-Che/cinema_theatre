import os

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("NOTIFICATION_DB_NAME"),
        "USER": os.environ.get("NOTIFICATION_DB_USER"),
        "PASSWORD": os.environ.get("NOTIFICATION_DB_PASSWORD"),
        "HOST": os.environ.get("NOTIFICATION_DB_HOST"),
        "PORT": os.environ.get("NOTIFICATION_DB_PORT", 5432),
        'OPTIONS': {
            'options': os.getenv('SQL_OPTIONS'),
        },
    }
}
