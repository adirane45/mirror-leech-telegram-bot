import asyncio
from os import remove as os_remove
from typing import Any

from aiofiles import open as aiopen


def filter_links(links_list: list[str], bulk_start: int, bulk_end: int) -> list[str]:
    start = bulk_start if bulk_start > 0 else None
    end = bulk_end if bulk_end > 0 else None
    return links_list[start:end]


def get_links_from_message(text: str) -> list[str]:
    links_list = text.split("\n")
    return [item.strip() for item in links_list if len(item) != 0]


async def get_links_from_file(message: Any) -> list[str]:
    links_list: list[str] = []
    text_file_dir = await message.download()
    async with aiopen(text_file_dir, "r+") as f:
        lines = await f.readlines()
        links_list.extend(line.strip() for line in lines if len(line) != 0)
    await asyncio.to_thread(os_remove, text_file_dir)
    return links_list


async def extract_bulk_links(message: Any, bulk_start: int | str, bulk_end: int | str) -> list[str]:
    bulk_start = int(bulk_start)
    bulk_end = int(bulk_end)
    links_list: list[str] = []
    if reply_to := message.reply_to_message:
        if (file_ := reply_to.document) and (file_.mime_type == "text/plain"):
            links_list = await get_links_from_file(reply_to)
        elif text := reply_to.text:
            links_list = get_links_from_message(text)
    return filter_links(links_list, bulk_start, bulk_end) if links_list else links_list
