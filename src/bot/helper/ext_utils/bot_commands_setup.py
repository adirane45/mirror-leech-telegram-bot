# Bot Commands Setup - Modified by: justadi
from pyrogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllGroupChats,
)

from ...core.telegram_manager import TgClient
from ..telegram_helper.bot_commands import BotCommands
from ... import LOGGER


async def set_bot_commands():
    """Set bot commands that appear in Telegram's command menu"""
    # Get the command suffix
    i = getattr(BotCommands, 'StartCommand', 'start').replace('start', '')
    
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Get help and command list"),
        BotCommand(f"mirror{i}", "Mirror a file/folder to cloud"),
        BotCommand(f"leech{i}", "Leech a file/folder to Telegram"),
        BotCommand(f"clone{i}", "Clone from Google Drive"),
        BotCommand(f"status{i}", "Show active downloads"),
        BotCommand(f"dashboard{i}", "Show system overview"),
        BotCommand(f"queue{i}", "Show task queue"),
        BotCommand(f"speed{i}", "Test server speed"),
        BotCommand(f"schedule{i}", "Schedule a task"),
        BotCommand(f"schedules{i}", "List scheduled tasks"),
        BotCommand(f"unschedule{i}", "Cancel scheduled task"),
        BotCommand(f"limit{i}", "Set global bandwidth limit"),
        BotCommand(f"limit_task{i}", "Set task bandwidth limit"),
        BotCommand(f"category{i}", "Manage categories"),
        BotCommand(f"categorize{i}", "Categorize a task"),
        BotCommand(f"history{i}", "View download history"),
        BotCommand(f"settings{i}", "Configure bot settings"),
        BotCommand(f"cancel{i}", "Cancel a task"),
        BotCommand(f"stats{i}", "Show bot statistics"),
        BotCommand(f"estats{i}", "Enhanced statistics dashboard"),
        BotCommand(f"edash{i}", "Enhanced detailed dashboard"),
        BotCommand(f"equick{i}", "Quick status overview"),
        BotCommand(f"eanalytics{i}", "Task analytics"),
        BotCommand(f"rmon{i}", "Resource monitor"),
        BotCommand(f"health{i}", "System health report"),
        BotCommand(f"psummary{i}", "Progress summary"),
        BotCommand(f"cstats{i}", "Comparison stats"),
    ]
    
    try:
        from asyncio import sleep
        scopes = [
            BotCommandScopeDefault(),
            BotCommandScopeAllPrivateChats(),
            BotCommandScopeAllGroupChats(),
        ]

        # Clear then set commands for all major scopes to avoid language/scope mismatch.
        for scope in scopes:
            try:
                await TgClient.bot.delete_bot_commands(scope=scope)
            except Exception as clear_err:
                LOGGER.debug(f"Command clear skipped for scope {scope}: {clear_err}")

        await sleep(0.5)

        for scope in scopes:
            await TgClient.bot.set_bot_commands(commands=commands, scope=scope)

        LOGGER.info("✅ Bot commands set successfully for default/private/group scopes")
    except Exception as e:
        LOGGER.error(f"Failed to set bot commands: {e}")

