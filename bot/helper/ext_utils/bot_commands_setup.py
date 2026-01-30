# Bot Commands Setup - Modified by: justadi
from pyrogram.types import BotCommand

from ...core.telegram_manager import TgClient
from ..telegram_helper.bot_commands import BotCommands
from ... import LOGGER


async def set_bot_commands():
    """Set bot commands that appear in Telegram's command menu"""
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Get help and command list"),
        BotCommand("mirror", "Mirror a file/folder to cloud"),
        BotCommand("leech", "Leech a file/folder to Telegram"),
        BotCommand("clone", "Clone from Google Drive"),
        BotCommand("status", "Show active downloads"),
        BotCommand("dashboard", "Show system overview"),
        BotCommand("queue", "Show task queue"),
        BotCommand("speed", "Test server speed"),
        BotCommand("history", "View download history"),
        BotCommand("settings", "Configure bot settings"),
        BotCommand("cancel", "Cancel a task"),
        BotCommand("stats", "Show bot statistics"),
    ]
    
    try:
        await TgClient.bot.set_bot_commands(commands)
        LOGGER.info("Bot commands set successfully")
    except Exception as e:
        LOGGER.error(f"Failed to set bot commands: {e}")
