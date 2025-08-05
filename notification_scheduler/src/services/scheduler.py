# src/services/scheduler.py
"""
Core notification scheduler service.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional, Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_database
from models.schedule import ScheduleNotification, Template
from notification import NotificationContent
from services.auth_client import AuthAPIClient
from services.ugc_client import UGCClient
from services.theatre_client import TheatreClient
from services.notification_client import NotificationAPIClient
from services.content_builder import ContentBuilder


class NotificationScheduler:
    """Main scheduler service that orchestrates notification processing."""
    
    def __init__(self):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.database = get_database()
        
        # Initialize API clients
        self.auth_client = AuthAPIClient()
        self.ugc_client = UGCClient()
        self.theatre_client = TheatreClient()
        self.notification_client = NotificationAPIClient()
        self.content_builder = ContentBuilder()
        
        self._running = False
    
    async def start(self) -> None:
        """Start the scheduler loop."""
        self._running = True
        self.logger.info("Notification scheduler started")
        
        while self._running:
            try:
                await self._process_schedules()
                await asyncio.sleep(self.settings.SCHEDULER_INTERVAL)
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {str(e)}", exc_info=True)
                await asyncio.sleep(5)  # Brief pause before retrying
    
    def stop(self) -> None:
        """Stop the scheduler loop."""
        self._running = False
        self.logger.info("Notification scheduler stopped")
    
    async def _process_schedules(self) -> None:
        """Process all due notification schedules."""
        self.logger.info("Processing notification schedules...")
        
        async for session in self.database.get_session():
            try:
                # Fetch due schedules
                due_schedules = await self._get_due_schedules(session)
                
                if not due_schedules:
                    self.logger.debug("No due schedules found")
                    return
                
                self.logger.info(f"Found {len(due_schedules)} due schedule(s)")
                
                # Process each schedule
                for schedule in due_schedules:
                    await self._process_single_schedule(session, schedule)
                    
            except Exception as e:
                self.logger.error(f"Error processing schedules: {str(e)}", exc_info=True)
    
    async def _get_due_schedules(self, session: AsyncSession) -> List[ScheduleNotification]:
        """Fetch all schedules that are due for processing."""
        now = datetime.now(timezone.utc)
        
        query = select(ScheduleNotification).where(
            ScheduleNotification.next_send <= now
        )
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def _process_single_schedule(
        self, 
        session: AsyncSession, 
        schedule: ScheduleNotification
    ) -> None:
        """Process a single notification schedule."""
        try:
            self.logger.info(f"Processing schedule {schedule.id}")
            
            # Get users for the receiver group
            users = await self.auth_client.get_users_by_group(
                schedule.receiver_group_name
            )
            
            if not users:
                self.logger.warning(
                    f"No users found for group '{schedule.receiver_group_name}'"
                )
                await self._update_schedule_next_send(session, schedule)
                return
            
            # Process notifications for each user
            semaphore = asyncio.Semaphore(self.settings.MAX_CONCURRENT_REQUESTS)
            tasks = [
                self._process_user_notification(semaphore, user, schedule)
                for user in users
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log results
            successful = sum(1 for r in results if r is True)
            failed = len(results) - successful
            
            self.logger.info(
                f"Schedule {schedule.id} processed: "
                f"{successful} successful, {failed} failed"
            )
            
            # Update the schedule for next execution
            await self._update_schedule_next_send(session, schedule)

        except Exception as e:
            self.logger.error(
                f"Error processing schedule {schedule.id}: {str(e)}",
                exc_info=True
            )

    async def _process_user_notification(
            self,
            semaphore: asyncio.Semaphore,
            user,
            schedule: ScheduleNotification
    ) -> bool:
        """Process notification for a single user."""
        async with semaphore:
            try:
                # Получаем шаблон
                template = await self._get_template(schedule.template_id)
                if not template:
                    self.logger.error(f"Template {schedule.template_id} not found")
                    return False

                # Получаем данные в зависимости от типа шаблона
                if template.template_type == "film_recommendations":
                    films = await self.theatre_client.get_recommended_films(user.id)
                    bookmarks = await self.ugc_client.get_user_bookmarks(user.id)
                    likes = await self.ugc_client.get_user_likes(user.id)

                    # Строим контент через ContentBuilder
                    content = self.content_builder.build_content(
                        user=user.dict(),
                        films=films,
                        bookmarks=bookmarks,
                        likes=likes
                    )

                elif template.template_type == "personal_stats":
                    bookmarks = await self.ugc_client.get_user_bookmarks(user.id)
                    likes = await self.ugc_client.get_user_likes(user.id)

                    # Создаем контент вручную для этого типа
                    personal_message = (
                        f"Hello {user.login}! You have "
                        f"{len(bookmarks)} bookmarks and "
                        f"{len(likes)} likes."
                    )

                    content = NotificationContent(
                        personal_message=personal_message,
                        user_stats={
                            "bookmark_count": len(bookmarks),
                            "like_count": len(likes),
                            "last_activity": user.modified
                        }
                    )

                else:
                    # Дефолтный контент для неизвестных типов шаблонов
                    content = NotificationContent(
                        personal_message=f"Hello {user.login}! Here's your notification."
                    )

                # Отправляем уведомление
                success = await self.notification_client.send_notification(
                    user_id=user.login,
                    content_key=template.template_type,  # Используем тип шаблона как ключ
                    content_data=content,
                    send_by="email"
                )

                if success:
                    self.logger.debug(f"Notification sent successfully to {user.login}")
                else:
                    self.logger.warning(f"Failed to send notification to {user.login}")

                return success

            except Exception as e:
                self.logger.error(
                    f"Error processing notification for user {user.login}: {str(e)}",
                    exc_info=True
                )
                return False

    async def _get_template(self, template_id: UUID) -> Optional[Template]:
        """Get template from database."""
        async for session in self.database.get_session():
            try:
                query = select(Template).where(Template.id == template_id)
                result = await session.execute(query)
                return result.scalar_one_or_none()
            except Exception as e:
                self.logger.error(f"Error fetching template {template_id}: {str(e)}")
                return None

    async def _get_content_data(self, user, template_type: str) -> dict[str, Any]:
        """Get content data based on template type."""
        data = {}

        try:
            # Получаем базовую информацию о пользователе
            data['user'] = user.dict()

            # В зависимости от типа шаблона получаем разный контент
            if template_type == "film_recommendations":
                films = await self.theatre_client.get_recommended_films(user.id)
                bookmarks = await self.ugc_client.get_user_bookmarks(user.id)
                likes = await self.ugc_client.get_user_likes(user.id)

                data['films'] = films
                data['bookmarks'] = bookmarks
                data['likes'] = likes
                data['user_stats'] = {
                    'bookmark_count': len(bookmarks),
                    'like_count': len(likes)
                }

            elif template_type == "personal_stats":
                bookmarks = await self.ugc_client.get_user_bookmarks(user.id)
                likes = await self.ugc_client.get_user_likes(user.id)

                data['user_stats'] = {
                    'bookmark_count': len(bookmarks),
                    'like_count': len(likes),
                    'last_activity': user.modified
                }

            # Можно добавить другие типы шаблонов

            return data

        except Exception as e:
            self.logger.error(f"Error getting content data: {str(e)}")
            return {}

    def _fill_template(self, template: str, content_data: dict[str, Any]) -> str:
        """Fill template with content data."""
        try:
            # Простая замена плейсхолдеров
            # Например, шаблон может содержать {user.login}, {user_stats.bookmark_count} и т.д.
            from string import Template
            t = Template(template)
            return t.safe_substitute(**self._flatten_dict(content_data))
        except Exception as e:
            self.logger.error(f"Error filling template: {str(e)}")
            return template  # Возвращаем исходный шаблон в случае ошибки

    def _flatten_dict(self, d: dict[str, Any], parent_key: str = '') -> dict[str, Any]:
        """Flatten nested dictionaries for template substitution."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    async def _update_schedule_next_send(
        self,
        session: AsyncSession,
        schedule: ScheduleNotification
    ) -> None:
        """Update the schedule's next_send time or delete if it's a one-time schedule."""
        try:
            if schedule.once:
                # Delete one-time schedules after execution
                await session.delete(schedule)
                self.logger.info(f"Deleted one-time schedule {schedule.id}")
            else:
                # Update next_send for recurring schedules
                next_send = datetime.now(timezone.utc).timestamp() + schedule.period
                next_send_dt = datetime.fromtimestamp(next_send, tz=timezone.utc)
                
                await session.execute(
                    update(ScheduleNotification)
                    .where(ScheduleNotification.id == schedule.id)
                    .values(next_send=next_send_dt)
                )
                
                self.logger.info(
                    f"Updated schedule {schedule.id} next_send to {next_send_dt}"
                )
            
            await session.commit()
            
        except Exception as e:
            await session.rollback()
            self.logger.error(
                f"Error updating schedule {schedule.id}: {str(e)}",
                exc_info=True
            )