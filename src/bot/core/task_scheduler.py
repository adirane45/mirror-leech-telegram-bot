# Task Scheduling Module
# Schedule downloads to start at specific times
# Supports recurring tasks (daily, weekly, monthly)
# Modified by: justadi

from datetime import datetime
from typing import Optional, Dict, List
from secrets import randbelow
from time import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .. import LOGGER, bot_loop
from ..core.telegram_manager import TgClient
from ..helper.ext_utils.db_handler import database


class TaskScheduler:
    """
    Manages scheduled downloads and recurring tasks
    """
    
    scheduler = AsyncIOScheduler(event_loop=bot_loop)
    scheduled_tasks: Dict[str, dict] = {}
    
    @classmethod
    async def init(cls):
        """Initialize the scheduler"""
        if not cls.scheduler.running:
            cls.scheduler.start()
            LOGGER.info("Task Scheduler initialized")
        # Load scheduled tasks from DB if available
        try:
            saved = await database.get_task_schedules()
            for task_id, task_data in saved.items():
                start_time = task_data.get("scheduled_for")
                if isinstance(start_time, str):
                    try:
                        start_time = datetime.fromisoformat(start_time)
                    except Exception:
                        continue
                trigger = cls._get_cron_trigger(start_time, task_data.get("recurring"))
                cls.scheduler.add_job(
                    cls._execute_scheduled_task,
                    trigger,
                    args=(task_id, task_data),
                    id=f"task_{task_id}",
                    replace_existing=True,
                )
                cls.scheduled_tasks[task_id] = task_data
        except Exception as e:
            LOGGER.error(f"Error loading scheduled tasks: {e}")
    
    @classmethod
    async def schedule_download(
        cls,
        task_id: str,
        user_id: int,
        chat_id: int,
        command_text: str,
        start_time: datetime,
        recurring: Optional[str] = None,
        name: str = "",
        is_leech: bool = False,
        **kwargs
    ) -> bool:
        """
        Schedule a download to start at a specific time
        
        Args:
            task_id: Unique task identifier
            user_id: Telegram user ID
            download_link: Link to download
            start_time: When to start the download
            recurring: Recurring pattern (daily, weekly, etc.)
            name: Task name
            is_leech: Whether it's a leech task
            **kwargs: Additional parameters
            
        Returns:
            True if scheduled successfully
        """
        try:
            task_data = {
                "user_id": user_id,
                "chat_id": chat_id,
                "command": command_text,
                "name": name,
                "is_leech": is_leech,
                "created_at": datetime.now(),
                "scheduled_for": start_time,
                "recurring": recurring,
                "kwargs": kwargs,
                "status": "scheduled"
            }
            
            # Save to database
            await database.save_task_schedule(task_id, task_data)
            
            # Schedule the job
            if recurring:
                trigger = cls._get_cron_trigger(start_time, recurring)
            else:
                trigger = start_time
            
            cls.scheduler.add_job(
                cls._execute_scheduled_task,
                trigger,
                args=(task_id, task_data),
                id=f"task_{task_id}",
                replace_existing=True
            )
            
            cls.scheduled_tasks[task_id] = task_data
            LOGGER.info(f"Task {task_id} scheduled for {start_time}")
            return True
            
        except Exception as e:
            LOGGER.error(f"Error scheduling task: {e}")
            return False
    
    @classmethod
    async def cancel_scheduled_task(cls, task_id: str) -> bool:
        """Cancel a scheduled task"""
        try:
            job_id = f"task_{task_id}"
            if cls.scheduler.get_job(job_id):
                cls.scheduler.remove_job(job_id)
            if task_id in cls.scheduled_tasks:
                del cls.scheduled_tasks[task_id]
            await database.delete_task_schedule(task_id)
            LOGGER.info(f"Task {task_id} cancelled")
            return True
        except Exception as e:
            LOGGER.error(f"Error cancelling task: {e}")
            return False
    
    @classmethod
    async def get_scheduled_tasks(cls, user_id: int) -> List[dict]:
        """Get all scheduled tasks for a user"""
        result = []
        for task_id, task in cls.scheduled_tasks.items():
            if task.get("user_id") == user_id:
                item = task.copy()
                item["_id"] = task_id
                result.append(item)
        return result
    
    @classmethod
    async def _execute_scheduled_task(cls, task_id: str, task_data: dict):
        """Execute a scheduled task"""
        try:
            from ..modules.mirror_leech import mirror, leech

            class ScheduledUser:
                def __init__(self, uid: int):
                    self.id = uid

            class ScheduledChat:
                def __init__(self, cid: int):
                    self.id = cid

            class ScheduledMessage:
                def __init__(self, chat_id: int, user_id: int, text: str):
                    self.text = text
                    self.chat = ScheduledChat(chat_id)
                    self.from_user = ScheduledUser(user_id)
                    self.sender_chat = None
                    self.reply_to_message = None
                    self.link = None
                    self.id = int(time() * 1000) + randbelow(1000)

                async def reply(self, text, disable_notification=True, reply_markup=None):
                    return await TgClient.bot.send_message(
                        chat_id=self.chat.id,
                        text=text,
                        disable_notification=disable_notification,
                        reply_markup=reply_markup,
                    )

            message = ScheduledMessage(
                task_data.get("chat_id"),
                task_data.get("user_id"),
                task_data.get("command"),
            )

            # Update status
            task_data["status"] = "executing"
            
            # Execute the appropriate function
            if task_data.get("is_leech"):
                await leech(None, message)
            else:
                await mirror(None, message)
            
            task_data["status"] = "completed"
            LOGGER.info(f"Scheduled task {task_id} executed successfully")
            await database.save_task_schedule(task_id, task_data)
            
        except Exception as e:
            task_data["status"] = "failed"
            LOGGER.error(f"Error executing scheduled task {task_id}: {e}")
            await database.save_task_schedule(task_id, task_data)
    
    @staticmethod
    def _get_cron_trigger(dt: datetime, recurring: str):
        """Get a cron trigger for recurring tasks"""
        recurring = recurring.lower()
        
        if recurring == "daily":
            return CronTrigger(hour=dt.hour, minute=dt.minute)
        elif recurring == "weekly":
            days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
            day_of_week = days[dt.weekday()]
            return CronTrigger(day_of_week=day_of_week, hour=dt.hour, minute=dt.minute)
        elif recurring == "monthly":
            return CronTrigger(day=dt.day, hour=dt.hour, minute=dt.minute)
        elif recurring == "hourly":
            return CronTrigger(minute=dt.minute)
        else:
            return dt
