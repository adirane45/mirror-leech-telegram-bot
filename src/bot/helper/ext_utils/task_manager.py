from asyncio import Event

from ... import LOGGER, non_queued_dl, non_queued_up, queue_dict_lock, queued_dl, queued_up
from ...core.config_manager import Config
from ..mirror_leech_utils.gdrive_utils.search import GoogleDriveSearch
from .bot_utils import get_telegraph_list, sync_to_async
from .files_utils import get_base_name
from .links_utils import is_gdrive_id


async def stop_duplicate_check(listener):
    if _should_skip_duplicate_check(listener):
        return False, None

    name = listener.name
    LOGGER.info(f"Checking File/Folder if already in Drive: {name}")

    name = _get_duplicate_check_name(listener, name)

    if name is not None:
        telegraph_content, contents_no = await sync_to_async(
            GoogleDriveSearch(stop_dup=True, no_multi=listener.is_clone).drive_list,
            name,
            listener.up_dest,
            listener.user_id,
        )
        if telegraph_content:
            msg = f"File/Folder is already available in Drive.\nHere are {contents_no} list results:"
            button = await get_telegraph_list(telegraph_content)
            return msg, button

    return False, None


def _should_skip_duplicate_check(listener):
    return (
        listener.is_leech
        or not listener.stop_duplicate
        or listener.same_dir
        or listener.select
        or not is_gdrive_id(listener.up_dest)
    )


def _get_duplicate_check_name(listener, name):
    if listener.compress:
        return f"{name}.zip"
    elif listener.extract:
        try:
            return get_base_name(name)
        except:
            return None
    return name


def _should_skip_queue_limits(listener, state: str):
    return (
        listener.force_run
        or (listener.force_upload and state == "up")
        or (listener.force_download and state == "dl")
    )


def _is_queue_over_limit(state: str, all_limit: int, state_limit: int):
    dl_count = len(non_queued_dl)
    up_count = len(non_queued_up)
    t_count = dl_count if state == "dl" else up_count
    return (
        all_limit
        and dl_count + up_count >= all_limit
        and (not state_limit or t_count >= state_limit)
    ) or (state_limit and t_count >= state_limit)


def _add_to_waiting_queue(listener, state: str):
    event = Event()
    if state == "dl":
        queued_dl[listener.mid] = event
    else:
        queued_up[listener.mid] = event
    return event


def _add_to_running_queue(listener, state: str):
    if state == "up":
        non_queued_up.add(listener.mid)
    else:
        non_queued_dl.add(listener.mid)


async def check_running_tasks(listener, state="dl"):
    all_limit = Config.QUEUE_ALL
    state_limit = Config.QUEUE_DOWNLOAD if state == "dl" else Config.QUEUE_UPLOAD
    event = None
    is_over_limit = False
    async with queue_dict_lock:
        if state == "up" and listener.mid in non_queued_dl:
            non_queued_dl.remove(listener.mid)
        if (all_limit or state_limit) and not _should_skip_queue_limits(listener, state):
            is_over_limit = _is_queue_over_limit(state, all_limit, state_limit)
            if is_over_limit:
                event = _add_to_waiting_queue(listener, state)
        if not is_over_limit:
            _add_to_running_queue(listener, state)

    return is_over_limit, event


async def start_dl_from_queued(mid: int):
    queued_dl[mid].set()
    del queued_dl[mid]
    non_queued_dl.add(mid)


async def start_up_from_queued(mid: int):
    queued_up[mid].set()
    del queued_up[mid]
    non_queued_up.add(mid)


def _resolve_capacity(limit, current, fallback):
    if limit:
        return max(0, min(fallback, limit - current))
    return fallback


async def _start_with_capacity(queue_store, start_func, capacity):
    started = 0
    if capacity <= 0:
        return started
    for mid in list(queue_store.keys()):
        await start_func(mid)
        started += 1
        if started >= capacity:
            break
    return started


async def _start_with_limit(queue_store, start_func, limit, current):
    if not queue_store:
        return
    if not limit:
        await _start_with_capacity(queue_store, start_func, len(queue_store))
        return
    await _start_with_capacity(queue_store, start_func, max(0, limit - current))


async def _start_with_all_limit(all_limit, dl_limit, up_limit):
    async with queue_dict_lock:
        dl = len(non_queued_dl)
        up = len(non_queued_up)
        running_total = dl + up
        if running_total >= all_limit:
            return

        free_tasks = all_limit - running_total
        up_capacity = _resolve_capacity(up_limit, up, free_tasks)
        started_up = await _start_with_capacity(queued_up, start_up_from_queued, up_capacity)

        free_tasks -= started_up
        if free_tasks <= 0:
            return

        dl_capacity = _resolve_capacity(dl_limit, dl, free_tasks)
        await _start_with_capacity(queued_dl, start_dl_from_queued, dl_capacity)


async def start_from_queued():
    if all_limit := Config.QUEUE_ALL:
        await _start_with_all_limit(
            all_limit,
            Config.QUEUE_DOWNLOAD,
            Config.QUEUE_UPLOAD,
        )
        return

    async with queue_dict_lock:
        await _start_with_limit(
            queued_up,
            start_up_from_queued,
            Config.QUEUE_UPLOAD,
            len(non_queued_up),
        )
        await _start_with_limit(
            queued_dl,
            start_dl_from_queued,
            Config.QUEUE_DOWNLOAD,
            len(non_queued_dl),
        )
