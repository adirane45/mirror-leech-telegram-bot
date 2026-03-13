from ..helper.ext_utils.bot_utils import COMMAND_USAGE, new_task
from ..helper.ext_utils.help_messages import (
    CLONE_HELP_DICT,
    HELP_CATEGORIES,
    HELP_CATEGORY_ALIASES,
    HELP_CATEGORY_ORDER,
    MIRROR_HELP_DICT,
    YT_HELP_DICT,
    build_help_category_text,
    build_help_home_text,
    help_string,
    search_help,
)
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.message_utils import delete_message, edit_message, send_message


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
    action = data[1]
    if action == "close":
        await delete_message(message)
        return
    if action == "menu":
        await edit_message(message, build_help_home_text(), _help_menu_buttons())
        return
    if action == "cat":
        await _show_help_category(message, data[2])
        return
    if action == "search":
        await _show_help_search(message)
        return
    if action == "back":
        await _show_help_back(message, data[2])
        return

    help_maps = {
        "mirror": (MIRROR_HELP_DICT, "m"),
        "yt": (YT_HELP_DICT, "y"),
        "clone": (CLONE_HELP_DICT, "c"),
    }
    if action in help_maps:
        data_map, back_key = help_maps[action]
        await _show_help_topic(message, data_map[data[2]], back_key)


async def _show_help_category(message, category_key):
    await edit_message(message, build_help_category_text(category_key), _help_back_buttons())


async def _show_help_search(message):
    await edit_message(
        message,
        "<b>🔎 Search Help</b>\n\nType <code>/help keyword</code> to search commands.",
        _help_back_buttons(),
    )


async def _show_help_back(message, back_key):
    usage_map = {
        "m": "mirror",
        "y": "yt",
        "c": "clone",
    }
    usage_key = usage_map.get(back_key)
    if usage_key:
        await edit_message(message, COMMAND_USAGE[usage_key][0], COMMAND_USAGE[usage_key][1])


async def _show_help_topic(message, text, back_key):
    buttons = ButtonMaker()
    buttons.data_button("Back", f"help back {back_key}")
    await edit_message(message, text, buttons.build_menu())


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
