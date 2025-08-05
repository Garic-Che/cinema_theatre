# Используем официальный образ Python
FROM python:3.10.2-buster
ENV PYTHONPATH="/app/src"

# Установка зависимостей для netcat
RUN apt-get update && apt-get install -y netcat

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# Копируем исходный код приложения
COPY . .

RUN chmod +x /app/entrypoint.sh

# Команда для запуска приложения
ENTRYPOINT ["/app/entrypoint.sh"]