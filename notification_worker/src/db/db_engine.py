from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jinja2 import Environment, meta
from async_lru import alru_cache

from db.postgres import async_session
from models.entity import NotificationDB, TemplateDB, ContentDB


class DBEngine:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_notification_by_id(
        self, notification_id: str
    ) -> NotificationDB | None:
        """Получение уведомления по его ID"""
        result = await self.session.execute(
            select(NotificationDB).where(NotificationDB.id == notification_id)
        )
        return result.scalars().one_or_none()

    @alru_cache(maxsize=1000, ttl=60)
    async def get_template_by_id(self, template_id: str) -> TemplateDB | None:
        """Получение шаблона уведомления по ID"""
        result = await self.session.execute(
            select(TemplateDB).where(TemplateDB.id == template_id)
        )
        return result.scalars().one_or_none()

    @alru_cache(maxsize=1000, ttl=60)
    async def get_content_by_id(self, content_id: str) -> ContentDB | None:
        """Получение контента для шаблона по ID"""
        result = await self.session.execute(
            select(ContentDB).where(ContentDB.id == content_id)
        )
        return result.scalars().one_or_none()

    async def get_contents_by_key(self, key: str) -> list[ContentDB]:
        """Получение списка значений контента по ключу"""
        result = await self.session.execute(
            select(ContentDB).where(ContentDB.key == key)
        )
        return list(result.scalars().all())

    async def add_template(self, template: TemplateDB) -> str:
        """Добавление в базу данных шаблона уведомления"""
        self.session.add(template)
        await self.session.commit()
        await self.session.refresh(template)
        return template.id

    async def change_template_id(
        self, notification_id: str, template_id: str
    ) -> str:
        """Изменение template_id в notification"""
        notification = await self.get_notification_by_id(notification_id)
        if not notification:
            raise ValueError("Notification not found")

        notification.template_id = template_id
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification.id

    @alru_cache(maxsize=1000, ttl=60)
    async def get_template_by_type(
        self, template_type: str
    ) -> TemplateDB | None:
        """Получение шаблона уведомления по типу"""
        result = await self.session.execute(
            select(TemplateDB).where(TemplateDB.template_type == template_type)
        )
        return result.scalars().one_or_none()

    async def get_data_from_db(
        self, notification_id: str
    ) -> tuple[str, list[ContentDB]]:
        """Получение данных из базы данных"""
        template = ""
        contents = []

        # Запросы в базу данных
        notification_data = await self.get_notification_by_id(notification_id)
        template_data = await self.get_template_by_id(
            notification_data.template_id
        )
        content_data = await self.get_content_by_id(
            notification_data.content_id
        )

        template = template_data.template or template
        if not content_data or not content_data.key:
            return template, contents

        contents = await self.get_contents_by_key(content_data.key)
        return template, contents

    async def fill_template(
        self, template: str, contents: list[ContentDB]
    ) -> str | None:
        """Заполнение шаблона.
        Если в шаблоне есть переменная content, но contents пустой,
        возвращается None."""
        values = []
        # Получение уникальных значений контента
        for content in contents:
            if content.value not in values:
                values.append(content.value)

        # Инициализация шаблона
        env = Environment()
        ast = env.parse(template)
        variables_used = meta.find_undeclared_variables(ast)
        content_variable_needed = "content" in variables_used
        content_name_variable_needed = "content_name" in variables_used

        # Заполнение шаблона
        filled_template = ""
        if content_variable_needed:
            if values:
                if content_name_variable_needed:
                    content_names = values
                    filled_template = env.from_string(template).render(
                        content=values, content_name=content_names, zip=zip
                    )
                else:
                    filled_template = env.from_string(template).render(
                        content=values
                    )
        else:
            filled_template = template
        if not filled_template:
            return None

        filled_template = await self.add_footer_and_header(filled_template)
        return filled_template

    async def add_footer_and_header(self, template: str) -> str:
        """Добавление шапки и подвала к шаблону"""
        header = await self.get_template_by_type("header")
        if header and header.template:
            template = f"{header.template}\n{template}"

        footer = await self.get_template_by_type("footer")
        if footer and footer.template:
            template = f"{template}\n{footer.template}"

        return template

    async def save_filled_template_to_db(
        self, filled_template: str, notification_id: str
    ) -> None:
        """Сохранение заполненного шаблона в базу данных
        и изменение template_id в notification"""
        template_data = TemplateDB(template=filled_template)
        template_id = await self.add_template(template_data)
        await self.change_template_id(notification_id, template_id)

    async def delete_contents_from_db(self, contents: list[ContentDB]) -> None:
        """Удаление заполненных данных из базы данных"""
        for content in contents:
            await self.session.delete(content)
        await self.session.commit()


async def get_db_engine() -> DBEngine:
    async with async_session() as session:
        return DBEngine(session)
