from ..helper.ext_utils.bot_utils import new_task
from ..helper.ext_utils.links_utils import is_url
from ..helper.telegram_helper.bot_commands import BotCommands
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.message_utils import send_message
from ..core.link_bypassers import LinkBypassEngine


BYPASS_ENGINE = LinkBypassEngine(enabled=True)


def _extract_link_from_message(message) -> str:
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        return args[1].strip()

    reply = message.reply_to_message
    if reply and reply.text:
        return reply.text.split("\n", 1)[0].strip().split(maxsplit=1)[0]

    return ""


@new_task
async def bypass_link(_, message):
    link = _extract_link_from_message(message)

    if not link or not is_url(link):
        usage = (
            f"Usage: /{BotCommands.BypassCommand[0]} <url>\\n"
            f"Or reply to a message containing a URL with /{BotCommands.BypassCommand[0]}"
        )
        await send_message(message, usage)
        return

    result = await BYPASS_ENGINE.normalize_link(link)

    response = (
        "<b>🔓 URL Bypass Result</b>\n\n"
        f"<b>Input:</b> <code>{result.original_url}</code>\n"
        f"<b>Final:</b> <code>{result.final_url}</code>\n"
        f"<b>Service:</b> <code>{result.service}</code>\n"
        f"<b>Status:</b> {'Bypassed' if result.bypassed else 'No redirect found'}"
    )

    buttons = ButtonMaker()
    if is_url(result.original_url):
        buttons.url_button("📥 Open Input URL", result.original_url)
    if is_url(result.final_url):
        buttons.url_button("🔗 Open Final URL", result.final_url)
    await send_message(message, response, buttons.build_menu(2))
