FROM python:3.12.1

WORKDIR /app

ENV PYTHONBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . .

CMD ["python3", "main.py"]