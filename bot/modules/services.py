from time import time

from ..helper.ext_utils.bot_utils import new_task
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.message_utils import send_message, edit_message, send_file
from ..helper.telegram_helper.filters import CustomFilters
from ..helper.telegram_helper.bot_commands import BotCommands


@new_task
async def start(_, message):
    buttons = ButtonMaker()
    buttons.url_button(
        "Repo", "https://www.github.com/adirane45/mirror-leech-telegram-bot"
    )
    buttons.url_button("Code Owner", "https://t.me/anas_tayyar")
    buttons.data_button("Get Started", "onboard start")
    buttons.data_button("Help Menu", "help menu")
    buttons.data_button("Settings", "quick_settings")
    reply_markup = buttons.build_menu(2)
    if await CustomFilters.authorized(_, message):
        start_string = f"""
This bot can mirror from links|tgfiles|torrents|nzb|rclone-cloud to any rclone cloud, Google Drive or to telegram.
Type /{BotCommands.HelpCommand} to open the command menu
"""
        await send_message(message, start_string, reply_markup)
    else:
        await send_message(
            message,
            "This bot can mirror from links|tgfiles|torrents|nzb|rclone-cloud to any rclone cloud, Google Drive or to telegram.\n\n⚠️ You Are not authorized user! Deploy your own mirror-leech bot",
            reply_markup,
        )


@new_task
async def ping(_, message):
    start_time = int(round(time() * 1000))
    reply = await send_message(message, "Starting Ping")
    end_time = int(round(time() * 1000))
    await edit_message(reply, f"{end_time - start_time} ms")


@new_task
async def log(_, message):
    await send_file(message, "log.txt")


@new_task
async def onboarding_callback(_, query):
    data = query.data.split()
    message = query.message

    if len(data) < 2:
        await query.answer()
        return

    step = data[1]
    buttons = ButtonMaker()

    if step == "start":
        text = (
            "<b>🚀 Getting Started</b>\n\n"
            "1) Send a link with /mirror or /leech\n"
            "2) Set your default upload destination\n"
            "3) Track tasks with /status\n\n"
            "Pick a step below."
        )
        buttons.data_button("Mirror a Link", "onboard mirror")
        buttons.data_button("Leech to Telegram", "onboard leech")
        buttons.data_button("Set Upload", "onboard settings")
        buttons.data_button("Help Menu", "help menu", position="footer")
        buttons.data_button("Close", "help close", position="footer")
        await edit_message(message, text, buttons.build_menu(2))
        await query.answer()
        return

    if step == "mirror":
        text = (
            "<b>📥 Mirror a Link</b>\n\n"
            "Use: <code>/mirror [link]</code>\n"
            "Tip: /dl is a short alias.\n\n"
            "Reply to a link or file to mirror it."
        )
    elif step == "leech":
        text = (
            "<b>📤 Leech to Telegram</b>\n\n"
            "Use: <code>/leech [link]</code>\n"
            "Tip: /ul is a short alias.\n\n"
            "Reply to a link or file to leech it."
        )
    elif step == "settings":
        text = (
            "<b>⚙️ Set Your Defaults</b>\n\n"
            f"Open user settings: <code>/{BotCommands.UserSetCommand[0]}</code>\n"
            "Pick your default upload target and preferences."
        )
    else:
        await query.answer()
        return

    buttons.data_button("Back", "onboard start")
    buttons.data_button("Help Menu", "help menu")
    buttons.data_button("Close", "help close")
    await edit_message(message, text, buttons.build_menu(2))
    await query.answer()
