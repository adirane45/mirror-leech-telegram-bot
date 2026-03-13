from asyncio import gather
from json import loads
from secrets import token_urlsafe

from aiofiles.os import remove

from .... import LOGGER, task_dict, task_dict_lock
from ...ext_utils.bot_utils import cmd_exec
from ...ext_utils.task_manager import check_running_tasks, stop_duplicate_check
from ...mirror_leech_utils.rclone_utils.transfer import RcloneTransferHelper
from ...mirror_leech_utils.status_utils.queue_status import QueueStatus
from ...mirror_leech_utils.status_utils.rclone_status import RcloneStatus
from ...telegram_helper.message_utils import send_status_message


def _parse_rclone_config_and_remote(listener):
    """Parse config path and remote from listener link."""
    if listener.link.startswith("mrcc:"):
        listener.link = listener.link.split("mrcc:", 1)[1]
        config_path = f"rclone/{listener.user_id}.conf"
    else:
        config_path = "rclone.conf"
    
    remote, listener.link = listener.link.split(":", 1)
    listener.link = listener.link.strip("/")
    return config_path, remote


def _is_rclone_select(link):
    """Check if link is a rclone_select file."""
    return link.startswith("rclone_select")


def _build_rclone_commands(config_path, remote, rpath, rclone_select, select_file):
    """Build rclone lsjson and size commands."""
    cmd1 = [
        "rclone",
        "lsjson",
        "--fast-list",
        "--stat",
        "--no-mimetype",
        "--no-modtime",
        "--config",
        config_path,
        f"{remote}:{rpath}",
    ]
    cmd2 = [
        "rclone",
        "size",
        "--fast-list",
        "--json",
        "--config",
        config_path,
        f"{remote}:{rpath}",
    ]
    if rclone_select:
        cmd2.extend(("--files-from", select_file))
    return cmd1, cmd2


async def _fetch_rclone_select_size(cmd2, remote, link, listener):
    """Fetch size for rclone_select."""
    res = await cmd_exec(cmd2)
    if res[2] != 0:
        if res[2] != -9:
            msg = f"Error: While getting rclone stat/size. Path: {remote}:{link}. Stderr: {res[1][:4000]}"
            await listener.on_download_error(msg)
        return None
    try:
        return loads(res[0])
    except Exception as err:
        await listener.on_download_error(f"RcloneDownload JsonLoad: {err}")
        return None


async def _fetch_rclone_stat_and_size(cmd1, cmd2, remote, link, listener):
    """Fetch stat and size for regular rclone path."""
    res1, res2 = await gather(cmd_exec(cmd1), cmd_exec(cmd2))
    if res1[2] != 0 or res2[2] != 0:
        if res1[2] != -9:
            err = res1[1] or res2[1]
            msg = f"Error: While getting rclone stat/size. Path: {remote}:{link}. Stderr: {err[:4000]}"
            await listener.on_download_error(msg)
        return None, None
    try:
        rstat = loads(res1[0])
        rsize = loads(res2[0])
        return rstat, rsize
    except Exception as err:
        await listener.on_download_error(f"RcloneDownload JsonLoad: {err}")
        return None, None


def _resolve_download_name(listener, rstat, remote, rclone_select):
    """Resolve download name based on path type."""
    if rclone_select:
        if not listener.name:
            listener.name = listener.link
        return listener.name
    
    if rstat["IsDir"]:
        if not listener.name:
            listener.name = (
                listener.link.rsplit("/", 1)[-1] if listener.link else remote
            )
        return listener.name
    else:
        listener.name = listener.link.rsplit("/", 1)[-1]
        return listener.name


async def _setup_download_task(listener, gid, add_to_queue, event):
    """Setup download task in task_dict and handle queue."""
    if add_to_queue:
        LOGGER.info(f"Added to Queue/Download: {listener.name}")
        async with task_dict_lock:
            task_dict[listener.mid] = QueueStatus(listener, gid, "dl")
        await listener.on_download_start()
        if listener.multi <= 1:
            await send_status_message(listener.message)
        await event.wait()
        if listener.is_cancelled:
            return False
    return True


async def _get_rclone_metadata(
    cmd1,
    cmd2,
    remote,
    listener,
    rclone_select,
):
    if rclone_select:
        rsize = await _fetch_rclone_select_size(cmd2, remote, listener.link, listener)
        if rsize is None:
            return None, None
        return None, rsize

    rstat, rsize = await _fetch_rclone_stat_and_size(
        cmd1,
        cmd2,
        remote,
        listener.link,
        listener,
    )
    if rstat is None or rsize is None:
        return None, None
    return rstat, rsize


async def _announce_rclone_download_start(listener, add_to_queue):
    if add_to_queue:
        LOGGER.info(f"Start Queued Download with rclone: {listener.link}")
        return

    await listener.on_download_start()
    if listener.multi <= 1:
        await send_status_message(listener.message)
    LOGGER.info(f"Download with rclone: {listener.link}")


async def add_rclone_download(listener, path):
    config_path, remote = _parse_rclone_config_and_remote(listener)
    rclone_select = _is_rclone_select(listener.link)
    rpath = "" if rclone_select else listener.link
    
    cmd1, cmd2 = _build_rclone_commands(
        config_path, remote, rpath, rclone_select, listener.link
    )
    
    rstat, rsize = await _get_rclone_metadata(
        cmd1,
        cmd2,
        remote,
        listener,
        rclone_select,
    )
    if rsize is None:
        return
    
    listener.name = _resolve_download_name(listener, rstat, remote, rclone_select)
    if rstat is None or rstat.get("IsDir"):
        path += listener.name
    
    listener.size = rsize["bytes"]
    gid = token_urlsafe(12)
    
    if not rclone_select:
        msg, button = await stop_duplicate_check(listener)
        if msg:
            await listener.on_download_error(msg, button)
            return
    
    add_to_queue, event = await check_running_tasks(listener)
    if not await _setup_download_task(listener, gid, add_to_queue, event):
        return
    
    RCTransfer = RcloneTransferHelper(listener)
    async with task_dict_lock:
        task_dict[listener.mid] = RcloneStatus(listener, RCTransfer, gid, "dl")

    await _announce_rclone_download_start(listener, add_to_queue)
    
    await RCTransfer.download(remote, config_path, path)
    if rclone_select:
        await remove(listener.link)
