# Bandwidth Limiting Commands
# Control download and upload speeds globally or per-task
# Prevents network saturation
# Modified by: justadi

from ..core.bandwidth_limiter import BandwidthLimiter
from ..core.torrent_manager import TorrentManager
from ..helper.ext_utils.bot_utils import new_task
from ..helper.telegram_helper.message_utils import send_message
from .. import task_dict, task_dict_lock


def _parse_limit(value: str):
    value = value.lower().strip()
    if value in {"off", "none", "0"}:
        return None
    return float(value)


async def _apply_global_limits():
    """Apply global limits to aria2/qbit if available"""
    dl = await BandwidthLimiter.get_effective_limit("global", "download")
    ul = await BandwidthLimiter.get_effective_limit("global", "upload")

    # aria2 global limits
    try:
        options = {}
        if dl is not None:
            options["max-overall-download-limit"] = str(dl)
        if ul is not None:
            options["max-overall-upload-limit"] = str(ul)
        if options:
            await TorrentManager.aria2.changeGlobalOption(options)
    except Exception:
        pass

    # qBittorrent global limits
    try:
        prefs = {}
        if dl is not None:
            prefs["dl_limit"] = dl
        if ul is not None:
            prefs["up_limit"] = ul
        if prefs:
            await TorrentManager.qbittorrent.app.set_preferences(prefs)
    except Exception:
        pass


@new_task
async def set_bandwidth(_, message):
    """
    Set global bandwidth limits (sudo only)
    
    Usage:
        /limit dl <mbps|off>  - Set download limit
        /limit ul <mbps|off>  - Set upload limit
    
    Examples:
        /limit dl 50    - Limit downloads to 50 Mbps
        /limit ul 10    - Limit uploads to 10 Mbps
        /limit dl off   - Remove download limit
    
    Modified by: justadi
    """
    parts = message.text.split()
    if len(parts) < 3:
        await send_message(
            message,
            "<b>⚙️ Bandwidth Limit</b>\n\n"
            "Usage:\n"
            "<code>/limit dl &lt;mbps|off&gt;</code>\n"
            "<code>/limit ul &lt;mbps|off&gt;</code>",
        )
        return

    limit_type = parts[1].lower()
    try:
        limit_value = _parse_limit(parts[2])
    except Exception:
        await send_message(message, "<b>❌ Invalid limit value.</b>")
        return

    if limit_type == "dl":
        ok = await BandwidthLimiter.set_global_download_limit(limit_value)
    elif limit_type == "ul":
        ok = await BandwidthLimiter.set_global_upload_limit(limit_value)
    else:
        await send_message(message, "<b>❌ Use dl or ul.</b>")
        return

    if ok:
        await _apply_global_limits()
        await send_message(message, "<b>✅ Global limit updated.</b>")
    else:
        await send_message(message, "<b>❌ Failed to update limit.</b>")


@new_task
async def set_task_bandwidth(_, message):
    """Set per-task bandwidth limits (aria2 supported)"""
    parts = message.text.split()
    if len(parts) < 4:
        await send_message(
            message,
            "<b>⚙️ Task Bandwidth Limit</b>\n\n"
            "Usage:\n"
            "<code>/limit_task &lt;gid&gt; dl &lt;mbps|off&gt;</code>\n"
            "<code>/limit_task &lt;gid&gt; ul &lt;mbps|off&gt;</code>",
        )
        return

    gid = parts[1].strip()
    limit_type = parts[2].lower()
    try:
        limit_value = _parse_limit(parts[3])
    except Exception:
        await send_message(message, "<b>❌ Invalid limit value.</b>")
        return

    target = None
    async with task_dict_lock:
        for task in task_dict.values():
            try:
                if task.gid() == gid:
                    target = task
                    break
            except Exception:
                continue

    if not target:
        await send_message(message, "<b>❌ Task not found.</b>")
        return

    if limit_type == "dl":
        await BandwidthLimiter.set_task_limit(gid, download_limit=limit_value)
    elif limit_type == "ul":
        await BandwidthLimiter.set_task_limit(gid, upload_limit=limit_value)
    else:
        await send_message(message, "<b>❌ Use dl or ul.</b>")
        return

    if getattr(target, "tool", "") == "aria2":
        try:
            options = {}
            if limit_type == "dl":
                options["max-download-limit"] = str(int(limit_value * 1_000_000 / 8)) if limit_value else "0"
            else:
                options["max-upload-limit"] = str(int(limit_value * 1_000_000 / 8)) if limit_value else "0"
            await TorrentManager.aria2.changeOption(target.gid(), options)
        except Exception:
            pass

    await send_message(message, "<b>✅ Task limit updated.</b>")