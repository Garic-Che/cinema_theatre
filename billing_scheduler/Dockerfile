# Используем официальный образ Python
FROM python:3.10-slim

# Устанавливаем cron
RUN apt-get update && \
    apt-get install -y cron

# Создаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# Копируем исходный код
COPY . .

ENV PYTHONUNBUFFERED=1

# Команда запуска
CMD ["python", "src/main.py"]