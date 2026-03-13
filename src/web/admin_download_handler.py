"""Admin download handler - Process downloads from admin panel"""
import asyncio
from logging import getLogger
from typing import Any, Dict, Optional

from bot.core.config_manager import Config
from web.download_history import DownloadHistory

LOGGER = getLogger(__name__)

# In-memory storage for pending downloads (simple queue)
# In production, use Redis with proper key scanning
_pending_downloads: Dict[str, Dict[str, Any]] = {}
_download_lock = asyncio.Lock()

# Initialize history database
history_db = DownloadHistory("/app/data/download_history.db")

# For tracking active downloads in task_dict
_last_speed_update = {}
_tracked_in_task_dict = set()  # Track which downloads are currently in task_dict
_completion_called = set()  # Track downloads that already had completion callback called


def _normalize_destination(destination: Optional[str]) -> str:
    if not destination or not destination.startswith("/"):
        return "/app/downloads"
    return destination


async def _set_download_error(download_id: str, error_msg: str):
    """Set download status to error with message"""
    async with _download_lock:
        if download_id in _pending_downloads:
            _pending_downloads[download_id]["status"] = "error"
            _pending_downloads[download_id]["error"] = error_msg


async def _init_aria2_if_needed(download_id: str) -> bool:
    """Initialize Aria2 if not ready. Returns True if ready, False otherwise."""
    from bot.core.torrent_manager import TorrentManager
    if TorrentManager.aria2 is None:
        LOGGER.warning(f"[_PROCESS_DOWNLOAD] Aria2 not initialized for {download_id} - attempting init")
        try:
            await TorrentManager.initiate()
        except Exception as e:
            LOGGER.warning(f"[_PROCESS_DOWNLOAD] Aria2 init failed for {download_id}: {e}")
            return False
    return TorrentManager.aria2 is not None


async def _handle_torrent_download(listener, destination: str, download_id: str):
    """Handle torrent downloads with qBittorrent or Aria2 fallback"""
    LOGGER.info(f"[_PROCESS_DOWNLOAD] Detected torrent link, using qBittorrent for {download_id}")
    try:
        from bot.helper.mirror_leech_utils.download_utils.qbit_download import add_qb_torrent
        LOGGER.info(f"[_PROCESS_DOWNLOAD] Imported add_qb_torrent successfully for {download_id}")
        await add_qb_torrent(listener, destination, 0, 0)
        LOGGER.info(f"Queued to qBittorrent: {download_id}")
    except ImportError:
        LOGGER.info(f"[_PROCESS_DOWNLOAD] qBittorrent unavailable, trying Aria2 fallback for {download_id}")
        if not await _init_aria2_if_needed(download_id):
            return
        from bot.helper.mirror_leech_utils.download_utils.aria2_download import add_aria2_download
        await add_aria2_download(listener, destination, "", 0, 0)
        LOGGER.info(f"[_PROCESS_DOWNLOAD] Queued to Aria2 (fallback) for {download_id}")
    except (AttributeError, TypeError) as e:
        LOGGER.error(f"[_PROCESS_DOWNLOAD] qBittorrent attribute error: {e} for {download_id}", exc_info=True)
        await _set_download_error(download_id, f"qBittorrent error: {e}")
        raise
    except Exception as e:
        LOGGER.error(f"[_PROCESS_DOWNLOAD] Exception in qBittorrent: {e} for {download_id}", exc_info=True)
        await _set_download_error(download_id, f"qBittorrent error: {e}")
        raise


async def _handle_direct_download(listener, destination: str, download_id: str):
    """Handle direct downloads with Aria2"""
    LOGGER.info(f"[_PROCESS_DOWNLOAD] Detected direct link, using Aria2 for {download_id}")
    if not await _init_aria2_if_needed(download_id):
        return
    try:
        from bot.helper.mirror_leech_utils.download_utils.aria2_download import add_aria2_download
        LOGGER.info(f"[_PROCESS_DOWNLOAD] Imported add_aria2_download successfully for {download_id}")
        await add_aria2_download(listener, destination, "", 0, 0)
        LOGGER.info(f"Queued to Aria2: {download_id}")
    except ImportError as ie:
        LOGGER.error(f"[_PROCESS_DOWNLOAD] ImportError in Aria2: {ie} for {download_id}")
        await _set_download_error(download_id, f"Aria2 import failed: {ie}")
        raise
    except (AttributeError, TypeError) as e:
        LOGGER.error(f"[_PROCESS_DOWNLOAD] Aria2 client error: {e} for {download_id}", exc_info=True)
        await _set_download_error(download_id, f"Aria2 client error: {e}")
        raise
    except Exception as e:
        LOGGER.error(f"[_PROCESS_DOWNLOAD] Exception in Aria2: {e} for {download_id}", exc_info=True)
        await _set_download_error(download_id, f"Aria2 error: {e}")
        raise


async def _handle_mirror_operation(listener, destination: str, download_id: str, url: str):
    """Handle mirror/qm/qb_mirror operations"""
    LOGGER.info(f"[_PROCESS_DOWNLOAD] Operation is mirror/qm/qb_mirror for {download_id}")
    if url.startswith("magnet:") or url.lower().endswith((".torrent", ".torr")):
        await _handle_torrent_download(listener, destination, download_id)
    else:
        await _handle_direct_download(listener, destination, download_id)


async def _handle_leech_operation(listener, destination: str, download_id: str):
    """Handle leech/qd_leech operations"""
    LOGGER.info(f"[_PROCESS_DOWNLOAD] Operation is leech/qd_leech for {download_id}")
    if not await _init_aria2_if_needed(download_id):
        return
    try:
        from bot.helper.mirror_leech_utils.download_utils.aria2_download import add_aria2_download
        LOGGER.info(f"[_PROCESS_DOWNLOAD] Imported add_aria2_download for leech {download_id}")
        await add_aria2_download(listener, destination, "", 0, 0)
        LOGGER.info(f"Leech queued to Aria2: {download_id}")
    except ImportError as ie:
        LOGGER.error(f"[_PROCESS_DOWNLOAD] ImportError in Aria2 leech: {ie} for {download_id}")
        await _set_download_error(download_id, f"Aria2 import failed: {ie}")
        raise
    except (AttributeError, TypeError) as e:
        LOGGER.error(f"[_PROCESS_DOWNLOAD] Aria2 leech error: {e} for {download_id}", exc_info=True)
        await _set_download_error(download_id, f"Aria2 client error: {e}")
        raise
    except Exception as e:
        LOGGER.error(f"[_PROCESS_DOWNLOAD] Exception in Aria2 leech: {e} for {download_id}", exc_info=True)
        await _set_download_error(download_id, f"Aria2 error: {e}")
        raise


async def _handle_jdownloader_operation(listener, destination: str, download_id: str):
    """Handle jm/jd_mirror operations"""
    LOGGER.info(f"[_PROCESS_DOWNLOAD] Operation is jm/jd_mirror for {download_id}")
    try:
        from bot.helper.mirror_leech_utils.download_utils.jd_download import add_jd_download
        LOGGER.info(f"[_PROCESS_DOWNLOAD] Imported add_jd_download for {download_id}")
        await add_jd_download(listener, destination)
        LOGGER.info(f"Queued to JDownloader: {download_id}")
    except ImportError as ie:
        LOGGER.error(f"[_PROCESS_DOWNLOAD] ImportError in JDownloader: {ie} for {download_id}")
        async with _download_lock:
            if download_id in _pending_downloads:
                _pending_downloads[download_id]["status"] = "queued"
                _pending_downloads[download_id]["message"] = f"JDownloader unavailable: {ie}"
        raise
    except Exception as e:
        LOGGER.error(f"[_PROCESS_DOWNLOAD] Exception in JDownloader: {e} for {download_id}", exc_info=True)
        async with _download_lock:
            if download_id in _pending_downloads:
                _pending_downloads[download_id]["status"] = "queued"
                _pending_downloads[download_id]["message"] = f"Error: {e}"
        raise


class MockMessage:
    """Mock Telegram message object for admin downloads"""
    def __init__(self, user_id: int, download_id: str):
        self.chat = type('obj', (object,), {'id': user_id})()
        self.from_user = type('obj', (object,), {'id': user_id})()
        self.message_id = hash(download_id) % 1000000
        self.text = f"Admin Download {download_id[:8]}"


async def _monitor_task_dict_downloads():
    """Monitor active downloads in task_dict for progress updates"""
    try:
        from bot import task_dict, task_dict_lock

        async with task_dict_lock:
            task_items = list(task_dict.items())

        current_in_task_dict = set()
        for listener_mid, status_obj in task_items:
            if listener_mid not in _pending_downloads:
                continue

            current_in_task_dict.add(listener_mid)
            try:
                await _process_task_dict_download(listener_mid, status_obj)
            except Exception as e:
                LOGGER.debug(f"[PROCESSOR] Error monitoring {listener_mid}: {e}")

        return current_in_task_dict
    except ImportError:
        return set()
    except Exception as e:
        LOGGER.debug(f"[PROCESSOR] Error checking task_dict: {e}")
        return set()


def _extract_download_progress(download_info):
    current = int(download_info.get('completedLength', '0'))
    total = int(download_info.get('totalLength', '0'))
    speed = int(download_info.get('downloadSpeed', '0'))
    aria2_status = download_info.get('status', '')
    return current, total, speed, aria2_status


def _is_completed_download(current: int, total: int, aria2_status: str) -> bool:
    return total > 0 and current >= total and aria2_status == 'complete'


async def _handle_completed_task_dict_download(listener_mid, status_obj, total: int) -> None:
    if listener_mid in _completion_called:
        return
    LOGGER.info(f"[PROCESSOR] Download {listener_mid} completed (100%), size={total} bytes")
    _completion_called.add(listener_mid)
    await status_obj.listener.on_download_complete(total_size=total)
    _tracked_in_task_dict.discard(listener_mid)


async def _update_task_dict_download_progress(
    listener_mid,
    status_obj,
    current: int,
    total: int,
    speed: int,
) -> None:
    if total <= 0:
        return
    listener = status_obj.listener
    last_speed = _last_speed_update.get(listener_mid, 0)
    last_current = _pending_downloads[listener_mid].get('current', 0)
    if speed == last_speed and current == last_current:
        return
    _last_speed_update[listener_mid] = speed
    await listener.on_download_progress(current, total, speed)


async def _process_task_dict_download(listener_mid, status_obj) -> None:
    await status_obj.update()
    download_info = status_obj._download
    current, total, speed, aria2_status = _extract_download_progress(download_info)

    if _is_completed_download(current, total, aria2_status):
        await _handle_completed_task_dict_download(listener_mid, status_obj, total)
        return

    await _update_task_dict_download_progress(listener_mid, status_obj, current, total, speed)


async def _handle_disappeared_downloads(disappeared: set):
    """Handle downloads that disappeared from task_dict"""
    for listener_mid in disappeared:
        if listener_mid in _pending_downloads and listener_mid not in _completion_called:
            download_status = _pending_downloads[listener_mid].get('status', '')
            if download_status == 'downloading':
                LOGGER.info(f"[PROCESSOR] Download {listener_mid} disappeared from task_dict - marking complete")
                _completion_called.add(listener_mid)
                try:
                    listener_data = _pending_downloads[listener_mid]
                    total_size = listener_data.get('total', 0)
                    if 'listener' in listener_data:
                        await listener_data['listener'].on_download_complete(total_size=total_size)
                    else:
                        async with _download_lock:
                            _pending_downloads[listener_mid]["status"] = "downloaded"
                            _pending_downloads[listener_mid]["message"] = "Download completed"
                        LOGGER.info(f"[PROCESSOR] Marked {listener_mid} as downloaded")
                except Exception as e:
                    LOGGER.error(f"[PROCESSOR] Error marking completion for {listener_mid}: {e}")


async def _cleanup_old_downloads():
    """Clean up old completed downloads"""
    import time
    current_time = time.time()
    async with _download_lock:
        to_remove = []
        for dl_id, dl_data in _pending_downloads.items():
            status = dl_data.get('status', '')
            if status in ['downloaded', 'upload_completed', 'error']:
                if 'completed_at' not in dl_data:
                    dl_data['completed_at'] = current_time
                elif current_time - dl_data['completed_at'] > 60:
                    to_remove.append(dl_id)

        for dl_id in to_remove:
            LOGGER.info(f"[PROCESSOR] Cleaning up old download {dl_id}")
            _pending_downloads.pop(dl_id, None)
            _completion_called.discard(dl_id)
            _last_speed_update.pop(dl_id, None)


class AdminDownloadHandler:
    """Handle downloads triggered from admin panel"""

    @staticmethod
    async def process_pending_downloads():
        """Check for pending admin downloads and process them"""
        try:
            global _pending_downloads, _last_speed_update, _tracked_in_task_dict, _completion_called

            LOGGER.info("[PROCESSOR] Checking downloads...")

            async with _download_lock:
                download_ids = list(_pending_downloads.keys())

            if download_ids:
                LOGGER.info(f"[PROCESSOR] Found {len(download_ids)} downloads to process: {download_ids}")
            else:
                LOGGER.info("[PROCESSOR] No pending downloads to process")

            for download_id in download_ids:
                async with _download_lock:
                    if download_id not in _pending_downloads:
                        continue
                    data = _pending_downloads[download_id]
                    status = data.get("status", "pending")

                LOGGER.info(f"[PROCESSOR] Processing download {download_id}: status={status}")

                if status == "pending":
                    LOGGER.info(f"[PROCESSOR] Calling _process_download for {download_id}")
                    await AdminDownloadHandler._process_download(download_id, data)
                    LOGGER.info(f"[PROCESSOR] Finished _process_download for {download_id}")

            # Monitor active downloads
            current_in_task_dict = await _monitor_task_dict_downloads()

            # Handle disappeared downloads
            disappeared = _tracked_in_task_dict - current_in_task_dict
            if disappeared:
                await _handle_disappeared_downloads(disappeared)

            # Update tracked set
            _tracked_in_task_dict = current_in_task_dict

            # Clean up old downloads
            await _cleanup_old_downloads()

        except Exception as e:
            LOGGER.error(f"Error processing admin downloads: {e}", exc_info=True)

    @staticmethod
    async def _initialize_download_state(download_id: str, url: str, operation: str):
        """Initialize download state in tracking dictionary"""
        async with _download_lock:
            if download_id in _pending_downloads:
                _pending_downloads[download_id]["status"] = "processing"
                _pending_downloads[download_id]["message"] = "Initializing download client..."
        LOGGER.info(f"Processing admin download: {operation} - {url}")
    
    async def _create_and_attach_listener(download_id: str, operation: str, url: str):
        """Create listener and attach to download tracking"""
        listener = AdminDownloadListener(download_id, operation, url)
        LOGGER.info(f"[_PROCESS_DOWNLOAD] Created listener for {download_id}")
        async with _download_lock:
            if download_id in _pending_downloads:
                _pending_downloads[download_id]["listener"] = listener
        return listener
    
    async def _route_to_handler(operation: str, listener, destination: str, download_id: str, url: str):
        """Route download to appropriate handler based on operation"""
        if operation in ["mirror", "qm", "qb_mirror"]:
            await _handle_mirror_operation(listener, destination, download_id, url)
        elif operation in ["leech", "qd_leech"]:
            await _handle_leech_operation(listener, destination, download_id)
        elif operation in ["jm", "jd_mirror"]:
            await _handle_jdownloader_operation(listener, destination, download_id)
        else:
            LOGGER.warning(f"[_PROCESS_DOWNLOAD] Unknown operation: {operation} for {download_id}")
            async with _download_lock:
                if download_id in _pending_downloads:
                    _pending_downloads[download_id]["status"] = "error"
                    _pending_downloads[download_id]["message"] = f"Unknown operation: {operation}"
    
    async def _update_success_status(download_id: str, operation: str):
        """Update download status to queued after successful handler execution"""
        LOGGER.info(f"[_PROCESS_DOWNLOAD] Handler completed successfully, updating to queued for {download_id}")
        async with _download_lock:
            if download_id in _pending_downloads:
                current_status = _pending_downloads[download_id].get("status", "pending")
                if current_status == "processing":
                    _pending_downloads[download_id]["status"] = "queued"
                    _pending_downloads[download_id]["message"] = f"Download queued ({operation})"
    
    async def _handle_processing_error(download_id: str, error: Exception, operation: str):
        """Handle errors during download processing"""
        LOGGER.error(f"[_PROCESS_DOWNLOAD] Handler error: {error} for {download_id}", exc_info=True)
        async with _download_lock:
            if download_id in _pending_downloads:
                _pending_downloads[download_id]["status"] = "queued"
                _pending_downloads[download_id]["message"] = f"Error: {error}"
    
    async def _process_download(download_id: str, data: Dict[str, Any]):
        """Process a single download request"""
        try:
            url = data.get("url", "")
            operation = data.get("operation", "mirror")
            destination = _normalize_destination(data.get("destination", "/app/downloads"))

            LOGGER.info(f"[_PROCESS_DOWNLOAD] START: id={download_id}, url={url[:50] if url else 'EMPTY'}, op={operation}")

            if not url:
                await _set_download_error(download_id, "No URL provided")
                return

            await _initialize_download_state(download_id, url, operation)

            try:
                listener = await _create_and_attach_listener(download_id, operation, url)
                
                try:
                    await _route_to_handler(operation, listener, destination, download_id, url)
                    await _update_success_status(download_id, operation)
                except Exception as handler_error:
                    await _handle_processing_error(download_id, handler_error, operation)

            except Exception as handler_error:
                LOGGER.error(f"Error queuing download to handler: {handler_error}", exc_info=True)
                async with _download_lock:
                    if download_id in _pending_downloads:
                        _pending_downloads[download_id]["status"] = "queued"
                        _pending_downloads[download_id]["message"] = f"Queued to {operation}"

        except Exception as e:
            LOGGER.error(f"Error processing download {download_id}: {e}", exc_info=True)
            async with _download_lock:
                if download_id in _pending_downloads:
                    _pending_downloads[download_id]["status"] = "queued"
                    _pending_downloads[download_id]["message"] = "Download queued (processing)"


class AdminDownloadListener:
    """Listener for admin-initiated downloads - implements download callbacks"""

    def __init__(self, download_id: str, operation: str, url: str = ""):
        self.download_id = download_id
        self.operation = operation
        self.link = url  # Expected by download handlers
        self.name = url.split("/")[-1][:50] if url else f"download_{download_id[:8]}"
        self.user_id = Config.OWNER_ID  # Use bot owner as user
        self.message = MockMessage(self.user_id, download_id)  # Mock message for compatibility
        self.upload_details = {}
        self.is_cancelled = False
        self.progress = 0
        self.speed = 0
        self.size = 0
        self.is_file = False

        # Add required attributes for compatibility with download handlers
        self.mid = download_id  # Message ID for task_dict tracking
        self.select = False  # File selection not enabled for admin downloads
        self.multi = 1  # Single download
        self.is_rss = False  # Not an RSS download
        self.is_super_chat = False
        self.subname = ""

        # Upload-related attributes
        self.is_leech = operation in ["leech", "qd_leech"]
        self.up_dest = f"mtp:{Config.GDRIVE_ID}" if hasattr(Config, 'GDRIVE_ID') and Config.GDRIVE_ID else ""
        self.user_dict = {}  # User settings for leech
        self.thumb = f"thumbnails/{self.user_id}.jpg"
        self.user_transmission = False
        self.client = None  # Will be set from bot context
        self.tag = f"@admin_{download_id[:8]}"  # Tag for leech uploads

        LOGGER.info(f"[LISTENER] Created listener for {download_id}: name={self.name}, link={self.link[:50] if self.link else 'NONE'}")

    async def on_download_start(self):
        """Called when download starts"""
        LOGGER.info(f"[LISTENER] on_download_start called for {self.download_id}")
        async with _download_lock:
            if self.download_id in _pending_downloads:
                _pending_downloads[self.download_id]["status"] = "downloading"
                _pending_downloads[self.download_id]["message"] = "Download in progress"

        # Record in history database
        try:
            destination = _pending_downloads.get(self.download_id, {}).get("destination", "/app/downloads")
            history_db.add_download(
                download_id=self.download_id,
                url=self.link,
                operation=self.operation,
                destination=destination
            )
            history_db.update_download_status(self.download_id, "downloading")
        except Exception as e:
            LOGGER.warning(f"Failed to record download in history: {e}")

        # Broadcast via WebSocket
        try:
            from web.websocket_handler import broadcast_download_progress, broadcast_notification
            broadcast_download_progress(
                self.download_id,
                progress=0,
                speed=0,
                status="downloading",
                message="Download started"
            )
            broadcast_notification("Download Started", f"Started downloading: {self.name}", "info")
        except Exception as e:
            LOGGER.warning(f"WebSocket broadcast failed: {e}")

        LOGGER.info(f"Admin download {self.download_id} started")

    async def _start_leech_upload(self, download_path: str):
        """Start Telegram upload for leech operation"""
        try:
            LOGGER.info(f"[LEECH] Starting Telegram upload: {download_path}")

            async with _download_lock:
                if self.download_id in _pending_downloads:
                    _pending_downloads[self.download_id]["status"] = "uploading"
                    _pending_downloads[self.download_id]["message"] = "Uploading to Telegram..."

            # Run upload on bot event loop to avoid cross-loop issues
            import asyncio
            from asyncio import run_coroutine_threadsafe

            from bot import bot_loop

            async def _upload():
                from bot import task_dict, task_dict_lock
                from bot.core.telegram_manager import TgClient
                from bot.helper.mirror_leech_utils.status_utils.telegram_status import TelegramStatus
                from bot.helper.mirror_leech_utils.telegram_uploader import TelegramUploader

                self.client = TgClient.user or TgClient.bot
                if not self.client:
                    raise RuntimeError("Telegram client not initialized")

                tg_uploader = TelegramUploader(self, download_path)
                async with task_dict_lock:
                    task_dict[self.mid] = TelegramStatus(self, tg_uploader, self.download_id, "up")
                await tg_uploader.upload()
                LOGGER.info(f"[LEECH] Telegram upload completed: {self.download_id}")

            future = run_coroutine_threadsafe(_upload(), bot_loop)
            await asyncio.wrap_future(future)

        except Exception as e:
            LOGGER.error(f"[LEECH] Error starting Telegram upload: {e}", exc_info=True)
            await self.on_upload_error(str(e))

    async def _start_mirror_upload(self, download_path: str):
        """Start Google Drive/Rclone upload for mirror operation"""
        try:
            LOGGER.info(f"[MIRROR] Starting upload: {download_path}")

            async with _download_lock:
                if self.download_id in _pending_downloads:
                    _pending_downloads[self.download_id]["status"] = "uploading"
                    _pending_downloads[self.download_id]["message"] = "Uploading to Drive..."

            # Run upload on bot event loop to avoid cross-loop issues
            import asyncio
            from asyncio import run_coroutine_threadsafe

            from bot import bot_loop

            async def _upload():
                from bot import task_dict, task_dict_lock
                from bot.helper.ext_utils.links_utils import is_gdrive_id

                if is_gdrive_id(self.up_dest):
                    from bot.helper.mirror_leech_utils.gdrive_utils.upload import GoogleDriveUpload
                    from bot.helper.mirror_leech_utils.status_utils.gdrive_status import GoogleDriveStatus

                    drive = GoogleDriveUpload(self, download_path)
                    async with task_dict_lock:
                        task_dict[self.mid] = GoogleDriveStatus(self, drive, self.download_id, "up")

                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, drive.upload)
                    LOGGER.info(f"[MIRROR] Google Drive upload completed: {self.download_id}")
                else:
                    from bot.helper.mirror_leech_utils.rclone_utils.transfer import RcloneTransferHelper
                    from bot.helper.mirror_leech_utils.status_utils.rclone_status import RcloneStatus

                    rc_transfer = RcloneTransferHelper(self)
                    async with task_dict_lock:
                        task_dict[self.mid] = RcloneStatus(self, rc_transfer, self.download_id, "up")
                    await rc_transfer.upload(download_path)
                    LOGGER.info(f"[MIRROR] Rclone upload completed: {self.download_id}")

            future = run_coroutine_threadsafe(_upload(), bot_loop)
            await asyncio.wrap_future(future)

        except Exception as e:
            LOGGER.error(f"[MIRROR] Error starting upload: {e}", exc_info=True)
            await self.on_upload_error(str(e))

    async def on_download_progress(self, current, total, speed):
        """Called during download progress"""
        global _pending_downloads
        try:
            progress = (current / total * 100) if total > 0 else 0
            self.progress = progress
            self.speed = speed
            async with _download_lock:
                if self.download_id in _pending_downloads:
                    _pending_downloads[self.download_id].update({
                        "progress": progress,
                        "speed": speed,
                        "current": current,
                        "total": total,
                        "status": "downloading"
                    })

            # Record progress in history (throttle to every 10%)
            if int(progress) % 10 == 0:
                try:
                    history_db.record_progress(self.download_id, progress, speed)
                except Exception as e:
                    LOGGER.debug(f"Failed to record progress: {e}")

            # Broadcast via WebSocket (throttle to every 2%)
            if int(progress) % 2 == 0:
                try:
                    from web.websocket_handler import broadcast_download_progress
                    broadcast_download_progress(
                        self.download_id,
                        progress=progress,
                        speed=speed,
                        status="downloading",
                        current=current,
                        total=total
                    )
                except Exception as e:
                    LOGGER.debug(f"WebSocket broadcast failed: {e}")

        except Exception as e:
            LOGGER.error(f"Error updating progress for {self.download_id}: {e}")

    async def _mark_download_complete(self, total_size: int) -> None:
        async with _download_lock:
            if self.download_id in _pending_downloads:
                _pending_downloads[self.download_id]["status"] = "downloaded"
                _pending_downloads[self.download_id]["message"] = "Download completed, preparing upload..."
                if total_size > 0:
                    _pending_downloads[self.download_id]["total_size"] = total_size

    def _update_history_on_complete(self, total_size: int) -> None:
        if total_size <= 0:
            return
        conn = history_db._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
                    UPDATE downloads
                    SET total_size = ?, downloaded_size = ?, status = 'uploading', completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
            (total_size, total_size, self.download_id),
        )
        conn.commit()
        conn.close()
        LOGGER.info(f"Updated download {self.download_id} with size {total_size} bytes")

    async def _resolve_download_path(self) -> str:
        from os import path as ospath
        from bot import task_dict, task_dict_lock

        download_path = None
        async with task_dict_lock:
            if self.download_id in task_dict:
                status_obj = task_dict[self.download_id]
                download_info = status_obj._download
                if 'files' in download_info and len(download_info['files']) > 0:
                    download_path = download_info['files'][0].get('path', '')
                    if download_path:
                        self.name = ospath.basename(download_path)
                        self.is_file = True

        if not download_path:
            return f"/downloads/{self.name}"
        return download_path

    async def _start_upload_for_path(self, download_path: str) -> None:
        LOGGER.info(
            f"[UPLOAD] Starting upload for {self.download_id}, path={download_path}, is_leech={self.is_leech}"
        )
        if self.is_leech:
            await self._start_leech_upload(download_path)
            return
        await self._start_mirror_upload(download_path)

    def _broadcast_download_completed(self) -> None:
        from web.websocket_handler import broadcast_download_progress, broadcast_notification

        broadcast_download_progress(
            self.download_id,
            progress=100,
            speed=0,
            status="downloaded",
            message="Download completed"
        )
        broadcast_notification("Download Complete", f"Completed: {self.name}", "success")

    async def on_download_complete(self, total_size: int = 0):
        """Called when download completes - triggers upload"""
        self.size = total_size

        await self._mark_download_complete(total_size)

        # Update in history database with file size
        try:
            self._update_history_on_complete(total_size)
        except Exception as e:
            LOGGER.warning(f"Failed to update history: {e}")

        # Get download path from Aria2
        try:
            download_path = await self._resolve_download_path()
            await self._start_upload_for_path(download_path)

        except Exception as e:
            LOGGER.error(f"Error starting upload for {self.download_id}: {e}", exc_info=True)
            await self.on_upload_error(str(e))

        # Broadcast via WebSocket
        try:
            self._broadcast_download_completed()
        except Exception as e:
            LOGGER.warning(f"WebSocket broadcast failed: {e}")

        LOGGER.info(f"Admin download {self.download_id} completed")

    async def on_download_error(self, error: str):
        """Called when download errors"""
        LOGGER.error(f"[LISTENER] on_download_error called for {self.download_id}: {error}")
        async with _download_lock:
            if self.download_id in _pending_downloads:
                _pending_downloads[self.download_id]["status"] = "error"
                _pending_downloads[self.download_id]["error"] = error
                _pending_downloads[self.download_id]["message"] = f"Error: {error}"

        # Update in history database
        try:
            history_db.update_download_status(self.download_id, "error", error=error)
        except Exception as e:
            LOGGER.warning(f"Failed to update history: {e}")

        # Broadcast via WebSocket
        try:
            from web.websocket_handler import broadcast_download_progress, broadcast_notification
            broadcast_download_progress(
                self.download_id,
                progress=0,
                speed=0,
                status="error",
                error=error,
                message=f"Error: {error}"
            )
            broadcast_notification("Download Failed", f"Error in {self.name}: {error}", "error")
        except Exception as e:
            LOGGER.warning(f"WebSocket broadcast failed: {e}")

        LOGGER.error(f"Admin download {self.download_id} error: {error}")

    async def on_upload_error(self, error: str):
        """Called when upload errors"""
        LOGGER.error(f"[LISTENER] on_upload_error called for {self.download_id}: {error}")
        async with _download_lock:
            if self.download_id in _pending_downloads:
                _pending_downloads[self.download_id]["status"] = "error"
                _pending_downloads[self.download_id]["error"] = error
                _pending_downloads[self.download_id]["message"] = f"Upload error: {error}"

        # Update in history database
        try:
            history_db.update_download_status(self.download_id, "error", error=error)
        except Exception as e:
            LOGGER.warning(f"Failed to update history: {e}")

        # Broadcast via WebSocket
        try:
            from web.websocket_handler import broadcast_download_progress, broadcast_notification
            broadcast_download_progress(
                self.download_id,
                progress=0,
                speed=0,
                status="error",
                error=error,
                message=f"Upload error: {error}"
            )
            broadcast_notification("Upload Failed", f"Error uploading {self.name}: {error}", "error")
        except Exception as e:
            LOGGER.warning(f"WebSocket broadcast failed: {e}")

        LOGGER.error(f"Admin upload {self.download_id} error: {error}")

    async def on_upload_started(self):
        """Called when upload starts"""
        async with _download_lock:
            if self.download_id in _pending_downloads:
                _pending_downloads[self.download_id]["status"] = "uploading"

    async def on_upload_progress(self, current, total):
        """Called during upload progress"""
        global _pending_downloads
        progress = (current / total * 100) if total > 0 else 0
        async with _download_lock:
            if self.download_id in _pending_downloads:
                _pending_downloads[self.download_id]["upload_progress"] = progress

    async def on_upload_complete(self, link: str, files: int = 0, folders: int = 0, mime_type: str = "", rclone_path: str = "", dir_id: str = ""):
        """Called when upload completes"""
        LOGGER.info(f"[LISTENER] on_upload_complete called for {self.download_id}, link={link}, files={files}, folders={folders}")
        async with _download_lock:
            if self.download_id in _pending_downloads:
                _pending_downloads[self.download_id]["status"] = "completed"
                _pending_downloads[self.download_id]["link"] = link
                _pending_downloads[self.download_id]["message"] = "Upload completed"
                _pending_downloads[self.download_id]["files_count"] = files
                _pending_downloads[self.download_id]["folders_count"] = folders
                _pending_downloads[self.download_id]["mime_type"] = mime_type

        # Update in history database
        try:
            history_db.update_download_status(self.download_id, "completed")
        except Exception as e:
            LOGGER.warning(f"Failed to update history: {e}")

        # Broadcast via WebSocket
        try:
            from web.websocket_handler import broadcast_download_progress, broadcast_notification

            # Format message based on operation type
            if self.is_leech:
                message = f"Uploaded {files} file(s) to Telegram"
            else:
                message = f"Uploaded to Drive: {mime_type}"

            broadcast_download_progress(
                self.download_id,
                progress=100,
                speed=0,
                status="completed",
                link=link,
                message=message
            )
            broadcast_notification("Upload Complete", f"Successfully uploaded: {self.name}", "success")
        except Exception as e:
            LOGGER.warning(f"WebSocket broadcast failed: {e}")

        LOGGER.info(f"Admin download {self.download_id} uploaded: {link}")


# Background task to process downloads
async def start_admin_download_processor():
    """Start background task to process admin downloads"""
    LOGGER.info("🚀 Starting admin download processor...")

    loop_count = 0
    while True:
        try:
            loop_count += 1
            if loop_count % 12 == 0:  # Log every 60 seconds (12 * 5second cycles)
                LOGGER.info(f"[PROCESSOR-LOOP] Cycle #{loop_count} - still running...")
            await AdminDownloadHandler.process_pending_downloads()
        except Exception as e:
            LOGGER.error(f"Error in admin download processor: {e}", exc_info=True)

        # Check every 5 seconds
        await asyncio.sleep(5)
