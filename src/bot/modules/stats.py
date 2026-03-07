from time import time
from re import search as research
from asyncio import gather, sleep
from aiofiles.os import path as aiopath
from psutil import (
    disk_usage,
    cpu_percent,
    swap_memory,
    cpu_count,
    virtual_memory,
    net_io_counters,
    boot_time,
)

from .. import bot_start_time
from ..helper.ext_utils.status_utils import get_readable_file_size, get_readable_time
from ..helper.ext_utils.bot_utils import cmd_exec, new_task
from ..helper.telegram_helper.message_utils import send_message

commands = {
    "aria2": "(checking...)",
    "qBittorrent": "(checking...)",
    "SABnzbd+": "(checking...)",
    "python": (["python3", "--version"], r"Python ([\d.]+)"),
    "rclone": "(checking...)",
    "yt-dlp": (["yt-dlp", "--version"], r"([\d.]+)"),
    "ffmpeg": (["ffmpeg", "-version"], r"ffmpeg version ([\d.]+(-\w+)?).*"),
    "7z": (["7z", "i"], r"7-Zip ([\d.]+)"),
}


@new_task
async def bot_stats(_, message):
    total, used, free, disk = disk_usage("/")
    swap = swap_memory()
    memory = virtual_memory()
    per_cpu = cpu_percent(interval=1, percpu=True)
    per_cpu_str = " | ".join([f"CPU{i+1}: {round(p)}%" for i, p in enumerate(per_cpu)])
    stats = f"""
<b>Commit Date:</b> {commands["commit"]}

<b>Bot Uptime:</b> {get_readable_time(time() - bot_start_time)}
<b>OS Uptime:</b> {get_readable_time(time() - boot_time())}

<b>Total Disk Space:</b> {get_readable_file_size(total)}
<b>Used:</b> {get_readable_file_size(used)} | <b>Free:</b> {get_readable_file_size(free)}

<b>Upload:</b> {get_readable_file_size(net_io_counters().bytes_sent)}
<b>Download:</b> {get_readable_file_size(net_io_counters().bytes_recv)}

<b>CPU:</b> {cpu_percent(interval=1)}%
<b>CPU Cores:</b>
{per_cpu_str}

<b>RAM:</b> {memory.percent}%
<b>DISK:</b> {disk}%

<b>Physical Cores:</b> {cpu_count(logical=False)}
<b>Total Cores:</b> {cpu_count()}
<b>SWAP:</b> {get_readable_file_size(swap.total)} | <b>Used:</b> {swap.percent}%

<b>Memory Total:</b> {get_readable_file_size(memory.total)}
<b>Memory Free:</b> {get_readable_file_size(memory.available)}
<b>Memory Used:</b> {get_readable_file_size(memory.used)}

<b>python:</b> {commands["python"]}
<b>aria2:</b> {commands["aria2"]}
<b>qBittorrent:</b> {commands["qBittorrent"]}
<b>SABnzbd+:</b> {commands["SABnzbd+"]}
<b>rclone:</b> {commands["rclone"]}
<b>yt-dlp:</b> {commands["yt-dlp"]}
<b>ffmpeg:</b> {commands["ffmpeg"]}
<b>7z:</b> {commands["7z"]}
"""
    await send_message(message, stats)


async def get_version_async(command, regex):
    try:
        out, err, code = await cmd_exec(command)
        if code != 0:
            return f"Error: {err}"
        match = research(regex, out)
        return match.group(1) if match else "Version not found"
    except Exception as e:
        return f"Exception: {str(e)}"


async def get_service_status():
    """Check if external services are available"""
    from os import environ
    
    versions = {}
    
    # Check Aria2 - if ARIA2_HOST is configured, assume it's available
    aria2_host = environ.get("ARIA2_HOST", "").strip()
    if aria2_host and aria2_host.lower() != "none":
        try:
            from ..core.torrent_manager import TorrentManager
            # Try to get version from aria2 via RPC
            ver = await TorrentManager.aria2.getVersion()
            if ver and isinstance(ver, dict):
                versions["aria2"] = ver.get("version", "Available (RPC)")
            else:
                versions["aria2"] = "Available (RPC)"
        except Exception:
            versions["aria2"] = "Available (docker)"
    else:
        versions["aria2"] = "Not configured"
    
    # Check qBittorrent - if QB_HOST is configured, assume it's available
    qb_host = environ.get("QB_HOST", "").strip()
    if qb_host and qb_host.lower() != "none":
        versions["qBittorrent"] = "Available (docker)"
    else:
        versions["qBittorrent"] = "Not configured"
    
    # Check SABnzbd - if SAB_HOST is configured, assume it's available
    sab_host = environ.get("SAB_HOST", "").strip()
    if sab_host and sab_host.lower() != "none":
        versions["SABnzbd+"] = "Available (docker)"
    else:
        versions["SABnzbd+"] = "Not configured"
    
    # Check rclone - if rclone.conf exists, assume it's available
    if await aiopath.exists("/app/rclone.conf"):
        versions["rclone"] = "Available (configured)"
    else:
        versions["rclone"] = "Not configured"
    
    return versions


@new_task
async def get_packages_version():
    # Get versions for local tools
    local_tools = {
        "python": (["python3", "--version"], r"Python ([\d.]+)"),
        "yt-dlp": (["yt-dlp", "--version"], r"([\d.]+)"),
        "ffmpeg": (["ffmpeg", "-version"], r"ffmpeg version ([\d.]+(-\w+)?).*"),
        "7z": (["7z", "i"], r"7-Zip ([\d.]+)"),
    }
    
    tasks = [get_version_async(command, regex) for command, regex in local_tools.values()]
    versions = await gather(*tasks)
    for tool, version in zip(local_tools.keys(), versions):
        commands[tool] = version
    
    # Get service status for docker containers
    service_versions = await get_service_status()
    commands.update(service_versions)
    
    # Get git commit info
    if await aiopath.exists(".git"):
        try:
            last_commit = await cmd_exec(
                "git log -1 --date=short --pretty=format:'%cd <b>From</b> %cr'", True
            )
            last_commit = last_commit[0]
        except Exception:
            last_commit = "No UPSTREAM_REPO"
    else:
        last_commit = "No UPSTREAM_REPO"
    commands["commit"] = last_commit
