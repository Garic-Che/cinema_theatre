FROM python:3.12.10

WORKDIR /tests

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /tests/requirements.txt

COPY . .

ENTRYPOINT ["ptw"]