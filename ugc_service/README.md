# ugc_service

Сервис для сбора пользовательского контента (User Generated Content) и событий пользователей.

## Swagger-документация

[api/v1/ugc/openapi](http://127.0.0.1/api/v1/ugc/openapi)

## Эндпоинты

### События (Events)

#### Отправка события
- **POST** `/api/v1/event`
- **Описание**: Отправка события пользователя в систему
- **Аутентификация**: Только внутренняя
- **Rate Limiting**: 10 запросов в секунду
- **Тело запроса**:
```json
{
  "timestamp": 1672531200,
  "event": "page_view",
  "user_id": "4e7e4fb5-7dac-4816-95f8-715cf4c220ab"
}
```
- **Ответ**:
```json
{
  "message": "Event sent to broker",
  "event": {
    "timestamp": 1672531200,
    "event": "page_view",
    "user_id": "4e7e4fb5-7dac-4816-95f8-715cf4c220ab"
  }
}
```

## Аутентификация

Сервис поддерживает только внутреннюю аутентификацию для межсервисного взаимодействия:
- **Внутренняя аутентификация** - через заголовок `X-Internal-Auth`

## Rate Limiting

Сервис использует Redis для ограничения частоты запросов:
- **Лимит**: 10 запросов в секунду на IP-адрес

## Примеры событий

### Просмотр страницы
```json
{
  "timestamp": 1672531200,
  "event": "page_view",
  "user_id": "4e7e4fb5-7dac-4816-95f8-715cf4c220ab"
}
```

### Клик по кнопке
```json
{
  "timestamp": 1672531260,
  "event": "button_click",
  "user_id": "4e7e4fb5-7dac-4816-95f8-715cf4c220ab"
}
```

### Покупка
```json
{
  "timestamp": 1672531320,
  "event": "purchase",
  "user_id": "4e7e4fb5-7dac-4816-95f8-715cf4c220ab"
}
```

### Регистрация
```json
{
  "timestamp": 1672531380,
  "event": "registration",
  "user_id": "4e7e4fb5-7dac-4816-95f8-715cf4c220ab"
}
```

## Интеграция с Kafka

Сервис отправляет события в Kafka для дальнейшей обработки:
- **Топик**: `event` (настраивается через `KAFKA_TOPIC_NAME`)
- **Серверы**: Настраиваются через `KAFKA_BOOTSTRAP_SERVER`
- **Формат**: JSON с полями `timestamp`, `event`, `user_id`

## Мониторинг

Сервис интегрирован с Sentry для мониторинга ошибок:
- **DSN**: Настраивается через `SENTRY_DSN_UGC`
- **Логирование**: Структурированные логи с уровнем INFO и выше
