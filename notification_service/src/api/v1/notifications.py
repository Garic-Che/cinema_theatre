from fastapi import APIRouter, Depends, Request

from api.v1.schemes import Notification, Message, NotificationId, Template
from services.notification import NotificationService, get_notification_service
from utils.auth_middleware import internal_auth_required

router = APIRouter()


@router.post(
    "/",
    response_model=Message,
    summary="Отправка уведомления",
)
@internal_auth_required
async def send_notification(
    request: Request,
    notification_data: Notification,
    notification_service: NotificationService = Depends(
        get_notification_service
    ),
) -> Message:
    await notification_service.send_notification(notification_data)
    return Message(detail="notification sent")


@router.get(
    "/template/{notification_id}",
    response_model=Template,
    summary="Получение шаблона уведомления",
)
@internal_auth_required
async def get_template(
    request: Request,
    notification_id: str,
    notification_service: NotificationService = Depends(
        get_notification_service
    ),
) -> Template:
    template = await notification_service.get_template(
        notification_id
    )
    return Template(template=template)


@router.post(
    "/sent",
    response_model=Message,
    summary="Извещение об отправке уведомления",
)
@internal_auth_required
async def sent_notification(
    request: Request,
    notification_data: NotificationId,
    notification_service: NotificationService = Depends(
        get_notification_service
    ),
) -> Message:
    await notification_service.set_notification_sent(
        notification_data.notification_id
    )
    return Message(detail="OK")
