import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('BILLING_DB_NAME'),
        'USER': os.getenv('BILLING_DB_USER'),
        'PASSWORD': os.getenv('BILLING_DB_PASSWORD'),
        'HOST': os.getenv('BILLING_DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('BILLING_DB_PORT', 5432),
        'OPTIONS': {
            'options': os.getenv('BILLING_DB_OPTIONS'),
        },
    }
}
