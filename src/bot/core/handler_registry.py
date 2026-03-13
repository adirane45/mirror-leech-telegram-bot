from pyrogram.handlers import CallbackQueryHandler, EditedMessageHandler, MessageHandler  # type: ignore[attr-defined]
from typing import Any


def register_message(
    bot: Any,
    callback: Any,
    *,
    filters: Any,
    group: int | None = None,
) -> None:
    handler = MessageHandler(callback, filters=filters)
    if group is None:
        bot.add_handler(handler)
    else:
        bot.add_handler(handler, group=group)


def register_callback(
    bot: Any,
    callback: Any,
    *,
    filters: Any,
    group: int | None = None,
) -> None:
    handler = CallbackQueryHandler(callback, filters=filters)
    if group is None:
        bot.add_handler(handler)
    else:
        bot.add_handler(handler, group=group)


def register_edited(
    bot: Any,
    callback: Any,
    *,
    filters: Any,
    group: int | None = None,
) -> None:
    handler = EditedMessageHandler(callback, filters=filters)
    if group is None:
        bot.add_handler(handler)
    else:
        bot.add_handler(handler, group=group)
