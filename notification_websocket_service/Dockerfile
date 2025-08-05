# Используем официальный образ Python slim для уменьшения размера контейнера
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения
COPY . .
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]