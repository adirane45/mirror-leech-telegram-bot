# Bot Command Handlers
# Enhanced with Interactive UI and Queue Management
# Modified by: justadi

from importlib import import_module
from typing import Any

from pyrogram.filters import command, regex

from .handler_registry import register_callback, register_edited, register_message


def _module_symbol(name: str) -> Any:
    modules = import_module("bot.modules")
    return getattr(modules, name)


def _service_symbol(name: str) -> Any:
    services = import_module("bot.modules.services")
    return getattr(services, name)


def _group_symbol(module_name: str, symbol: str) -> Any:
    group_module = import_module(module_name)
    return getattr(group_module, symbol)


def _bot_commands() -> Any:
    commands_module = import_module("bot.helper.telegram_helper.bot_commands")
    return getattr(commands_module, "BotCommands")


def _custom_filters() -> Any:
    filters_module = import_module("bot.helper.telegram_helper.filters")
    return getattr(filters_module, "CustomFilters")


def _get_tg_bot() -> Any | None:
    telegram_manager = import_module("bot.core.telegram_manager")
    tg_client = getattr(telegram_manager, "TgClient")
    return getattr(tg_client, "bot", None)


async def _command_audit(_: Any, message: Any) -> None:
    try:
        text = getattr(message, "text", "") or ""
        if text.startswith("/"):
            from .. import LOGGER
            from .command_health_monitor import command_health_monitor

            user_id = message.from_user.id if message.from_user else "unknown"
            LOGGER.info(f"🧪 CMD_AUDIT user={user_id} text={text}")

            parts = text.split()
            command_name = parts[0].lstrip("/") if parts else ""
            if command_name and command_health_monitor._enabled:
                pass
    except Exception:
        pass


def _register_core_handlers(bot: Any) -> None:
    BotCommands = _bot_commands()
    CustomFilters = _custom_filters()
    run_shell = _module_symbol("run_shell")
    start = _module_symbol("start")
    log = _module_symbol("log")
    stream_link = _module_symbol("stream_link")
    bypass_link = _module_symbol("bypass_link")
    restart_bot = _module_symbol("restart_bot")
    confirm_restart = _module_symbol("confirm_restart")
    ping = _module_symbol("ping")
    bot_help = _module_symbol("bot_help")
    command_list = _module_symbol("command_list")
    onboarding_callback = _module_symbol("onboarding_callback")
    bot_stats = _module_symbol("bot_stats")
    speedtest = _module_symbol("speedtest")
    schedule_task = _module_symbol("schedule_task")
    list_schedules = _module_symbol("list_schedules")
    cancel_schedule = _module_symbol("cancel_schedule")
    set_bandwidth = _module_symbol("set_bandwidth")
    set_task_bandwidth = _module_symbol("set_task_bandwidth")
    manage_categories = _module_symbol("manage_categories")
    categorize_task = _module_symbol("categorize_task")
    torrent_search = _module_symbol("torrent_search")
    torrent_search_update = _module_symbol("torrent_search_update")
    get_users_settings = _module_symbol("get_users_settings")
    send_user_settings = _module_symbol("send_user_settings")
    edit_user_settings = _module_symbol("edit_user_settings")
    ytdl = _module_symbol("ytdl")
    ytdl_leech = _module_symbol("ytdl_leech")
    hydra_search = _module_symbol("hydra_search")
    web_logs = _service_symbol("web_logs")
    reload_config = _service_symbol("reload_config")
    register_core_admin_handlers = _group_symbol(
        "bot.core.handler_groups.core_admin", "register_core_admin_handlers"
    )
    register_mirror_leech_handlers = _group_symbol(
        "bot.core.handler_groups.mirror_leech", "register_mirror_leech_handlers"
    )
    register_queue_control_handlers = _group_symbol(
        "bot.core.handler_groups.queue_controls", "register_queue_control_handlers"
    )
    register_media_archive_handlers = _group_symbol(
        "bot.core.handler_groups.media_archive", "register_media_archive_handlers"
    )
    register_status_dashboard_handlers = _group_symbol(
        "bot.core.handler_groups.status_dashboard", "register_status_dashboard_handlers"
    )
    register_task_status_handlers = _group_symbol(
        "bot.core.handler_groups.status_dashboard", "register_task_status_handlers"
    )

    register_message(
        bot,
        _command_audit,
        filters=regex(r"^/"),
        group=-100,
    )
    register_core_admin_handlers(bot)
    register_message(
        bot,
        run_shell,
        filters=command(BotCommands.ShellCommand, case_sensitive=True) & CustomFilters.owner,
    )
    register_mirror_leech_handlers(bot)
    register_edited(
        bot,
        run_shell,
        filters=command(BotCommands.ShellCommand, case_sensitive=True) & CustomFilters.owner,
    )
    register_message(
        bot,
        start,
        filters=command(BotCommands.StartCommandList, case_sensitive=True),
    )
    register_message(
        bot,
        log,
        filters=command(BotCommands.LogCommand, case_sensitive=True) & CustomFilters.sudo,
    )
    register_message(
        bot,
        web_logs,
        filters=command(BotCommands.WebLogsCommand, case_sensitive=True) & CustomFilters.sudo,
    )
    register_message(
        bot,
        reload_config,
        filters=command(BotCommands.ReloadConfigCommand, case_sensitive=True) & CustomFilters.sudo,
    )
    register_message(
        bot,
        stream_link,
        filters=command(BotCommands.StreamLinkCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        bypass_link,
        filters=command(BotCommands.BypassCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        restart_bot,
        filters=command(BotCommands.RestartCommand, case_sensitive=True) & CustomFilters.sudo,
    )
    register_callback(
        bot,
        confirm_restart,
        filters=regex("^botrestart") & CustomFilters.sudo,
    )
    register_message(
        bot,
        ping,
        filters=command(BotCommands.PingCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        bot_help,
        filters=command(BotCommands.HelpCommandList, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        command_list,
        filters=command(BotCommands.CommandListCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_callback(bot, onboarding_callback, filters=regex("^onboard"))
    register_message(
        bot,
        bot_stats,
        filters=command(BotCommands.StatsCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        speedtest,
        filters=command(BotCommands.SpeedCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        schedule_task,
        filters=command(BotCommands.ScheduleCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        list_schedules,
        filters=command(BotCommands.SchedulesCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        cancel_schedule,
        filters=command(BotCommands.UnscheduleCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        set_bandwidth,
        filters=command(BotCommands.LimitCommand, case_sensitive=True) & CustomFilters.sudo,
    )
    register_message(
        bot,
        set_task_bandwidth,
        filters=command(BotCommands.LimitTaskCommand, case_sensitive=True) & CustomFilters.sudo,
    )
    register_message(
        bot,
        manage_categories,
        filters=command(BotCommands.CategoryCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        categorize_task,
        filters=command(BotCommands.CategorizeCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_task_status_handlers(bot)
    register_message(
        bot,
        torrent_search,
        filters=command(BotCommands.SearchCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_callback(bot, torrent_search_update, filters=regex("^torser"))
    register_message(
        bot,
        get_users_settings,
        filters=command(BotCommands.UsersCommand, case_sensitive=True) & CustomFilters.sudo,
    )
    register_message(
        bot,
        send_user_settings,
        filters=command(BotCommands.UserSetCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_callback(bot, edit_user_settings, filters=regex("^userset"))
    register_message(
        bot,
        ytdl,
        filters=command(BotCommands.YtdlCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        ytdl_leech,
        filters=command(BotCommands.YtdlLeechCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        hydra_search,
        filters=command(BotCommands.NzbSearchCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_queue_control_handlers(bot)
    register_media_archive_handlers(bot)
    register_status_dashboard_handlers(bot)


def add_handlers() -> None:
    try:
        from .. import LOGGER

        LOGGER.info("???? Registering bot command handlers...")
        bot = _get_tg_bot()
        if bot:
            _register_core_handlers(bot)
            register_optional_features = _group_symbol(
                "bot.core.handler_groups", "register_optional_features"
            )
            register_optional_features(bot, LOGGER)
        LOGGER.info("✅ All bot command handlers registered successfully")
    except Exception as error:
        from .. import LOGGER

        LOGGER.error(f"??? ERROR in add_handlers(): {error}", exc_info=True)
        raise
