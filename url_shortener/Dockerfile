FROM python:3.12.1

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

COPY . .

ENTRYPOINT ["python3", "src/main.py"]