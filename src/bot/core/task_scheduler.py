# Task Scheduling Module
# Schedule downloads to start at specific times
# Supports recurring tasks (daily, weekly, monthly)
# Modified by: justadi

import asyncio
import logging
from datetime import datetime
from importlib import import_module
from secrets import randbelow
from time import time
from typing import Any, TypedDict, cast

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

LOGGER = logging.getLogger(__name__)


def _get_database() -> Any:
    db_module = import_module("bot.helper.ext_utils.db_handler")
    return getattr(db_module, "database")


def _get_tg_bot() -> Any | None:
    tg_module = import_module("bot.core.telegram_manager")
    tg_client = getattr(tg_module, "TgClient")
    return getattr(tg_client, "bot", None)


class TaskRecord(TypedDict):
    user_id: int
    chat_id: int
    command: str
    name: str
    is_leech: bool
    created_at: datetime
    scheduled_for: datetime
    recurring: str | None
    kwargs: dict[str, Any]
    status: str


class TaskScheduler:
    """
    Manages scheduled downloads and recurring tasks
    """

    scheduler: AsyncIOScheduler | None = None
    scheduled_tasks: dict[str, TaskRecord] = {}

    @classmethod
    def _get_scheduler(cls) -> AsyncIOScheduler:
        if cls.scheduler is None:
            loop = asyncio.get_running_loop()
            cls.scheduler = AsyncIOScheduler(event_loop=loop)
        return cls.scheduler

    @classmethod
    async def init(cls) -> None:
        """Initialize the scheduler"""
        scheduler = cls._get_scheduler()
        if not scheduler.running:
            scheduler.start()
            LOGGER.info("Task Scheduler initialized")
        # Load scheduled tasks from DB if available
        try:
            database = _get_database()
            saved = await database.get_task_schedules()
            for task_id, task_data in saved.items():
                start_time = task_data.get("scheduled_for")
                if isinstance(start_time, str):
                    try:
                        start_time = datetime.fromisoformat(start_time)
                    except Exception:
                        continue
                recurring = task_data.get("recurring")
                recurring_text = recurring if isinstance(recurring, str) else None
                if not isinstance(start_time, datetime):
                    continue
                trigger = cls._get_cron_trigger(start_time, recurring_text)
                scheduler.add_job(
                    cls._execute_scheduled_task,
                    trigger,
                    args=(task_id, task_data),
                    id=f"task_{task_id}",
                    replace_existing=True,
                )
                cls.scheduled_tasks[task_id] = cast(TaskRecord, task_data)
        except Exception as error:
            LOGGER.error(f"Error loading scheduled tasks: {error}")

    @classmethod
    async def schedule_download(
        cls,
        task_id: str,
        user_id: int,
        chat_id: int,
        command_text: str,
        start_time: datetime,
        recurring: str | None = None,
        name: str = "",
        is_leech: bool = False,
        **kwargs: Any,
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
            scheduler = cls._get_scheduler()
            database = _get_database()
            task_data: TaskRecord = {
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

            scheduler.add_job(
                cls._execute_scheduled_task,
                trigger,
                args=(task_id, task_data),
                id=f"task_{task_id}",
                replace_existing=True
            )

            cls.scheduled_tasks[task_id] = task_data
            LOGGER.info(f"Task {task_id} scheduled for {start_time}")
            return True

        except Exception as error:
            LOGGER.error(f"Error scheduling task: {error}")
            return False

    @classmethod
    async def cancel_scheduled_task(cls, task_id: str) -> bool:
        """Cancel a scheduled task"""
        try:
            scheduler = cls._get_scheduler()
            database = _get_database()
            job_id = f"task_{task_id}"
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)
            if task_id in cls.scheduled_tasks:
                del cls.scheduled_tasks[task_id]
            await database.delete_task_schedule(task_id)
            LOGGER.info(f"Task {task_id} cancelled")
            return True
        except Exception as error:
            LOGGER.error(f"Error cancelling task: {error}")
            return False

    @classmethod
    async def get_scheduled_tasks(cls, user_id: int) -> list[dict[str, Any]]:
        """Get all scheduled tasks for a user"""
        result: list[dict[str, Any]] = []
        for task_id, task in cls.scheduled_tasks.items():
            if task.get("user_id") == user_id:
                item = dict(task)
                item["_id"] = task_id
                result.append(item)
        return result

    @classmethod
    async def _execute_scheduled_task(
        cls, task_id: str, task_data: TaskRecord | dict[str, Any]
    ) -> None:
        """Execute a scheduled task"""
        try:
            database = _get_database()
            module_name = ".".join(["bot", "modules", "mirror_leech"])
            mirror_leech_module = import_module(module_name)
            leech = getattr(mirror_leech_module, "leech")
            mirror = getattr(mirror_leech_module, "mirror")

            class ScheduledUser:
                def __init__(self, uid: int) -> None:
                    self.id = uid

            class ScheduledChat:
                def __init__(self, cid: int) -> None:
                    self.id = cid

            class ScheduledMessage:
                def __init__(self, chat_id: int, user_id: int, text: str) -> None:
                    self.text = text
                    self.chat = ScheduledChat(chat_id)
                    self.from_user = ScheduledUser(user_id)
                    self.sender_chat = None
                    self.reply_to_message = None
                    self.link = None
                    self.id = int(time() * 1000) + randbelow(1000)

                async def reply(
                    self,
                    text: str,
                    disable_notification: bool = True,
                    reply_markup: Any = None,
                ) -> Any:
                    bot = _get_tg_bot()
                    if bot is None:
                        return None
                    return await bot.send_message(
                        chat_id=self.chat.id,
                        text=text,
                        disable_notification=disable_notification,
                        reply_markup=reply_markup,
                    )

            message = ScheduledMessage(
                int(task_data.get("chat_id", 0)),
                int(task_data.get("user_id", 0)),
                str(task_data.get("command", "")),
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

        except Exception as error:
            task_data["status"] = "failed"
            LOGGER.error(f"Error executing scheduled task {task_id}: {error}")
            await database.save_task_schedule(task_id, task_data)

    @staticmethod
    def _get_cron_trigger(dt: datetime, recurring: str | None) -> CronTrigger | datetime:
        """Get a cron trigger for recurring tasks"""
        if recurring is None:
            return dt
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
