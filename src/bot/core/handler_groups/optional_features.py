from pyrogram.filters import command
from pyrogram.handlers import MessageHandler
from typing import Any

from ...helper.telegram_helper.filters import CustomFilters


def register_optional_features(bot: Any, logger: Any) -> None:
    try:
        from ...modules.command_health import (
            command_stats_handler,
            health_report_handler,
            reset_command_stats_handler,
        )

        bot.add_handler(
            MessageHandler(
                health_report_handler,
                filters=command(["cmdhealth", "commandhealth"], case_sensitive=True)
                & CustomFilters.authorized,
            )
        )
        bot.add_handler(
            MessageHandler(
                command_stats_handler,
                filters=command(["cmdstats", "commandstats"], case_sensitive=True)
                & CustomFilters.authorized,
            )
        )
        bot.add_handler(
            MessageHandler(
                reset_command_stats_handler,
                filters=command(["resetstats", "resetcmdstats"], case_sensitive=True)
                & CustomFilters.sudo,
            )
        )
        logger.info("✅ Command health monitoring handlers registered")
    except Exception as error:
        logger.warning(f"⚠️  Command health handlers skipped: {error}")

    try:
        from ...modules.category_b_commands import (
            boost_task,
            cancel_task,
            category_b_help,
            circuit_status,
            dlq_status,
            my_queue_position,
            queue_status,
            system_health,
        )

        bot.add_handler(
            MessageHandler(
                queue_status,
                filters=command(["qstatus"], case_sensitive=True) & CustomFilters.sudo,
            )
        )
        bot.add_handler(
            MessageHandler(
                dlq_status,
                filters=command(["dlq"], case_sensitive=True) & CustomFilters.sudo,
            )
        )
        bot.add_handler(
            MessageHandler(
                circuit_status,
                filters=command(["circuits"], case_sensitive=True) & CustomFilters.sudo,
            )
        )
        bot.add_handler(
            MessageHandler(
                boost_task,
                filters=command(["boost"], case_sensitive=True) & CustomFilters.sudo,
            )
        )
        bot.add_handler(
            MessageHandler(
                cancel_task,
                filters=command(["cancel"], case_sensitive=True) & CustomFilters.sudo,
            )
        )
        bot.add_handler(
            MessageHandler(
                system_health,
                filters=command(["health"], case_sensitive=True) & CustomFilters.sudo,
            )
        )

        bot.add_handler(
            MessageHandler(my_queue_position, filters=command(["myqueue"], case_sensitive=True))
        )
        bot.add_handler(
            MessageHandler(
                category_b_help,
                filters=command(["categoryb", "catb", "advancedhelp"], case_sensitive=True),
            )
        )

        logger.info("✅ Category B command handlers registered")
    except Exception as error:
        logger.warning(f"⚠️  Category B handlers skipped: {error}")
