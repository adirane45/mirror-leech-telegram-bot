from asyncio import TimeoutError, sleep
from time import time

from aiofiles.os import path as aiopath
from aiofiles.os import remove
from aiohttp.client_exceptions import ClientError

from ... import LOGGER, intervals, task_dict, task_dict_lock
from ...core.config_manager import Config
from ...core.torrent_manager import TorrentManager, aria2_name, is_metadata
from ..ext_utils.bot_utils import bt_selection_buttons
from ..ext_utils.files_utils import clean_unwanted
from ..ext_utils.status_utils import get_task_by_gid
from ..ext_utils.task_manager import stop_duplicate_check
from ..mirror_leech_utils.status_utils.aria2_status import Aria2Status
from ..telegram_helper.message_utils import delete_message, send_message, update_status_message


async def _handle_metadata_start(api, gid, download):
    LOGGER.info(f"onDownloadStarted: {gid} METADATA")
    await sleep(1)
    if not (task := await get_task_by_gid(gid)):
        return

    task.listener.is_torrent = True
    if not task.listener.select:
        return

    metamsg = "Downloading Metadata, wait then you can select files. Use torrent file to avoid this wait."
    meta = await send_message(task.listener.message, metamsg)
    while True:
        await sleep(0.5)
        if download.get("status", "") == "removed" or download.get("followedBy", []):
            await delete_message(meta)
            break
        download = await api.tellStatus(gid)


async def _handle_regular_start(api, gid, download):
    LOGGER.info(f"onDownloadStarted: {aria2_name(download)} - Gid: {gid}")
    await sleep(1)
    await sleep(2)

    if not (task := await get_task_by_gid(gid)):
        return

    download = await api.tellStatus(gid)
    if "bittorrent" in download:
        task.listener.is_torrent = True
    task.listener.name = aria2_name(download)
    msg, button = await stop_duplicate_check(task.listener)
    if msg:
        await TorrentManager.aria2_remove(download)
        await task.listener.on_download_error(msg, button)


async def _on_download_started(api, data):
    gid = data["params"][0]["gid"]
    download = await api.tellStatus(gid)
    options = await api.getOption(gid)
    if options.get("follow-torrent", "") == "false":
        return
    if is_metadata(download):
        await _handle_metadata_start(api, gid, download)
        return

    await _handle_regular_start(api, gid, download)


async def _handle_followed_download(api, download, gid):
    """Handle torrent that was followed (metadata download)"""
    new_gid = download.get("followedBy", [])[0]
    LOGGER.info(f"Gid changed from {gid} to {new_gid}")
    
    task = await get_task_by_gid(new_gid)
    if not task:
        return
    
    task.listener.is_torrent = True
    if Config.BASE_URL and task.listener.select:
        if not task.queued:
            await api.forcePause(new_gid)
        SBUTTONS = bt_selection_buttons(new_gid)
        msg = "Your download paused. Choose files then press Done Selecting button to start downloading."
        await send_message(task.listener.message, msg, SBUTTONS)

async def _handle_bittorrent_download(download, gid):
    """Handle bittorrent download completion"""
    task = await get_task_by_gid(gid)
    if not task:
        return
    
    task.listener.is_torrent = True
    if hasattr(task, "seeding") and task.seeding:
        LOGGER.info(f"Cancelling Seed: {aria2_name(download)} onDownloadComplete")
        await TorrentManager.aria2_remove(download)
        await task.listener.on_upload_error(
            f"Seeding stopped with Ratio: {task.ratio()} and Time: {task.seeding_time()}"
        )

async def _handle_regular_download(download, gid):
    """Handle regular (non-bittorrent) download completion"""
    LOGGER.info(f"onDownloadComplete: {aria2_name(download)} - Gid: {gid}")
    task = await get_task_by_gid(gid)
    
    if not task:
        return
    
    await task.listener.on_download_complete()
    if not intervals["stopAll"]:
        await TorrentManager.aria2_remove(download)

async def _on_download_complete(api, data):
    try:
        gid = data["params"][0]["gid"]
        download = await api.tellStatus(gid)
        options = await api.getOption(gid)
    except (TimeoutError, ClientError, Exception) as e:
        LOGGER.error(f"onDownloadComplete: {e}")
        return
    
    if options.get("follow-torrent", "") == "false":
        return
    
    if download.get("followedBy", []):
        await _handle_followed_download(api, download, gid)
    elif "bittorrent" in download:
        await _handle_bittorrent_download(download, gid)
    else:
        await _handle_regular_download(download, gid)


async def _cleanup_unselected_files(download):
    """Remove unselected files from selective download."""
    res = download.get("files", [])
    for file_o in res:
        f_path = file_o.get("path", "")
        if file_o.get("selected", "") != "true" and await aiopath.exists(f_path):
            try:
                await remove(f_path)
            except:
                pass
    await clean_unwanted(download.get("dir", ""))


async def _configure_seed_or_pause(api, gid, should_seed):
    """Configure seeding options or pause download."""
    if should_seed:
        try:
            await api.changeOption(gid, {"max-upload-limit": "0"})
        except (TimeoutError, ClientError, Exception) as e:
            LOGGER.error(
                f"{e} You are not able to seed because you added global option seed-time=0 without adding specific seed_time for this torrent GID: {gid}"
            )
    else:
        try:
            await api.forcePause(gid)
        except (TimeoutError, ClientError, Exception) as e:
            LOGGER.error(f"onBtDownloadComplete: {e} GID: {gid}")


async def _handle_seeding_completion(task, api, download, gid):
    """Handle seeding state after download completion."""
    if not task.listener.seed:
        await TorrentManager.aria2_remove(download)
        return

    download = await api.tellStatus(gid)
    task_exists = await get_task_by_gid(gid)
    
    if download.get("status", "") == "complete" and task_exists:
        LOGGER.info(f"Cancelling Seed: {aria2_name(download)}")
        await TorrentManager.aria2_remove(download)
        await task.listener.on_upload_error(
            f"Seeding stopped with Ratio: {task.ratio()} and Time: {task.seeding_time()}"
        )
    elif download.get("status", "") == "complete" and not task_exists:
        pass  # Task already removed
    elif not task.listener.is_cancelled:
        async with task_dict_lock:
            if task.listener.mid not in task_dict:
                await TorrentManager.aria2_remove(download)
                return
            task_dict[task.listener.mid] = Aria2Status(task.listener, gid, True)
            task_dict[task.listener.mid].start_time = time()
        LOGGER.info(f"Seeding started: {aria2_name(download)} - Gid: {gid}")
        await update_status_message(task.listener.message.chat.id)
    else:
        await TorrentManager.aria2_remove(download)


async def _on_bt_download_complete(api, data):
    gid = data["params"][0]["gid"]
    await sleep(1)
    download = await api.tellStatus(gid)
    LOGGER.info(f"onBtDownloadComplete: {aria2_name(download)} - Gid: {gid}")
    
    if task := await get_task_by_gid(gid):
        task.listener.is_torrent = True
        
        if task.listener.select:
            await _cleanup_unselected_files(download)
        
        await _configure_seed_or_pause(api, gid, task.listener.seed)
        await task.listener.on_download_complete()
        
        if intervals["stopAll"]:
            return
        
        await _handle_seeding_completion(task, api, download, gid)


async def _on_download_stopped(_, data):
    gid = data["params"][0]["gid"]
    await sleep(4)
    if task := await get_task_by_gid(gid):
        await task.listener.on_download_error("Dead torrent!")


async def _on_download_error(api, data):
    gid = data["params"][0]["gid"]
    await sleep(1)
    LOGGER.info(f"onDownloadError: {gid}")
    error = "None"
    try:
        download = await api.tellStatus(gid)
        options = await api.getOption(gid)
        error = download.get("errorMessage", "")
        LOGGER.info(f"Download Error: {error}")
        if options.get("follow-torrent", "") == "false":
            return
    except (TimeoutError, ClientError, Exception):
        return
    if task := await get_task_by_gid(gid):
        await task.listener.on_download_error(error)


def add_aria2_callbacks():
    TorrentManager.aria2.onBtDownloadComplete(_on_bt_download_complete)
    TorrentManager.aria2.onDownloadComplete(_on_download_complete)
    TorrentManager.aria2.onDownloadError(_on_download_error)
    TorrentManager.aria2.onDownloadStart(_on_download_started)
    TorrentManager.aria2.onDownloadStop(_on_download_stopped)
