from asyncio import TimeoutError, sleep

from aiofiles import open as aiopen
from aiofiles.os import path as aiopath
from aiofiles.os import remove
from aiohttp.client_exceptions import ClientError
from aioqbt.api import AddFormBuilder
from aioqbt.exc import AQError

from .... import LOGGER, qb_torrents, task_dict, task_dict_lock
from ....core.config_manager import Config
from ....core.torrent_manager import TorrentManager
from ...ext_utils.bot_utils import bt_selection_buttons
from ...ext_utils.task_manager import check_running_tasks
from ...listeners.qbit_listener import on_download_start
from ...mirror_leech_utils.status_utils.qbit_status import QbittorrentStatus
from ...telegram_helper.message_utils import delete_message, send_message, send_status_message

"""
Only v1 torrents
#from hashlib import sha1
#from base64 import b16encode, b32decode
#from bencoding import bencode, bdecode
#from re import search as re_search
def _get_hash_magnet(mgt: str):
    hash_ = re_search(r'(?<=xt=urn:btih:)[a-zA-Z0-9]+', mgt).group(0)
    if len(hash_) == 32:
        hash_ = b16encode(b32decode(hash_.upper())).decode()
    return hash_

def _get_hash_file(fpath):
    with open(fpath, "rb") as f:
        decodedDict = bdecode(f.read())
        return sha1(bencode(decodedDict[b'info'])).hexdigest()
"""


def _map_download_path(path: str) -> str:
    if path.startswith("/app/downloads"):
        return path.replace("/app/downloads", "/downloads", 1)
    return path


def _get_aq_error_message(error: AQError) -> str:
    error_str = str(error).lower()
    full_error = str(error)
    if "403" in full_error or "forbidden" in error_str:
        error_msg = "❌ <b>HTTP 403 Forbidden Error</b>\n\n"
        error_msg += "<b>The torrent source rejected your download request.</b>\n\n"
        error_msg += "<b>🔍 Common Causes:</b>\n"
        error_msg += "• Source is geo-blocked or region-restricted\n"
        error_msg += "• Your IP is rate-limited by the source\n"
        error_msg += "• The source requires authentication/cookies\n"
        error_msg += "• The torrent file/magnet is no longer available\n"
        error_msg += "• qBittorrent lacks proper User-Agent header\n\n"
        error_msg += "<b>✅ Solutions to Try:</b>\n"
        error_msg += "1️⃣ <b>Wait & Retry</b> - Try again in 5-10 minutes\n"
        error_msg += "2️⃣ <b>Different Source</b> - Use another torrent source\n"
        error_msg += "3️⃣ <b>Verify Link</b> - Check if the link still works\n"
        error_msg += "4️⃣ <b>Use /mirror</b> - Try downloading with /mirror command instead\n"
        error_msg += "5️⃣ <b>Direct .torrent</b> - Download torrent file first, then upload\n\n"
        error_msg += f"<b>Error Details:</b> <code>{full_error}</code>"
        return error_msg
    if "401" in full_error or "unauthorized" in error_str:
        return (
            "❌ <b>HTTP 401 Unauthorized</b>\n\n"
            "The torrent source requires authentication.\n"
            "This source may need login credentials or API key."
        )
    if "already" in error_str or "exists" in error_str:
        return (
            "⚠️  <b>Torrent Already Added</b>\n\n"
            "This torrent/magnet link is already in qBittorrent.\n"
            "Check ongoing downloads or use /stats to see queue."
        )
    if "invalid" in error_str or "bad" in error_str:
        return (
            "❌ <b>Invalid Torrent Link</b>\n\n"
            "The link format is not recognized.\n"
            "<b>Supported formats:</b>\n"
            "• Magnet link: magnet:?xt=urn:btih:...\n"
            "• Torrent URL: https://example.com/file.torrent\n"
            "• Torrent file upload: Reply with .torrent file"
        )
    return f"❌ <b>qBittorrent Error</b>\n\n{error}"


def _get_add_request_error_message(error: Exception) -> str:
    error_str = str(error).lower()
    if "timeout" in error_str or "timed out" in error_str:
        return "⏱️  Connection to qBittorrent timed out. Ensure qBittorrent service is running."
    if "connection" in error_str or "connect" in error_str:
        return "🔴 Cannot connect to qBittorrent service. Please check if it's running."
    if "403" in str(error):
        return (
            "❌ <b>HTTP 403 Forbidden</b>\n\n"
            "The server rejected the download request.\n"
            "This usually means the source is blocking access.\n\n"
            "<b>Try:</b>\n"
            "• Waiting and retrying later\n"
            "• Using a different torrent source\n"
            "• Verifying the torrent link is valid"
        )
    if "already added" in error_str:
        return "⚠️  This torrent/magnet already exists in qBittorrent."
    return f"❌ qBittorrent error: {error}. Link may be unsupported or incorrect."


def _get_outer_error_message(error: Exception) -> str:
    error_str = str(error).lower()
    full_error = str(error)
    if "403" in full_error or "forbidden" in error_str:
        return (
            "❌ <b>HTTP 403 Forbidden</b>\n\n"
            "Access denied by the torrent source.\n"
            "The server is blocking this download.\n\n"
            "<b>Try:</b>\n"
            "• Wait a few minutes and retry\n"
            "• Use a different torrent/magnet link\n"
            "• Use /mirror command instead of /qm\n"
            "• Check if your IP is rate-limited"
        )
    if "timeout" in error_str or "timed out" in error_str:
        return (
            "⏱️  <b>Connection Timeout</b>\n\n"
            "Took too long to connect to torrent source.\n"
            "The server may be slow or unreachable.\n\n"
            "<b>Try:</b>\n"
            "• Wait a moment and retry\n"
            "• Check your internet connection\n"
            "• Try a different torrent source"
        )
    if "connection" in error_str or "cannot connect" in error_str:
        return (
            "🔴 <b>qBittorrent Connection Failed</b>\n\n"
            "Cannot reach qBittorrent service.\n"
            "Please ensure qBittorrent is running.\n\n"
            f"Debug: {full_error}"
        )
    if "already" in error_str:
        return "⚠️  <b>Torrent Already Added</b>\n\nThis torrent is already in qBittorrent."
    return f"❌ <b>qBittorrent Error:</b>\n<code>{full_error}</code>"


async def _wait_for_torrent_info(listener, add_to_queue, event):
    tor_info = await TorrentManager.qbittorrent.torrents.info(tag=f"{listener.mid}")
    while len(tor_info) == 0:
        if add_to_queue and event is not None and event.is_set():
            add_to_queue = False
        await sleep(1)
        tor_info = await TorrentManager.qbittorrent.torrents.info(tag=f"{listener.mid}")
    return tor_info[0], add_to_queue


async def _wait_for_magnet_metadata(listener):
    metamsg = "Downloading Metadata, wait then you can select files. Use torrent file to avoid this wait."
    meta = await send_message(listener.message, metamsg)
    while True:
        tor_info = await TorrentManager.qbittorrent.torrents.info(tag=f"{listener.mid}")
        if len(tor_info) == 0:
            await delete_message(meta)
            return None
        try:
            tor_info = tor_info[0]
            if tor_info.state not in ["metaDL", "checkingResumeData", "stoppedDL"]:
                await delete_message(meta)
                return tor_info
        except Exception:
            await delete_message(meta)
            return None


async def _handle_selection_or_status(listener, tor_info, add_to_queue):
    if Config.BASE_URL and listener.select:
        if listener.link.startswith("magnet:"):
            tor_info = await _wait_for_magnet_metadata(listener)
            if tor_info is None:
                return None

        ext_hash = tor_info.hash
        if not add_to_queue:
            await TorrentManager.qbittorrent.torrents.stop([ext_hash])
        buttons = bt_selection_buttons(ext_hash)
        msg = "Your download paused. Choose files then press Done Selecting button to start downloading."
        await send_message(listener.message, msg, buttons)
        return tor_info

    if listener.multi <= 1 and not listener.is_rss:
        await send_status_message(listener.message)
    return tor_info


async def add_qb_torrent(listener, path, ratio, seed_time):
    path = _map_download_path(path)
    try:
        form = await _build_torrent_form(listener, path, ratio, seed_time)
        if form is None:
            return
        
        add_to_queue, event = await check_running_tasks(listener)
        tor_info = await _add_and_wait_for_torrent(listener, form, add_to_queue, event)
        if tor_info is None:
            return
        
        await _start_download_task(listener, tor_info, add_to_queue)
        
        tor_info = await _handle_selection_or_status(listener, tor_info, add_to_queue)
        if tor_info is None:
            return
        
        await _handle_queue_resume(listener, tor_info, event, add_to_queue)
        
    except (ClientError, TimeoutError, Exception, AQError) as error:
        if f"{listener.mid}" in qb_torrents:
            del qb_torrents[f"{listener.mid}"]
        LOGGER.error(f"qBittorrent exception: {error}. User: {listener.mid}")
        await listener.on_download_error(_get_outer_error_message(error))
    finally:
        pass


async def _build_torrent_form(listener, path, ratio, seed_time):
    form = AddFormBuilder.with_client(TorrentManager.qbittorrent)
    if await aiopath.exists(listener.link):
        async with aiopen(listener.link, "rb") as f:
            form = form.include_file(await f.read())
    else:
        form = form.include_url(listener.link)

    form = form.savepath(path).tags([f"{listener.mid}"])
    add_to_queue, event = await check_running_tasks(listener)
    if add_to_queue:
        form = form.stopped(add_to_queue)
    if ratio:
        form = form.ratio_limit(ratio)
    if seed_time:
        form = form.seeding_time_limit(int(seed_time))
    return form


async def _add_and_wait_for_torrent(listener, form, add_to_queue, event):
    try:
        await TorrentManager.qbittorrent.torrents.add(form.build())
    except AQError as error:
        LOGGER.error(f"qBittorrent AQError: {error}. User: {listener.mid}")
        await listener.on_download_error(_get_aq_error_message(error))
        return None
    except (ClientError, TimeoutError, Exception) as error:
        LOGGER.error(f"qBittorrent add request error: {error}. User: {listener.mid}")
        await listener.on_download_error(_get_add_request_error_message(error))
        return None

    tor_info, add_to_queue = await _wait_for_torrent_info(listener, add_to_queue, event)
    return tor_info


async def _start_download_task(listener, tor_info, add_to_queue):
    listener.name = tor_info.name
    ext_hash = tor_info.hash

    async with task_dict_lock:
        task_dict[listener.mid] = QbittorrentStatus(listener, queued=add_to_queue)
    await on_download_start(f"{listener.mid}")

    if add_to_queue:
        LOGGER.info(f"Added to Queue/Download: {tor_info.name} - Hash: {ext_hash}")
    else:
        LOGGER.info(f"QbitDownload started: {tor_info.name} - Hash: {ext_hash}")

    await listener.on_download_start()


async def _handle_queue_resume(listener, tor_info, event, add_to_queue):
    if event is not None:
        if not event.is_set():
            await event.wait()
            if listener.is_cancelled:
                return
            async with task_dict_lock:
                task_dict[listener.mid].queued = False
            LOGGER.info(
                f"Start Queued Download from Qbittorrent: {tor_info.name} - Hash: {tor_info.hash}"
            )
        await on_download_start(f"{listener.mid}")
        await TorrentManager.qbittorrent.torrents.start([tor_info.hash])
        if await aiopath.exists(listener.link):
            await remove(listener.link)
