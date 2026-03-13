from asyncio import gather, iscoroutinefunction
from html import escape
from time import time
from typing import Any

from psutil import cpu_percent, disk_usage, virtual_memory  # type: ignore[import-untyped]

from ... import DOWNLOAD_DIR, bot_start_time, status_dict, task_dict, task_dict_lock, user_data
from ...core.config_manager import Config
from ..telegram_helper.bot_commands import BotCommands
from ..telegram_helper.button_build import ButtonMaker

SIZE_UNITS = ["B", "KB", "MB", "GB", "TB", "PB"]


class MirrorStatus:
    STATUS_UPLOAD = "Upload"
    STATUS_DOWNLOAD = "Download"
    STATUS_CLONE = "Clone"
    STATUS_QUEUEDL = "QueueDl"
    STATUS_QUEUEUP = "QueueUp"
    STATUS_PAUSED = "Pause"
    STATUS_ARCHIVE = "Archive"
    STATUS_EXTRACT = "Extract"
    STATUS_SPLIT = "Split"
    STATUS_CHECK = "CheckUp"
    STATUS_SEED = "Seed"
    STATUS_SAMVID = "SamVid"
    STATUS_CONVERT = "Convert"
    STATUS_FFMPEG = "FFmpeg"


STATUSES = {
    "ALL": "All",
    "DL": MirrorStatus.STATUS_DOWNLOAD,
    "UP": MirrorStatus.STATUS_UPLOAD,
    "QD": MirrorStatus.STATUS_QUEUEDL,
    "QU": MirrorStatus.STATUS_QUEUEUP,
    "AR": MirrorStatus.STATUS_ARCHIVE,
    "EX": MirrorStatus.STATUS_EXTRACT,
    "SD": MirrorStatus.STATUS_SEED,
    "CL": MirrorStatus.STATUS_CLONE,
    "CM": MirrorStatus.STATUS_CONVERT,
    "SP": MirrorStatus.STATUS_SPLIT,
    "SV": MirrorStatus.STATUS_SAMVID,
    "FF": MirrorStatus.STATUS_FFMPEG,
    "PA": MirrorStatus.STATUS_PAUSED,
    "CK": MirrorStatus.STATUS_CHECK,
}

STATUS_EMOJI = {
    MirrorStatus.STATUS_DOWNLOAD: "▶️",
    MirrorStatus.STATUS_UPLOAD: "⬆️",
    MirrorStatus.STATUS_QUEUEDL: "⏳",
    MirrorStatus.STATUS_QUEUEUP: "⏳",
    MirrorStatus.STATUS_PAUSED: "⏸️",
    MirrorStatus.STATUS_CLONE: "📂",
    MirrorStatus.STATUS_SEED: "🌱",
    MirrorStatus.STATUS_ARCHIVE: "🗜️",
    MirrorStatus.STATUS_EXTRACT: "📦",
    MirrorStatus.STATUS_SPLIT: "✂️",
    MirrorStatus.STATUS_CHECK: "✅",
    MirrorStatus.STATUS_SAMVID: "🎞️",
    MirrorStatus.STATUS_CONVERT: "🎛️",
    MirrorStatus.STATUS_FFMPEG: "🎬",
}


def speed_indicator(speed_text: str) -> str:
    try:
        speed_bytes = speed_string_to_bytes(speed_text)
    except Exception:
        speed_bytes = 0
    if speed_bytes >= 50 * 1024 * 1024:
        return "⚡"
    if speed_bytes >= 10 * 1024 * 1024:
        return "🚀"
    if speed_bytes >= 2 * 1024 * 1024:
        return "🏃"
    if speed_bytes > 0:
        return "🐢"
    return "⏸️"


async def get_task_by_gid(gid: str) -> Any | None:
    async with task_dict_lock:
        for tk in task_dict.values():
            if hasattr(tk, "seeding"):
                await tk.update()
            if tk.gid() == gid:
                return tk
        return None


async def get_specific_tasks(status: str, user_id: str | int | None) -> list[Any]:
    tasks_to_check = _filter_tasks_by_user(user_id)
    if status == "All":
        return tasks_to_check
    
    coro_map = await _gather_async_statuses(tasks_to_check)
    return _filter_tasks_by_status(tasks_to_check, status, coro_map)


def _filter_tasks_by_user(user_id: str | int | None) -> list[Any]:
    if user_id:
        return [tk for tk in task_dict.values() if tk.listener.user_id == user_id]
    return list(task_dict.values())


async def _gather_async_statuses(tasks_to_check: list[Any]) -> dict[Any, str]:
    coro_tasks = [tk for tk in tasks_to_check if iscoroutinefunction(tk.status)]
    coro_statuses = await gather(*[tk.status() for tk in coro_tasks])
    return dict(zip(coro_tasks, coro_statuses))


def _filter_tasks_by_status(
    tasks_to_check: list[Any], status: str, coro_map: dict[Any, str]
) -> list[Any]:
    result = []
    for tk in tasks_to_check:
        st = coro_map.get(tk, tk.status())
        if st == status or (
            status == MirrorStatus.STATUS_DOWNLOAD and st not in STATUSES.values()
        ):
            result.append(tk)
    return result


def _get_view_mode(sid: str, is_user: bool) -> str:
    view_mode = "detailed"
    if is_user:
        view_mode = user_data.get(sid, {}).get("UI_VIEW", "detailed")
    if sid in status_dict and status_dict[sid].get("view"):
        view_mode = status_dict[sid]["view"]
    return view_mode


def _normalize_page(page_no: int, pages: int, sid: str) -> int:
    if page_no > pages:
        page_no = (page_no - 1) % pages + 1
        status_dict[sid]["page_no"] = page_no
    elif page_no < 1:
        page_no = pages - (abs(page_no) % pages)
        status_dict[sid]["page_no"] = page_no
    return page_no


def _update_counts(counts: dict[str, int], tstatus: str) -> None:
    if tstatus == MirrorStatus.STATUS_DOWNLOAD:
        counts["download"] += 1
    elif tstatus == MirrorStatus.STATUS_UPLOAD:
        counts["upload"] += 1
    elif tstatus == MirrorStatus.STATUS_PAUSED:
        counts["paused"] += 1
    elif tstatus in [MirrorStatus.STATUS_QUEUEDL, MirrorStatus.STATUS_QUEUEUP]:
        counts["queued"] += 1
    else:
        counts["other"] += 1


async def get_all_tasks(req_status: str, user_id: str | int | None) -> list[Any]:
    async with task_dict_lock:
        return await get_specific_tasks(req_status, user_id)


def get_readable_file_size(size_in_bytes: int | float) -> str:
    if not size_in_bytes:
        return "0B"

    index = 0
    while size_in_bytes >= 1024 and index < len(SIZE_UNITS) - 1:
        size_in_bytes /= 1024
        index += 1

    return f"{size_in_bytes:.2f}{SIZE_UNITS[index]}"


def get_readable_time(seconds: int) -> str:
    periods = [("d", 86400), ("h", 3600), ("m", 60), ("s", 1)]
    result = ""
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f"{int(period_value)}{period_name}"
    return result


def time_to_seconds(time_duration: str) -> float:
    try:
        parts = time_duration.split(":")
        if len(parts) == 3:
            hours, minutes, seconds = map(float, parts)
        elif len(parts) == 2:
            hours = 0
            minutes, seconds = map(float, parts)
        elif len(parts) == 1:
            hours = 0
            minutes = 0
            seconds = float(parts[0])
        else:
            return 0
        return hours * 3600 + minutes * 60 + seconds
    except:
        return 0


def speed_string_to_bytes(size_text: str) -> float:
    size = 0.0
    size_text = size_text.lower()
    if "k" in size_text:
        size += float(size_text.split("k")[0]) * 1024
    elif "m" in size_text:
        size += float(size_text.split("m")[0]) * 1048576
    elif "g" in size_text:
        size += float(size_text.split("g")[0]) * 1073741824
    elif "t" in size_text:
        size += float(size_text.split("t")[0]) * 1099511627776
    elif "b" in size_text:
        size += float(size_text.split("b")[0])
    return size


def get_progress_bar_string(pct: str | float) -> str:
    progress = float(str(pct).strip("%"))
    p = min(max(progress, 0.0), 100.0)
    cFull = int(p // 8)
    p_str = "■" * cFull
    p_str += "□" * (12 - cFull)
    return f"[{p_str}]"


async def _resolve_task_status(task: Any, selected_status: str) -> Any:
    if selected_status != "All":
        return selected_status
    if iscoroutinefunction(task.status):
        return await task.status()
    return task.status()


def _build_task_header(task: Any, position: int, status_icon: str, task_status: str) -> str:
    if task.listener.is_super_chat:
        return (
            f"<b>{position}.<a href='{task.listener.message.link}'>{status_icon} {task_status}</a>:</b> "
            f"<code>{escape(f'{task.name()}')}</code>"
        )
    return (
        f"<b>{position}.{status_icon} {task_status}:</b> "
        f"<code>{escape(f'{task.name()}')}</code>"
    )


def _build_processed_count(task: Any) -> tuple[str, str]:
    if not task.listener.subname:
        return "", ""
    subsize = f"/{get_readable_file_size(task.listener.subsize)}"
    total_items = len(task.listener.files_to_proceed)
    count = f"{task.listener.proceed_count}/{total_items or '?'}"
    return subsize, count


async def _append_task_category(lines: list[str], task: Any) -> None:
    try:
        from ...core.task_categorizer import TaskCategorizer

        category = await TaskCategorizer.get_task_category(task.gid())
        if category:
            lines.append(f"<b>Category:</b> <code>{category}</code>")
    except Exception:
        pass


async def _build_active_task_lines(task: Any, task_status: str, view_mode: str) -> list[str]:
    lines = []
    progress = task.progress()
    lines.append(f"<b>Progress:</b> {get_progress_bar_string(progress)} {progress}")

    subsize, count = _build_processed_count(task)
    speed = task.speed()

    if view_mode == "detailed":
        await _append_task_category(lines, task)
        lines.append(f"<b>Processed:</b> {task.processed_bytes()}{subsize}")
        if count:
            lines.append(f"<b>Count:</b> {count}")
        lines.append(f"<b>Size:</b> {task.size()}")
        lines.append(f"<b>Speed:</b> {speed_indicator(speed)} {speed}")
        lines.append(f"<b>ETA:</b> ⏳ {task.eta()}")
    else:
        lines.append(f"<b>Speed:</b> {speed_indicator(speed)} {speed} | <b>ETA:</b> ⏳ {task.eta()}")

    if (
        task_status == MirrorStatus.STATUS_DOWNLOAD
        and task.listener.is_torrent
        or task.listener.is_qbit
    ):
        try:
            lines.append(
                f"<b>Seeders:</b> {task.seeders_num()} | <b>Leechers:</b> {task.leechers_num()}"
            )
        except Exception:
            pass
    return lines


def _build_seed_task_lines(task: Any) -> list[str]:
    return [
        f"<b>Size: </b>{task.size()}",
        f"<b>Speed: </b>{task.seed_speed()}",
        f"<b>Uploaded: </b>{task.uploaded_bytes()}",
        f"<b>Ratio: </b>{task.ratio()} | <b>Time: </b>{task.seeding_time()}",
    ]


def _build_overview_message(counts: dict[str, int]) -> str:
    return (
        f"<b>📌 Status Overview:</b> ▶️ {counts['download']} | ⬆️ {counts['upload']} | "
        f"⏸️ {counts['paused']} | ⏳ {counts['queued']} | ⚙️ {counts['other']}\n\n"
    )


def _add_header_buttons(buttons: ButtonMaker, sid: str, is_user: bool) -> None:
    buttons.data_button("Queue", "quick_queue", position="header")
    buttons.data_button("Settings", "quick_settings", position="header")
    buttons.data_button("Help", "help menu", position="header")
    if not is_user:
        buttons.data_button("📜", f"status {sid} ov", position="header")
    buttons.data_button("View", f"status {sid} view", position="header")
    buttons.data_button("♻️", f"status {sid} ref", position="header")


def _add_pagination_buttons(
    buttons: ButtonMaker,
    sid: str,
    tasks_no: int,
    status_limit: int,
    page_no: int,
    pages: int,
    page_step: int,
) -> str:
    page_info = ""
    if tasks_no > status_limit:
        page_info = (
            f"<b>Page:</b> {page_no}/{pages} | <b>Tasks:</b> {tasks_no} | <b>Step:</b> {page_step}\n"
        )
        buttons.data_button("<<", f"status {sid} pre", position="header")
        buttons.data_button(">>", f"status {sid} nex", position="header")
        if tasks_no > 30:
            for step in [1, 2, 4, 6, 8, 10, 15]:
                buttons.data_button(str(step), f"status {sid} ps {step}", position="footer")
    return page_info


def _add_status_filter_buttons(
    buttons: ButtonMaker, sid: str, status: str, tasks_no: int
) -> None:
    if status != "All" or tasks_no > 20:
        for label, status_value in list(STATUSES.items()):
            if status_value != status:
                buttons.data_button(label, f"status {sid} st {status_value}")


async def get_readable_message(
    sid: str,
    is_user: bool,
    page_no: int = 1,
    status: str = "All",
    page_step: int = 1,
) -> tuple[str | None, Any | None]:
    tasks = await get_specific_tasks(status, sid if is_user else None)
    view_mode = _get_view_mode(sid, is_user)
    status_limit = int(getattr(Config, "STATUS_LIMIT", 10))
    tasks_no = len(tasks)
    pages = (max(tasks_no, 1) + status_limit - 1) // status_limit
    page_no = _normalize_page(page_no, pages, sid)
    start_position = (page_no - 1) * status_limit

    counts = {
        "download": 0,
        "upload": 0,
        "paused": 0,
        "queued": 0,
        "other": 0,
    }
    task_messages = []

    for index, task in enumerate(
        tasks[start_position : status_limit + start_position], start=1
    ):
        task_status = await _resolve_task_status(task, status)
        _update_counts(counts, task_status)

        lines = [
            _build_task_header(
                task,
                index + start_position,
                STATUS_EMOJI.get(task_status, "⚙️"),
                task_status,
            )
        ]
        if task.listener.subname:
            lines.append(f"<i>{task.listener.subname}</i>")
        if (
            task_status not in [MirrorStatus.STATUS_SEED, MirrorStatus.STATUS_QUEUEUP]
            and task.listener.progress
        ):
            lines.extend(await _build_active_task_lines(task, task_status, view_mode))
        elif task_status == MirrorStatus.STATUS_SEED:
            lines.extend(_build_seed_task_lines(task))
        else:
            lines.append(f"<b>Size: </b>{task.size()}")
        lines.append(f"<code>/{BotCommands.CancelTaskCommand[1]} {task.gid()}</code>")
        task_messages.append("\n".join(lines))

    msg = "\n\n".join(task_messages)

    if len(msg) == 0:
        if status == "All":
            return None, None
        else:
            msg = f"No Active {status} Tasks!\n\n"

    buttons = ButtonMaker()
    _add_header_buttons(buttons, sid, is_user)
    msg = _build_overview_message(counts) + msg
    msg += _add_pagination_buttons(
        buttons,
        sid,
        tasks_no,
        status_limit,
        page_no,
        pages,
        page_step,
    )
    _add_status_filter_buttons(buttons, sid, status, tasks_no)

    button = buttons.build_menu(8)
    msg += f"<b>CPU:</b> {cpu_percent()}% | <b>FREE:</b> {get_readable_file_size(disk_usage(DOWNLOAD_DIR).free)}"
    msg += f"\n<b>RAM:</b> {virtual_memory().percent}% | <b>UPTIME:</b> {get_readable_time(int(time() - bot_start_time))}"
    return msg, button
