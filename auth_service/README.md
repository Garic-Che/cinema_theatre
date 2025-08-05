# auth_service

Сервис авторизации для управления пользователями, ролями и аутентификацией.

## Swagger-документация

[api/v1/auth/openapi](http://127.0.0.1/api/v1/auth/openapi)

[Схема сервиса auth_service](https://viewer.diagrams.net/?tags=%7B%7D&lightbox=1&highlight=0000ff&edit=_blank&layers=1&nav=1&title=%D0%A1%D0%B5%D1%80%D0%B2%D0%B8%D1%81%20%D0%B0%D0%B2%D1%82%D0%BE%D1%80%D0%B8%D0%B7%D0%B0%D1%86%D0%B8%D0%B8.drawio&dark=auto#Uhttps%3A%2F%2Fdrive.google.com%2Fuc%3Fid%3D16yqih5LCF9obOCW-455quPI5MmGAUVHl%26export%3Ddownload#%7B%22pageId%22%3A%22ytn_OKpRD8WPGU0JEZmp%22%7D)

## Эндпоинты

### Пользователи (User)

#### Регистрация пользователя
- **POST** `/api/v1/user/register`
- **Описание**: Регистрация нового пользователя
- **Аутентификация**: Привилегия "user/register"
- **Тело запроса**:
```json
{
  "login": "user123",
  "password": "secure_password",
  "email": "user@example.com"
}
```
- **Ответ**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000"
}
```

#### Вход пользователя
- **POST** `/api/v1/user/login`
- **Описание**: Аутентификация пользователя
- **Аутентификация**: Привилегия "user/login"
- **Тело запроса**:
```json
{
  "login": "user123",
  "password": "secure_password"
}
```
- **Ответ**: Устанавливает cookies с access_token и refresh_token
```json
{
  "detail": "User successfully logged in"
}
```

#### Профиль пользователя
- **GET** `/api/v1/user/` или `/api/v1/user/profile`
- **Описание**: Получение профиля текущего пользователя
- **Аутентификация**: JWT токен + привилегия "user/profile"
- **Ответ**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "login": "user123",
  "email": "user@example.com",
  "created": "2024-01-01T00:00:00"
}
```

#### Изменение логина
- **PUT** `/api/v1/user/login`
- **Описание**: Изменение логина пользователя
- **Аутентификация**: JWT токен + привилегия "user/login/change"
- **Тело запроса**:
```json
{
  "new_login": "new_user123"
}
```
- **Ответ**:
```json
{
  "detail": "Login successfully changed"
}
```

#### Изменение пароля
- **PUT** `/api/v1/user/password`
- **Описание**: Изменение пароля пользователя
- **Аутентификация**: JWT токен + привилегия "user/password/change"
- **Тело запроса**:
```json
{
  "old_password": "old_password",
  "new_password": "new_secure_password"
}
```
- **Ответ**:
```json
{
  "detail": "Password successfully changed"
}
```

#### Обновление токенов
- **POST** `/api/v1/user/refresh`
- **Описание**: Обновление access токена
- **Аутентификация**: Refresh токен
- **Тело запроса**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
- **Ответ**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Выход пользователя
- **POST** `/api/v1/user/logout`
- **Описание**: Выход пользователя из системы
- **Аутентификация**: JWT токен + привилегия "user/logout"
- **Ответ**:
```json
{
  "detail": "User successfully logged out"
}
```

### Аутентификация через соцсеть (Provider Auth)

#### Вход через провайдер
- **GET** `/api/v1/user/login/{provider}`
- **Описание**: Перенаправление на страницу авторизации провайдера
- **Аутентификация**: Привилегия "user/login/provider"
- **Параметры пути**: `provider` (string) - название провайдера
- **Ответ**: Перенаправление на страницу авторизации

#### Callback от провайдера
- **GET** `/api/v1/user/login/{provider}/callback`
- **Описание**: Обработка ответа от провайдера аутентификации
- **Аутентификация**: Привилегия "user/login/provider/callback"
- **Параметры пути**: `provider` (string) - название провайдера
- **Ответ**: Устанавливает cookies с токенами
```json
{
  "detail": "Successfully authenticated with provider"
}
```

### Роли (Role)

#### Создание роли
- **POST** `/api/v1/role/create`
- **Описание**: Создание новой роли
- **Аутентификация**: Привилегия "role/create"
- **Тело запроса**:
```json
{
  "name": "admin",
  "privilege_ids": [...]
}
```
- **Ответ**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174001",
  "name": "admin",
  "created": "2024-01-01T00:00:00",
  "modified": "2024-01-01T00:00:00",
  "privilege_ids": [...]
}
```

#### Удаление роли
- **DELETE** `/api/v1/role/delete`
- **Описание**: Удаление роли
- **Аутентификация**: Привилегия "role/delete"
- **Тело запроса**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174001"
}
```
- **Ответ**:
```json
{
  "detail": "Role successfully deleted"
}
```

#### Изменение роли
- **PUT** `/api/v1/role/change`
- **Описание**: Изменение существующей роли
- **Аутентификация**: Привилегия "role/change"
- **Тело запроса**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174001",
  "name": "admin",
  "privilege_ids": [...]
}
```
- **Ответ**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174001",
  "name": "admin",
  "privilege_ids": [...]
}
```

#### Список всех ролей
- **GET** `/api/v1/role/`
- **Описание**: Получение списка всех ролей
- **Аутентификация**: Привилегия "role/" или внутренняя
- **Ответ**:
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "admin",
    "privilege_ids": [...]
  }
]
```

#### Назначение роли пользователю
- **POST** `/api/v1/role/assign/{user_id}`
- **Описание**: Назначение роли пользователю
- **Аутентификация**: Привилегия "role/assign" или внутренняя
- **Параметры пути**: `user_id` (string)
- **Тело запроса**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174001"
}
```
- **Ответ**:
```json
{
  "detail": "Role successfully assigned to user"
}
```

#### Отзыв роли у пользователя
- **POST** `/api/v1/role/revoke/{user_id}`
- **Описание**: Отзыв роли у пользователя
- **Аутентификация**: Привилегия "role/revoke" или внутренняя
- **Параметры пути**: `user_id` (string)
- **Тело запроса**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174001"
}
```
- **Ответ**:
```json
{
  "detail": "Role successfully revoked from user"
}
```

#### Роли пользователя
- **GET** `/api/v1/role/{user_id}`
- **Описание**: Получение списка ролей пользователя
- **Аутентификация**: Привилегия "role/user"
- **Параметры пути**: `user_id` (string)
- **Ответ**:
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "admin",
    "privilege_ids": [...]
  }
]
```

### Внутренние операции (Internal Users)

#### Пользователи по группе рассылки
- **GET** `/api/v1/users/group/{group_name}`
- **Описание**: Получение пользователей по группе рассылки
- **Аутентификация**: Только внутренняя
- **Параметры пути**: `group_name` (string)
- **Ответ**:
```json
{
  "ids": ["123e4567-e89b-12d3-a456-426614174000", "123e4567-e89b-12d3-a456-426614174001"]
}
```

#### Пользователи по ролям
- **GET** `/api/v1/users/roles/{roles}`
- **Описание**: Получение пользователей по ролям
- **Аутентификация**: Только внутренняя
- **Параметры пути**: `roles` (string) - список ролей через запятую
- **Ответ**:
```json
{
  "ids": ["123e4567-e89b-12d3-a456-426614174000", "123e4567-e89b-12d3-a456-426614174001"]
}
```

#### Пользователь по ID
- **GET** `/api/v1/users/{user_id}`
- **Описание**: Получение пользователя по ID
- **Аутентификация**: Только внутренняя
- **Параметры пути**: `user_id` (string)
- **Ответ**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "login": "user123",
  "email": "user@example.com",
  "created": "2024-01-01T00:00:00"
}
```

## Аутентификация

Сервис поддерживает несколько типов аутентификации:
- **JWT токены** - для авторизованных пользователей (access_token и refresh_token)
- **Привилегии** - для проверки прав доступа к эндпоинтам
- **Внутренняя аутентификация** - для межсервисного взаимодействия через заголовок `X-Internal-Auth`

## Поддерживаемые провайдеры OAuth

Сервис поддерживает вход через внешние провайдеры аутентификации (google, vk, yandex).
