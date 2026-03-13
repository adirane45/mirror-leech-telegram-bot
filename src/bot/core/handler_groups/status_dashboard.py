from pyrogram.filters import command, regex

from ...helper.telegram_helper.bot_commands import BotCommands
from ...helper.telegram_helper.filters import CustomFilters
from ...modules import *
from ...modules.enhanced_dashboard import (
    comparison_stats_handler,
    enhanced_analytics_handler,
    enhanced_dashboard_handler,
    enhanced_quick_status_handler,
    enhanced_stats_handler,
    progress_summary_handler,
    resource_monitor_handler,
    system_health_handler,
)
from ..handler_registry import register_callback, register_message


def register_task_status_handlers(bot) -> None:
    register_message(
        bot,
        task_status,
        filters=command(BotCommands.StatusCommandList, case_sensitive=True) & CustomFilters.authorized,
    )
    register_callback(bot, status_pages, filters=regex("^status"))


def register_status_dashboard_handlers(bot) -> None:
    register_message(
        bot,
        dashboard,
        filters=command(BotCommands.DashboardCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        dashboard,
        filters=command(BotCommands.WebDashboardCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        task_details,
        filters=command(BotCommands.TaskDetailsCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        search_tasks,
        filters=command(BotCommands.SearchTasksCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        filter_tasks,
        filters=command(BotCommands.FilterTasksCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        download_history_view,
        filters=command(BotCommands.HistoryCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        settings_panel,
        filters=command(BotCommands.SettingsUICommandList, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        view_toggle,
        filters=command(BotCommands.ViewToggleCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        set_alerts,
        filters=command(BotCommands.SetAlertsCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_callback(bot, settings_callback, filters=regex("^settings"))
    register_callback(bot, dashboard_callback_handler, filters=regex("^quick"))

    register_message(
        bot,
        enhanced_stats_handler,
        filters=command(BotCommands.EnhancedStatsCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        enhanced_dashboard_handler,
        filters=command(BotCommands.EnhancedDashCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        enhanced_quick_status_handler,
        filters=command(BotCommands.EnhancedQuickCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        enhanced_analytics_handler,
        filters=command(BotCommands.EnhancedAnalyticsCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        resource_monitor_handler,
        filters=command(BotCommands.ResourceMonitorCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        system_health_handler,
        filters=command(BotCommands.SystemHealthCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        progress_summary_handler,
        filters=command(BotCommands.ProgressSummaryCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        comparison_stats_handler,
        filters=command(BotCommands.ComparisonStatsCommand, case_sensitive=True) & CustomFilters.authorized,
    )
