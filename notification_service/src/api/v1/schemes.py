from pydantic import BaseModel, Field


class Notification(BaseModel):
    to_id: str = Field(..., min_length=1)  # id пользователя, которому отправляется уведомление или имя рассылки ("all")
    send_by: str = Field(..., min_length=1)  # способ отправки уведомления ("email", "websocket")
    content_key: str = Field(..., min_length=1)  # ключ контента / тип шаблона
    content_data: str = ""  # данные контента


class NotificationId(BaseModel):
    notification_id: str = ""


class Message(BaseModel):
    detail: str = ""


class Template(BaseModel):
    template: str = ""
