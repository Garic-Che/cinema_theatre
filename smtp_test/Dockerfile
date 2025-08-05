FROM python:3.12.1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . .

ENTRYPOINT ["python3", "-m", "aiosmtpd", "-n", "-l", "0.0.0.0:8025", "-c", "aiosmtpd.handlers.Debugging"]