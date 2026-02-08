from ..helper.ext_utils.bot_utils import COMMAND_USAGE, new_task
from ..helper.ext_utils.help_messages import (
    YT_HELP_DICT,
    MIRROR_HELP_DICT,
    CLONE_HELP_DICT,
    HELP_CATEGORIES,
    HELP_CATEGORY_ORDER,
    HELP_CATEGORY_ALIASES,
    build_help_home_text,
    build_help_category_text,
    search_help,
)
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.message_utils import edit_message, delete_message, send_message
from ..helper.ext_utils.help_messages import help_string


def _help_menu_buttons():
    buttons = ButtonMaker()
    for key in HELP_CATEGORY_ORDER:
        title = HELP_CATEGORIES[key]["title"]
        buttons.data_button(title, f"help cat {key}")
    buttons.data_button("Search", "help search", position="footer")
    buttons.data_button("Close", "help close", position="footer")
    buttons.data_button("Queue", "quick_queue", position="header")
    buttons.data_button("Status", "quick_status", position="header")
    buttons.data_button("Settings", "quick_settings", position="header")
    return buttons.build_menu(2)


def _help_back_buttons():
    buttons = ButtonMaker()
    buttons.data_button("Back", "help menu")
    buttons.data_button("Close", "help close")
    return buttons.build_menu(2)


@new_task
async def arg_usage(_, query):
    data = query.data.split()
    message = query.message
    if data[1] == "close":
        await delete_message(message)
    elif data[1] == "menu":
        await edit_message(message, build_help_home_text(), _help_menu_buttons())
    elif data[1] == "cat":
        category_key = data[2]
        await edit_message(
            message, build_help_category_text(category_key), _help_back_buttons()
        )
    elif data[1] == "search":
        await edit_message(
            message,
            "<b>🔎 Search Help</b>\n\nType <code>/help keyword</code> to search commands.",
            _help_back_buttons(),
        )
    elif data[1] == "back":
        if data[2] == "m":
            await edit_message(
                message, COMMAND_USAGE["mirror"][0], COMMAND_USAGE["mirror"][1]
            )
        elif data[2] == "y":
            await edit_message(message, COMMAND_USAGE["yt"][0], COMMAND_USAGE["yt"][1])
        elif data[2] == "c":
            await edit_message(
                message, COMMAND_USAGE["clone"][0], COMMAND_USAGE["clone"][1]
            )
    elif data[1] == "mirror":
        buttons = ButtonMaker()
        buttons.data_button("Back", "help back m")
        button = buttons.build_menu()
        await edit_message(message, MIRROR_HELP_DICT[data[2]], button)
    elif data[1] == "yt":
        buttons = ButtonMaker()
        buttons.data_button("Back", "help back y")
        button = buttons.build_menu()
        await edit_message(message, YT_HELP_DICT[data[2]], button)
    elif data[1] == "clone":
        buttons = ButtonMaker()
        buttons.data_button("Back", "help back c")
        button = buttons.build_menu()
        await edit_message(message, CLONE_HELP_DICT[data[2]], button)


@new_task
async def bot_help(_, message):
    text = message.text.split(maxsplit=1)
    if len(text) > 1:
        query = text[1].strip().lower()
        category_key = HELP_CATEGORY_ALIASES.get(query)
        if category_key:
            await send_message(
                message, build_help_category_text(category_key), _help_back_buttons()
            )
            return
        await send_message(message, search_help(query), _help_back_buttons())
        return

    await send_message(message, help_string, _help_menu_buttons())
