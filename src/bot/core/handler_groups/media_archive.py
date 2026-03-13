from pyrogram.filters import command
from typing import Any

from ...helper.telegram_helper.bot_commands import BotCommands
from ...helper.telegram_helper.filters import CustomFilters
from ...modules.archive import compress_file, extract_archive, list_archive
from ...modules.mediainfo import extract_thumbnail, get_media_info, quick_media_stats
from ..handler_registry import register_message


def register_media_archive_handlers(bot: Any) -> None:
    register_message(
        bot,
        compress_file,
        filters=command(BotCommands.ZipCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        extract_archive,
        filters=command(BotCommands.UnzipCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        list_archive,
        filters=command(BotCommands.ZipInfoCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        get_media_info,
        filters=command(BotCommands.MediaInfoCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        extract_thumbnail,
        filters=command(BotCommands.ThumbnailCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        quick_media_stats,
        filters=command(BotCommands.MStatsCommand, case_sensitive=True) & CustomFilters.authorized,
    )
