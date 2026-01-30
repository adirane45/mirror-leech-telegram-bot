# Bot Commands Setup - Modified by: justadi
from pyrogram.types import BotCommand

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
    ]
    
    try:
        await TgClient.bot.set_bot_commands(commands)
        LOGGER.info("Bot commands set successfully")
    except Exception as e:
        LOGGER.error(f"Failed to set bot commands: {e}")

