#!/bin/sh

# Функция ожидания БД
wait_for_db() {
    echo "Ожидание базы данных..."
    host="$1"
    port="$2"
    while ! nc -z "$host" "$port"; do
        sleep 1
    done
    echo "База данных доступна!"
}

# Определение типа окружения
if [ "$APP_ENV" = "TEST" ]; then
    # Тестовое окружение
    DB_HOST="$BILLING_DB_TEST_HOST"
    DB_PORT="$BILLING_DB_TEST_PORT"
    SERVICE_PORT="$BILLING_SERVICE_TEST_PORT"
    ENV_TYPE="TEST"
else
    # Рабочее окружение
    DB_HOST="$BILLING_DB_HOST"
    DB_PORT="$BILLING_DB_PORT"
    SERVICE_PORT="$BILLING_SERVICE_PORT"
    ENV_TYPE="PRODUCTION"
fi

# Ожидаем готовность БД
wait_for_db "$DB_HOST" "$DB_PORT"

# Применяем миграции
alembic upgrade head || echo "Миграции не применены"

# Запускаем приложение
cd /app/src
exec uvicorn main:app --host 0.0.0.0 --port "$SERVICE_PORT" --reload