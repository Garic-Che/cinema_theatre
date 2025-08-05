import logging

from db.auth_service_engine import AuthServiceEngine
from db.db_engine import DBEngine
from db.postgres import get_db
from core.config import settings


async def check_role_existence():
    """Проверка существования ролей в AuthService"""
    logging.debug("Проверка существования ролей в AuthService")
    # Получаем роли из AuthService
    auth_service_engine = AuthServiceEngine(settings)
    roles = await auth_service_engine.get_roles()
    roles_ids = [role.id for role in roles]
    logging.debug("Найдено %d ролей в AuthService: %s", len(roles), roles_ids)

    # Получаем роли из БД
    async with get_db() as session:
        db_engine = DBEngine(session)
        roles_db = await db_engine.get_role_ids()
        logging.debug("Найдено %d ролей в БД: %s", len(roles_db), list(roles_db))
        # Удаляем роли, которых нет в AuthService
        for role_id in roles_db:
            if str(role_id) not in roles_ids:
                logging.debug("Роль не существует в AuthService: %s", role_id)
                try:
                    await db_engine.update_by_role_id(role_id, {"actual": False})
                except Exception as e:
                    logging.error("Ошибка при обновлении роли: %s", e)
        await session.commit()
