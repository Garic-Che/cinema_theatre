"""add test data

Revision ID: add_test_data
Revises: b204cda77077
Create Date: 2025-01-27 10:00:00.000000

"""

from typing import Sequence, Union
import uuid
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_test_data"
down_revision: Union[str, None] = "b204cda77077"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add test data."""
    # Создаем тестовые роли
    subscription1_id = "30c911d7-e22f-42aa-9b86-433b1da0e5d2"
    subscription2_id = "55bc01fe-3005-4bfe-81a9-db305c4db235"

    op.execute(f"""
        INSERT INTO content.role (id, name, created, modified) 
        VALUES 
            ('{subscription1_id}', 'subscription1', '{datetime.utcnow()}', '{datetime.utcnow()}'),
            ('{subscription2_id}', 'subscription2', '{datetime.utcnow()}', '{datetime.utcnow()}')
        ON CONFLICT (name) DO NOTHING;
    """)

    # Создаем тестового пользователя
    test_user_id = "de508489-c283-4400-856b-fbb2f510536d"
    op.execute(f"""
        INSERT INTO content.user (id, login, password, email, created, modified) 
        VALUES 
            ('{test_user_id}', 'test_user', 'hashed_password_here', 'test@example.com', '{datetime.utcnow()}', '{datetime.utcnow()}')
        ON CONFLICT (login) DO NOTHING;
    """)

    # Назначаем пользователю роль subscription1
    op.execute(f"""
        INSERT INTO content.user_role (user_id, role_id) 
        VALUES ('{test_user_id}', '{subscription1_id}')
        ON CONFLICT DO NOTHING;
    """)
    # Назначаем пользователю роль subscription2
    op.execute(f"""
        INSERT INTO content.user_role (user_id, role_id) 
        VALUES ('{test_user_id}', '{subscription2_id}')
        ON CONFLICT DO NOTHING;
    """)


def downgrade() -> None:
    """Remove test data."""
    # Удаляем связи пользователя с ролями
    op.execute("""
        DELETE FROM content.user_role 
        WHERE user_id IN (
            SELECT id FROM content.user WHERE login = 'test_user'
        );
    """)

    # Удаляем тестового пользователя
    op.execute("""
        DELETE FROM content.user 
        WHERE login = 'test_user';
    """)

    # Удаляем тестовые роли
    op.execute("""
        DELETE FROM content.role 
        WHERE name IN ('subscription1', 'subscription2');
    """)
