from pyrogram.filters import command, regex

from ...helper.telegram_helper.bot_commands import BotCommands
from ...helper.telegram_helper.filters import CustomFilters
from ...modules import *
from ..handler_registry import register_callback, register_message


def register_core_admin_handlers(bot) -> None:
    register_message(
        bot,
        authorize,
        filters=command(BotCommands.AuthorizeCommand, case_sensitive=True) & CustomFilters.sudo,
    )
    register_message(
        bot,
        unauthorize,
        filters=command(BotCommands.UnAuthorizeCommand, case_sensitive=True) & CustomFilters.sudo,
    )
    register_message(
        bot,
        add_sudo,
        filters=command(BotCommands.AddSudoCommand, case_sensitive=True) & CustomFilters.owner,
    )
    register_message(
        bot,
        remove_sudo,
        filters=command(BotCommands.RmSudoCommand, case_sensitive=True) & CustomFilters.owner,
    )
    register_message(
        bot,
        send_bot_settings,
        filters=command(BotCommands.BotSetCommand, case_sensitive=True) & CustomFilters.sudo,
    )
    register_callback(
        bot,
        edit_bot_settings,
        filters=regex("^botset") & CustomFilters.sudo,
    )
    register_message(
        bot,
        cancel,
        filters=command(BotCommands.CancelTaskCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        cancel_all_buttons,
        filters=command(BotCommands.CancelAllCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_callback(bot, cancel_all_update, filters=regex("^canall"))
    register_callback(bot, cancel_multi, filters=regex("^stopm"))
    register_message(
        bot,
        clone_node,
        filters=command(BotCommands.CloneCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        aioexecute,
        filters=command(BotCommands.AExecCommand, case_sensitive=True) & CustomFilters.owner,
    )
    register_message(
        bot,
        execute,
        filters=command(BotCommands.ExecCommand, case_sensitive=True) & CustomFilters.owner,
    )
    register_message(
        bot,
        clear,
        filters=command(BotCommands.ClearLocalsCommand, case_sensitive=True) & CustomFilters.owner,
    )
    register_message(
        bot,
        select,
        filters=command(BotCommands.SelectCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_callback(bot, confirm_selection, filters=regex("^sel"))
    register_message(
        bot,
        remove_from_queue,
        filters=command(BotCommands.ForceStartCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        count_node,
        filters=command(BotCommands.CountCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        delete_file,
        filters=command(BotCommands.DeleteCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_message(
        bot,
        gdrive_search,
        filters=command(BotCommands.ListCommand, case_sensitive=True) & CustomFilters.authorized,
    )
    register_callback(bot, select_type, filters=regex("^list_types"))
    register_callback(bot, arg_usage, filters=regex("^help"))
