from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import Depends

from models.entity import (
    NotificationDB,
    ScheduleEventDB,
    ContentDB,
    TemplateDB,
)
from db.postgres import get_session


class DBEngine:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_template_by_type(self, template_type: str) -> TemplateDB | None:
        """Получение шаблона уведомления по типу"""
        result = await self.session.execute(
            select(TemplateDB).where(TemplateDB.template_type == template_type)
        )
        return result.scalars().one_or_none()

    async def add_notification(self, notification: NotificationDB) -> str:
        """Добавление в базу данных уведомления"""
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification.id

    async def add_schedule_notification(
        self, schedule_notification: ScheduleEventDB
    ) -> str:
        """Добавление в базу данных периодического уведомления"""
        self.session.add(schedule_notification)
        await self.session.commit()
        await self.session.refresh(schedule_notification)
        return schedule_notification.id

    async def add_content(self, content: ContentDB) -> str:
        """Добавление в базу данных контента для вставки в шаблон уведомления"""
        self.session.add(content)
        await self.session.commit()
        await self.session.refresh(content)
        return content.id

    async def add_template(self, template: TemplateDB) -> str:
        """Добавление в базу данных шаблона уведомления"""
        self.session.add(template)
        await self.session.commit()
        await self.session.refresh(template)
        return template.id

    async def get_template_by_id(self, template_id: str) -> TemplateDB | None:
        """Получение шаблона уведомления по его ID"""
        result = await self.session.execute(
            select(TemplateDB).where(TemplateDB.id == template_id)
        )
        return result.scalars().one_or_none()

    async def delete_template(self, template_id: str) -> None:
        """Удаление шаблона уведомления по его ID"""
        template = await self.get_template_by_id(template_id)
        if template:
            await self.session.delete(template)
            await self.session.commit()

    async def get_notification_by_id(self, notification_id: str) -> NotificationDB | None:
        """Получение уведомления по его ID"""
        result = await self.session.execute(
            select(NotificationDB).where(NotificationDB.id == notification_id)
        )
        return result.scalars().one_or_none()

    async def delete_notification(self, notification_id: str) -> bool:
        """Удаление уведомления по его ID.
        Если шаблон не имеет типа, он также удаляется"""
        notification = await self.get_notification_by_id(notification_id)

        if not notification:
            return False

        template_id = notification.template_id
        if template_id:
            template = await self.get_template_by_id(template_id)
            # Если шаблон не имеет типа, удаляем его из базы данных
            if template and not template.template_type:
                await self.delete_template(template_id)
                # Дальше каскадное удаление notification
            else:
                await self.session.delete(notification)
                await self.session.commit()
        return True

    async def set_notification_sent(self, notification_id: str) -> bool:
        """Установка уведомления как отправленного"""
        notification = await self.get_notification_by_id(notification_id)
        if not notification:
            return None
        notification.sent = True
        await self.session.commit()
        await self.session.refresh(notification)
        return notification.sent

    async def get_template_by_notification_id(
        self, notification_id: str
    ) -> TemplateDB | None:
        """Получение шаблона уведомления по его ID"""
        notification = await self.get_notification_by_id(notification_id)
        if not notification:
            return None
        result = await self.session.execute(
            select(TemplateDB).where(TemplateDB.id == notification.template_id)
        )
        return result.scalars().one_or_none()


def get_db_engine(session: AsyncSession = Depends(get_session)) -> DBEngine:
    return DBEngine(session)
