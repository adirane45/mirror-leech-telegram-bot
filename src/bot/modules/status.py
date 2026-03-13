from asyncio import gather, iscoroutinefunction
from time import time

from psutil import cpu_percent, disk_usage, virtual_memory

from .. import DOWNLOAD_DIR, bot_start_time, intervals, sabnzbd_client, status_dict, task_dict, task_dict_lock
from ..core.jdownloader_booter import jdownloader
from ..core.torrent_manager import TorrentManager
from ..helper.ext_utils.bot_utils import new_task
from ..helper.ext_utils.status_utils import (
    MirrorStatus,
    get_readable_file_size,
    get_readable_time,
    speed_string_to_bytes,
)
from ..helper.telegram_helper.bot_commands import BotCommands
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.message_utils import (
    auto_delete_message,
    delete_message,
    edit_message,
    send_message,
    send_status_message,
    update_status_message,
)


@new_task
async def task_status(_, message):
    async with task_dict_lock:
        count = len(task_dict)
    if count == 0:
        currentTime = get_readable_time(time() - bot_start_time)
        free = get_readable_file_size(disk_usage(DOWNLOAD_DIR).free)
        msg = f"No Active Tasks!\nEach user can get status for his tasks by adding me or user_id after cmd: /{BotCommands.StatusCommand} me"
        msg += (
            f"\n<b>CPU:</b> {cpu_percent()}% | <b>FREE:</b> {free}"
            f"\n<b>RAM:</b> {virtual_memory().percent}% | <b>UPTIME:</b> {currentTime}"
        )
        reply_message = await send_message(message, msg)
        await auto_delete_message(message, reply_message)
    else:
        text = message.text.split()
        if len(text) > 1:
            user_id = message.from_user.id if text[1] == "me" else int(text[1])
        else:
            user_id = 0
            sid = message.chat.id
            if obj := intervals["status"].get(sid):
                obj.cancel()
                del intervals["status"][sid]
        await send_status_message(message, user_id)
        await delete_message(message)


async def get_download_status(download):
    tool = download.tool
    if tool in [
        "telegram",
        "yt-dlp",
        "rclone",
        "gDriveApi",
    ]:
        speed = download.speed()
    else:
        speed = 0
    return (
        await download.status()
        if iscoroutinefunction(download.status)
        else download.status()
    ), speed


async def _update_page_position(key, action):
    async with task_dict_lock:
        if key not in status_dict:
            return
        if action == "nex":
            status_dict[key]["page_no"] += status_dict[key]["page_step"]
        else:
            status_dict[key]["page_no"] -= status_dict[key]["page_step"]


async def _set_page_step(key, step):
    async with task_dict_lock:
        if key in status_dict:
            status_dict[key]["page_step"] = int(step)


async def _set_status_filter(key, status_value):
    async with task_dict_lock:
        if key in status_dict:
            status_dict[key]["status"] = status_value


async def _toggle_view_mode(key):
    async with task_dict_lock:
        if key not in status_dict:
            return
        current = status_dict[key].get("view", "detailed")
        status_dict[key]["view"] = "compact" if current == "detailed" else "detailed"


async def _get_base_overall_speeds():
    ds, ss = await TorrentManager.overall_speed()
    if sabnzbd_client.LOGGED_IN:
        sds = await sabnzbd_client.get_downloads()
        ds += int(float(sds["queue"].get("kbpersec", "0"))) * 1024
    if jdownloader.is_connected:
        ds += await jdownloader.device.downloadcontroller.get_speed_in_bytes()
    return ds, ss


def _init_overview_counts():
    return {
        "Download": 0,
        "Upload": 0,
        "Seed": 0,
        "Archive": 0,
        "Extract": 0,
        "Split": 0,
        "QueueDl": 0,
        "QueueUp": 0,
        "Clone": 0,
        "CheckUp": 0,
        "Pause": 0,
        "SamVid": 0,
        "ConvertMedia": 0,
        "FFmpeg": 0,
    }


def _apply_status_counts(tasks, status, speed, dl_speed, up_speed):
    status_map = {
        MirrorStatus.STATUS_DOWNLOAD: "Download",
        MirrorStatus.STATUS_UPLOAD: "Upload",
        MirrorStatus.STATUS_SEED: "Seed",
        MirrorStatus.STATUS_ARCHIVE: "Archive",
        MirrorStatus.STATUS_EXTRACT: "Extract",
        MirrorStatus.STATUS_SPLIT: "Split",
        MirrorStatus.STATUS_QUEUEDL: "QueueDl",
        MirrorStatus.STATUS_QUEUEUP: "QueueUp",
        MirrorStatus.STATUS_CLONE: "Clone",
        MirrorStatus.STATUS_CHECK: "CheckUp",
        MirrorStatus.STATUS_PAUSED: "Pause",
        MirrorStatus.STATUS_SAMVID: "SamVid",
        MirrorStatus.STATUS_CONVERT: "ConvertMedia",
        MirrorStatus.STATUS_FFMPEG: "FFmpeg",
    }
    key = status_map.get(status, "Download")
    tasks[key] += 1
    if key == "Download" and speed:
        dl_speed += speed_string_to_bytes(speed)
    elif key == "Upload":
        up_speed += speed_string_to_bytes(speed)
    return dl_speed, up_speed


def _build_overview_message(tasks, dl_speed, up_speed, seed_speed):
    return f"""<b>DL:</b> {tasks['Download']} | <b>UP:</b> {tasks['Upload']} | <b>SD:</b> {tasks['Seed']} | <b>AR:</b> {tasks['Archive']}
<b>EX:</b> {tasks['Extract']} | <b>SP:</b> {tasks['Split']} | <b>QD:</b> {tasks['QueueDl']} | <b>QU:</b> {tasks['QueueUp']}
<b>CL:</b> {tasks['Clone']} | <b>CK:</b> {tasks['CheckUp']} | <b>PA:</b> {tasks['Pause']} | <b>SV:</b> {tasks['SamVid']}
<b>CM:</b> {tasks['ConvertMedia']} | <b>FF:</b> {tasks['FFmpeg']}

<b>ODLS:</b> {get_readable_file_size(dl_speed)}/s
<b>OULS:</b> {get_readable_file_size(up_speed)}/s
<b>OSDS:</b> {get_readable_file_size(seed_speed)}/s
"""


async def _handle_overview(query, data):
    ds, ss = await _get_base_overall_speeds()
    tasks = _init_overview_counts()
    dl_speed = ds
    up_speed = 0
    seed_speed = ss

    async with task_dict_lock:
        status_results = await gather(
            *(get_download_status(download) for download in task_dict.values())
        )
        for status, speed in status_results:
            dl_speed, up_speed = _apply_status_counts(
                tasks, status, speed, dl_speed, up_speed
            )

    msg = _build_overview_message(tasks, dl_speed, up_speed, seed_speed)
    button = ButtonMaker()
    button.data_button("Back", f"status {data[1]} ref")
    await edit_message(query.message, msg, button.build_menu())


@new_task
async def status_pages(_, query):
    data = query.data.split()
    key = int(data[1])
    await query.answer()
    action = data[2]

    if action == "ref":
        await update_status_message(key, force=True)
        return

    if action in ["nex", "pre"]:
        await _update_page_position(key, action)
        return

    if action == "ps":
        await _set_page_step(key, data[3])
        return

    if action == "st":
        await _set_status_filter(key, data[3])
        await update_status_message(key, force=True)
        return

    if action == "view":
        await _toggle_view_mode(key)
        await update_status_message(key, force=True)
        return

    if action == "ov":
        await _handle_overview(query, data)
