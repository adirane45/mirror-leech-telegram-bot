from time import time

from ..helper.ext_utils.bot_utils import new_task
from ..helper.ext_utils.files_utils import get_mime_type
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.message_utils import send_message, edit_message, send_file
from ..helper.telegram_helper.filters import CustomFilters
from ..helper.telegram_helper.bot_commands import BotCommands
from ..core.config_manager import Config
from ..core.stream_proxy import stream_proxy


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
    await send_file(message, "data/logs/log.txt")


def _extract_stream_media(message):
    media = (
        message.document
        or message.video
        or message.audio
        or message.photo
        or message.animation
    )
    if not media:
        return None, None, None
    file_id = media.file_id
    file_name = getattr(media, "file_name", None) or "download"
    file_type = media.__class__.__name__.lower()
    return file_id, file_name, file_type


@new_task
async def stream_link(_, message):
    if not await CustomFilters.authorized(_, message):
        return

    reply = message.reply_to_message
    if reply:
        file_id, file_name, file_type = _extract_stream_media(reply)
    else:
        file_id = None
        file_name = None
        file_type = None

    if not file_id:
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            file_id = parts[1].strip()
            file_name = "download"
            file_type = "document"

    if not file_id:
        usage = f"Usage: /{BotCommands.StreamLinkCommand[0]} <file_id> or reply to a file"
        await send_message(message, usage)
        return

    mime_type = "application/octet-stream"
    if reply and reply.document and reply.document.file_name:
        mime_type = get_mime_type(reply.document.file_name)

    token = await stream_proxy.create_token(
        file_id=file_id,
        file_name=file_name or "download",
        file_type=file_type or "document",
        mime_type=mime_type,
    )

    if not token:
        await send_message(message, "Stream links are disabled.")
        return

    link = stream_proxy.build_url(token.token)
    ttl_minutes = int(getattr(Config, "STREAM_LINK_TTL_SECONDS", 1800) / 60)
    text = (
        "<b>🔗 Stream Link Generated</b>\n\n"
        f"Link: <code>{link}</code>\n"
        f"Expires in: {ttl_minutes} minutes\n"
        "Share this link to download the file."
    )
    await send_message(message, text)


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
