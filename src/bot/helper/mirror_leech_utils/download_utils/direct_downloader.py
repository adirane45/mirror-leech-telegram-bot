from secrets import token_urlsafe

from .... import LOGGER, task_dict, task_dict_lock
from ...ext_utils.task_manager import check_running_tasks, stop_duplicate_check
from ...listeners.direct_listener import DirectListener
from ...mirror_leech_utils.status_utils.direct_status import DirectStatus
from ...mirror_leech_utils.status_utils.queue_status import QueueStatus
from ...telegram_helper.message_utils import send_status_message


async def _prepare_direct_download_details(listener):
    details = listener.link
    contents = details.get("contents")
    if not contents:
        await listener.on_download_error("There is nothing to download!")
        return None, None

    listener.size = details["total_size"]
    if not listener.name:
        listener.name = details["title"]
    return details, contents


async def _handle_direct_duplicate_check(listener):
    msg, button = await stop_duplicate_check(listener)
    if not msg:
        return True
    await listener.on_download_error(msg, button)
    return False


async def _wait_direct_queue_if_needed(listener, gid, add_to_queue, event):
    if not add_to_queue:
        return True

    LOGGER.info(f"Added to Queue/Download: {listener.name}")
    async with task_dict_lock:
        task_dict[listener.mid] = QueueStatus(listener, gid, "dl")
    await listener.on_download_start()
    if listener.multi <= 1 and not listener.is_rss:
        await send_status_message(listener.message)
    await event.wait()
    return not listener.is_cancelled


def _build_direct_download_options(details):
    a2c_opt = {"follow-torrent": "false", "follow-metalink": "false"}
    if header := details.get("header"):
        a2c_opt["header"] = header
    return a2c_opt


async def _announce_direct_download_start(listener, add_to_queue):
    if add_to_queue:
        LOGGER.info(f"Start Queued Download from Direct Download: {listener.name}")
        return

    LOGGER.info(f"Download from Direct Download: {listener.name}")
    await listener.on_download_start()
    if listener.multi <= 1 and not listener.is_rss:
        await send_status_message(listener.message)


async def add_direct_download(listener, path):
    details, contents = await _prepare_direct_download_details(listener)
    if not details:
        return

    path = f"{path}/{listener.name}"

    if not await _handle_direct_duplicate_check(listener):
        return

    gid = token_urlsafe(10)
    add_to_queue, event = await check_running_tasks(listener)
    if not await _wait_direct_queue_if_needed(listener, gid, add_to_queue, event):
        return

    a2c_opt = _build_direct_download_options(details)
    directListener = DirectListener(path, listener, a2c_opt)

    async with task_dict_lock:
        task_dict[listener.mid] = DirectStatus(listener, directListener, gid)

    await _announce_direct_download_start(listener, add_to_queue)

    await directListener.download(contents)
