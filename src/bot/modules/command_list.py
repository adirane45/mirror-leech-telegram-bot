import os
from tempfile import NamedTemporaryFile
from typing import List, Tuple

from ..helper.ext_utils.bot_utils import new_task
from ..helper.ext_utils.help_messages import HELP_CATEGORIES, HELP_CATEGORY_ORDER, format_command, format_shortcuts
from ..helper.telegram_helper.bot_commands import BotCommands
from ..helper.telegram_helper.message_utils import send_file, send_message


def _primary_command(cmd) -> str:
    if isinstance(cmd, (list, tuple)):
        return cmd[0]
    return cmd


def _build_command_lines() -> Tuple[str, str]:
    """Return (chat_text, botfather_text)."""
    seen = set()
    botfather_lines: List[str] = []
    chat_lines: List[str] = ["<b>All Commands</b>", ""]

    for category_key in HELP_CATEGORY_ORDER:
        category = HELP_CATEGORIES[category_key]
        chat_lines.append(f"<b>{category['title']}</b>")
        for item in category["items"]:
            cmd_text = format_command(item["cmd"])
            shortcuts = format_shortcuts(item["cmd"])
            desc = item["desc"].strip()
            if shortcuts:
                chat_lines.append(f"- {cmd_text} ({shortcuts}) - {desc}")
            else:
                chat_lines.append(f"- {cmd_text} - {desc}")
            usage = item.get("usage")
            example = item.get("example")
            if usage:
                chat_lines.append(f"  Usage: {usage}")
            if example:
                chat_lines.append(f"  Example: {example}")

            primary = _primary_command(item["cmd"])
            if primary not in seen:
                seen.add(primary)
                botfather_lines.append(f"{primary} - {desc}")
        chat_lines.append("")

    chat_text = "\n".join(chat_lines).strip()
    botfather_text = "\n".join(botfather_lines).strip()
    return chat_text, botfather_text


async def _send_chunked_text(message, text: str, limit: int = 3800) -> None:
    if len(text) <= limit:
        await send_message(message, text)
        return

    parts = []
    current = []
    current_len = 0
    for line in text.split("\n"):
        line_len = len(line) + 1
        if current_len + line_len > limit and current:
            parts.append("\n".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += line_len
    if current:
        parts.append("\n".join(current))

    for part in parts:
        await send_message(message, part)


@new_task
async def command_list(_, message):
    chat_text, botfather_text = _build_command_lines()

    if not chat_text:
        await send_message(message, "No commands available.")
        return

    await _send_chunked_text(message, chat_text)

    with NamedTemporaryFile("w", suffix=".txt", delete=False) as temp:
        temp.write(botfather_text)
        temp_path = temp.name

    caption = (
        f"BotFather format for /{BotCommands.CommandListCommand[0]} "
        "(use /setcommands)."
    )
    await send_file(message, temp_path, caption=caption)
    try:
        os.unlink(temp_path)
    except OSError:
        pass
