# Используем официальный образ Python
FROM python:3.12.1

# Устанавливаем рабочую директорию
WORKDIR /app/src

# Копируем зависимости
COPY requirements.txt /app

# Устанавливаем зависимости
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && groupadd -r celery \
    && useradd -r -g celery celery \
    && chown -R celery:celery /app

# Копируем исходный код приложения
COPY . /app

ENV PYTHONUNBUFFERED=1

# CMD ["celery", "-A", "main_celery", "worker", "--loglevel=INFO"]
CMD ["python", "main.py"]