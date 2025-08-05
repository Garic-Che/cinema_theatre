#!/bin/sh

echo "Waiting for postgres..."
while ! nc -z $BILLING_DB_HOST $BILLING_DB_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

python manage.py migrate --fake --fake subscribes 0001
python manage.py migrate --no-input
python manage.py createsuperuser --login admin --noinput || true

gunicorn config.wsgi:application --bind 0.0.0.0:$BILLING_ADMIN_PORT --reload

exec "$@"