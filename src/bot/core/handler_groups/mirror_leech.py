from pyrogram.filters import command, regex
from importlib import import_module
from typing import Any

from ...helper.telegram_helper.bot_commands import BotCommands
from ...helper.telegram_helper.filters import CustomFilters
from ..handler_registry import register_callback, register_message


def _load_handler(module_path: str, name: str) -> Any:
    module = import_module(module_path)
    return getattr(module, name)


def register_mirror_leech_handlers(bot: Any) -> None:
    mirror_leech_module = ".".join(["bot", "modules", "mirror_leech"])
    rss_module = ".".join(["bot", "modules", "rss"])

    mirror = _load_handler(mirror_leech_module, "mirror")
    qb_mirror = _load_handler(mirror_leech_module, "qb_mirror")
    jd_mirror = _load_handler(mirror_leech_module, "jd_mirror")
    nzb_mirror = _load_handler(mirror_leech_module, "nzb_mirror")
    leech = _load_handler(mirror_leech_module, "leech")
    qb_leech = _load_handler(mirror_leech_module, "qb_leech")
    jd_leech = _load_handler(mirror_leech_module, "jd_leech")
    nzb_leech = _load_handler(mirror_leech_module, "nzb_leech")
    get_rss_menu = _load_handler(rss_module, "get_rss_menu")
    rss_listener = _load_handler(rss_module, "rss_listener")

    register_message(
        bot,
        mirror,
        filters=command(BotCommands.MirrorCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        qb_mirror,
        filters=command(BotCommands.QbMirrorCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        jd_mirror,
        filters=command(BotCommands.JdMirrorCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        nzb_mirror,
        filters=command(BotCommands.NzbMirrorCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        leech,
        filters=command(BotCommands.LeechCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        qb_leech,
        filters=command(BotCommands.QbLeechCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        jd_leech,
        filters=command(BotCommands.JdLeechCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        nzb_leech,
        filters=command(BotCommands.NzbLeechCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        get_rss_menu,
        filters=command(BotCommands.RssCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_callback(bot, rss_listener, filters=regex("^rss"))
