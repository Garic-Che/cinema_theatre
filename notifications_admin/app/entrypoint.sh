#!/bin/bash
set -e

echo "Notifications_app entrypoint"

wait_for_postgres() {
    echo "Waiting for PostgreSQL..."
    while ! nc -z $NOTIFICATION_DB_HOST $NOTIFICATION_DB_PORT; do
        sleep 0.1
    done
    echo "PostgreSQL started"
}

# wait_for_redis() {
#     echo "Waiting for Redis..."
#     while ! nc -z $REDIS_HOST $REDIS_PORT; do
#         sleep 0.1
#     done
#     echo "Redis started"
# }

run_migrations() {
    echo "Checking if migrations are needed..."
    if python manage.py showmigrations --plan | grep -q '\[ \]'; then
        echo "Applying database migrations..."
        python manage.py migrate --no-input
        echo "Creating migrations users..."
        python manage.py makemigrations users --no-input
        echo "Creating migrations notifications_app..."
        python manage.py makemigrations notifications_app --no-input
    else
        echo "No migrations needed."
    fi
}

wait_for_postgres
# wait_for_redis

# run_migrations

python manage.py collectstatic --no-input --clear

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    export DJANGO_SUPERUSER_USERNAME=$DJANGO_SUPERUSER_USERNAME
    export DJANGO_SUPERUSER_EMAIL=$DJANGO_SUPERUSER_EMAIL
    export DJANGO_SUPERUSER_PASSWORD=$DJANGO_SUPERUSER_PASSWORD
    python manage.py createsuperuser --noinput || true
fi

exec gunicorn notifications_project.wsgi:application \
    --bind $NOTIFICATION_DJANGO_ADMIN_HOST:$NOTIFICATION_DJANGO_ADMIN_PORT \
    --workers 4 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -