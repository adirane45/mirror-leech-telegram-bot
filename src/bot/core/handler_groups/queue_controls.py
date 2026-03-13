from pyrogram.filters import command
from importlib import import_module
from typing import Any

from ...helper.telegram_helper.bot_commands import BotCommands
from ...helper.telegram_helper.filters import CustomFilters
from ..handler_registry import register_message


def _load_handler(name: str) -> Any:
    module_name = ".".join(["bot", "modules", "queue_manager"])
    module = import_module(module_name)
    return getattr(module, name)


def register_queue_control_handlers(bot: Any) -> None:
    show_queue = _load_handler("show_queue")
    pause_queue = _load_handler("pause_queue")
    resume_queue = _load_handler("resume_queue")
    set_priority = _load_handler("set_priority")
    pause_all_queue = _load_handler("pause_all_queue")
    resume_all_queue = _load_handler("resume_all_queue")

    register_message(
        bot,
        show_queue,
        filters=command(BotCommands.QueueCommandList, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        pause_queue,
        filters=command(BotCommands.PauseCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        resume_queue,
        filters=command(BotCommands.ResumeCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        set_priority,
        filters=command(BotCommands.PriorityCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        pause_all_queue,
        filters=command(BotCommands.PauseAllCommand, case_sensitive=True) & CustomFilters.owner,
    )
    register_message(
        bot,
        resume_all_queue,
        filters=command(BotCommands.ResumeAllCommand, case_sensitive=True) & CustomFilters.owner,
    )
