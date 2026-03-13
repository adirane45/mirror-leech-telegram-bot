# Mirror Leech Telegram Bot
# Enhanced with Interactive UI and Queue Manager
# Modified by: justadi

import sys
from collections import deque
from typing import Any

try:
    import uvloop
    if sys.version_info < (3, 12):
        uvloop.install()
except Exception:
    pass
from asyncio import Lock, new_event_loop, set_event_loop
from logging import ERROR, INFO, WARNING, FileHandler, StreamHandler, basicConfig, getLogger
from os import cpu_count
from time import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler

_SabnzbdClient: Any = None
try:
    from integrations.sabnzbdapi import SabnzbdClient as _SabnzbdClient
except ImportError:
    _SabnzbdClient = None

# Import Config and TgClient for backwards compatibility
_Config: Any = None
try:
    from config.main_config import Config as _Config
except (ImportError, ModuleNotFoundError):
    try:
        from config import Config as _Config
    except (ImportError, ModuleNotFoundError):
        _Config = None

# TgClient will be imported later once config is loaded
Config = _Config
TgClient: Any = None

getLogger("requests").setLevel(WARNING)
getLogger("urllib3").setLevel(WARNING)
getLogger("pyrogram").setLevel(ERROR)
getLogger("httpx").setLevel(WARNING)
getLogger("pymongo").setLevel(WARNING)
getLogger("aiohttp").setLevel(WARNING)
getLogger("aioqbt").setLevel(ERROR)
getLogger("web.wserver").setLevel(ERROR)

bot_start_time = time()

bot_loop = new_event_loop()
set_event_loop(bot_loop)

basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[FileHandler("data/logs/log.txt"), StreamHandler()],
    level=INFO,
)

LOGGER = getLogger(__name__)
cpu_no = cpu_count()
threads = max(1, (cpu_no or 1) // 2)
cores = ",".join(str(i) for i in reversed(range(threads)))

DOWNLOAD_DIR = "/app/downloads/"
intervals = {"status": {}, "qb": "", "jd": "", "nzb": "", "stopAll": False}
qb_torrents: dict[str, Any] = {}
jd_downloads: dict[str, Any] = {}
nzb_jobs: dict[str, Any] = {}
user_data: dict[str, Any] = {}
aria2_options: dict[str, Any] = {}
qbit_options: dict[str, Any] = {}
nzb_options: dict[str, Any] = {}
queued_dl: dict[str, Any] = {}
queued_up: dict[str, Any] = {}
status_dict: dict[str, Any] = {}
task_dict: dict[str, Any] = {}
rss_dict: dict[str, Any] = {}
auth_chats: dict[str, Any] = {}
excluded_extensions = ["aria2", "!qB"]
included_extensions: list[str] = []
drives_names: list[str] = []
drives_ids: list[str] = []
index_urls: list[str] = []
sudo_users: list[int] = []
non_queued_dl: set[str] = set()
non_queued_up: set[str] = set()
multi_tags: set[str] = set()
task_dict_lock = Lock()
queue_dict_lock = Lock()
qb_listener_lock = Lock()
nzb_listener_lock = Lock()
jd_listener_lock = Lock()
cpu_eater_lock = Lock()
same_directory_lock = Lock()

sabnzbd_client = (
    _SabnzbdClient(
        host="http://localhost",
        api_key="mltb",
        port="8070",
    )
    if _SabnzbdClient is not None
    else None
)

scheduler = AsyncIOScheduler(event_loop=bot_loop)

# UI/UX enhancements: history and settings
download_history: deque[dict[str, Any]] = deque(maxlen=200)
ui_settings = {
    "theme": "dark",
    "notifications": True,
    "auto_pause": {
        "enabled": False,
        "cpu": 90,
        "ram": 90,
        "disk": 95,
        "last_trigger": 0,
    },
}
