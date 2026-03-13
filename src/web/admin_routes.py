"""Admin dashboard routes and API endpoints"""
import os
from datetime import datetime, timedelta
from logging import getLogger
from typing import Any, Dict, List, Optional

import psutil
from fastapi import APIRouter, Depends, HTTPException, WebSocket, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from bot.core.config_manager import Config
from web.admin_auth import AdminAuth, get_admin_credentials
from web.download_history import DownloadHistory
from web.scheduled_downloads import ScheduledDownloads
from web.torrent_file_browser import TorrentFileBrowser

LOGGER = getLogger(__name__)

# Initialize history database
history_db = DownloadHistory("/app/data/download_history.db")
# Initialize scheduled downloads
scheduled_db = ScheduledDownloads("/app/data/scheduled_downloads.db")

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBearer()


# Request/Response Models
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class DownloadRequest(BaseModel):
    url: str
    operation: str  # mirror, leech, qm, qb_mirror, jm, jd_mirror
    destination: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class DownloadStatus(BaseModel):
    gid: str
    name: str
    progress: float
    speed: float
    status: str
    eta: str
    size: str


# Phase 5: Request Models
class BatchDownloadRequest(BaseModel):
    urls: List[str]
    operation: str
    destination: Optional[str] = None


class ScheduleDownloadRequest(BaseModel):
    download_id: str
    url: str
    operation: str
    schedule_type: str = "once"
    schedule_data: Optional[Dict] = None
    destination: Optional[str] = None


class TemplateRequest(BaseModel):
    template_id: str
    name: str
    operation: str
    destination: Optional[str] = None
    options: Optional[Dict] = None
    description: Optional[str] = None

class SystemStats(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_used_gb: float
    disk_total_gb: float
    uptime_hours: float


# Dependency for verifying admin token
async def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token from Authorization header"""
    try:
        payload = AdminAuth.verify_token(credentials.credentials)
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return {"username": username}
    except HTTPException:
        raise


# Routes

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Admin login endpoint"""
    # Get admin credentials
    admin_credentials = get_admin_credentials()

    # Check if user exists in admin credentials
    if request.username not in admin_credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Verify password
    if not AdminAuth.verify_password(request.password, admin_credentials[request.username]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Create token
    token = AdminAuth.create_access_token(
        data={"sub": request.username},
        expires_delta=timedelta(hours=24)
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 24 * 3600
    }


@router.get("/dashboard")
async def dashboard():
    """Get admin dashboard HTML (auth checked by JavaScript)"""
    dashboard_html = get_dashboard_html()
    return HTMLResponse(content=dashboard_html)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    from web.websocket_handler import handle_websocket_client
    await handle_websocket_client(websocket)


@router.get("/api/health")
async def health_check(admin: Dict[str, Any] = Depends(verify_admin_token)):
    """Check bot and service health"""
    health_status = {
        "bot_status": "running",
        "download_queue": "operational",
        "database_status": "unknown",
        "web_server": "running",
        "qbittorrent": "unknown",
        "aria2": "unknown",
        "jdownloader": "unknown"
    }

    return health_status


@router.get("/api/stats", response_model=SystemStats)
async def get_system_stats(admin: Dict[str, Any] = Depends(verify_admin_token)):
    """Get system statistics"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('/')
    uptime_seconds = os.popen('uptime -p').read().strip() if os.name != 'nt' else "N/A"

    return SystemStats(
        cpu_percent=cpu_percent,
        memory_percent=memory_info.percent,
        disk_percent=disk_info.percent,
        memory_used_gb=memory_info.used / (1024 ** 3),
        memory_total_gb=memory_info.total / (1024 ** 3),
        disk_used_gb=disk_info.used / (1024 ** 3),
        disk_total_gb=disk_info.total / (1024 ** 3),
        uptime_hours=0
    )


@router.get("/api/downloads")
async def get_downloads(admin: Dict[str, Any] = Depends(verify_admin_token)):
    """Get list of admin-initiated downloads"""
    try:
        from web.admin_download_handler import _download_lock, _pending_downloads

        # Get all downloads from in-memory storage
        async with _download_lock:
            downloads = []
            for download_id, data in _pending_downloads.items():
                downloads.append({
                    "id": download_id,
                    "url": data.get("url", ""),
                    "operation": data.get("operation", ""),
                    "status": data.get("status", "unknown"),
                    "progress": data.get("progress", 0),
                    "speed": data.get("speed", 0),
                    "error": data.get("error", ""),
                    "message": data.get("message", "")
                })

        return {"downloads": downloads}
    except Exception as e:
        LOGGER.error(f"Error getting downloads: {e}")
        return {"downloads": [], "error": str(e)}


@router.post("/api/download/start")
async def start_download(request: DownloadRequest, admin: Dict[str, Any] = Depends(verify_admin_token)):
    """Start a new download operation"""
    try:
        import uuid

        from web.admin_download_handler import _download_lock, _pending_downloads

        # Validate input
        if not request.url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL is required"
            )

        if request.operation not in ["mirror", "leech", "qm", "jm", "qb_mirror"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid operation: {request.operation}"
            )

        # Store download request in in-memory queue
        download_id = str(uuid.uuid4())
        download_data = {
            "url": request.url,
            "operation": request.operation,
            "destination": request.destination or getattr(Config, 'DEFAULT_UPLOAD', '/app/downloads'),
            "status": "pending",
            "created_at": str(os.popen('date').read().strip()),
            "username": admin["username"],
            "progress": 0,
            "speed": 0
        }

        if request.options:
            download_data.update(request.options)

        # Add to pending downloads
        async with _download_lock:
            _pending_downloads[download_id] = download_data

        LOGGER.info(f"Admin download queued: {download_id} - {request.operation} - {request.url}")

        return {
            "status": "success",
            "download_id": download_id,
            "message": f"Download queued for {request.operation}"
        }
    except Exception as e:
        LOGGER.error(f"Error queuing download: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error queuing download: {str(e)}"
        )


@router.post("/api/download/{download_id}/cancel")
async def cancel_download(download_id: str, admin: Dict[str, Any] = Depends(verify_admin_token)):
    """Cancel an active download"""
    try:
        from web.admin_download_handler import _download_lock, _pending_downloads

        async with _download_lock:
            if download_id in _pending_downloads:
                _pending_downloads[download_id]["status"] = "cancelled"
                LOGGER.info(f"Download cancelled: {download_id}")
                return {
                    "status": "success",
                    "message": f"Download {download_id} cancelled"
                }

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Download {download_id} not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling download: {str(e)}"
        )


@router.post("/api/download/{download_id}/pause")
async def pause_download(download_id: str, admin: Dict[str, Any] = Depends(verify_admin_token)):
    """Pause an active download"""
    try:
        from web.admin_download_handler import _download_lock, _pending_downloads

        async with _download_lock:
            if download_id in _pending_downloads:
                _pending_downloads[download_id]["status"] = "paused"
                LOGGER.info(f"Download paused: {download_id}")
                return {
                    "status": "success",
                    "message": f"Download {download_id} paused"
                }

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Download {download_id} not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error pausing download: {str(e)}"
        )


@router.get("/api/config")
async def get_config(admin: Dict[str, Any] = Depends(verify_admin_token)):
    """Get current bot configuration (sanitized)"""
    config_data = {
        "bot_name": "Mirror Leech Bot",
        "version": "1.0.0",
        "default_upload": Config.DEFAULT_UPLOAD,
        "status_limit": Config.STATUS_LIMIT,
        "index_url": Config.INDEX_URL if Config.INDEX_URL else "Not configured",
        "rclone_enabled": bool(Config.RCLONE_PATH),
        "jdownloader_enabled": bool(Config.JD_EMAIL),
        "qbittorrent_enabled": True,
        "aria2_enabled": True,
    }
    return config_data


# Phase 4: Torrent File Browser Endpoints
@router.get("/api/torrent/{torrent_hash}/files")
async def get_torrent_files(
    torrent_hash: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get file tree for a torrent from qBittorrent or Aria2"""
    auth = AdminAuth()
    if not auth.verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        browser = TorrentFileBrowser()

        # Try to get from qBittorrent first
        try:
            qb_data = await get_qb_torrent_files(torrent_hash)
            if qb_data:
                metadata = browser.parse_torrent_metadata(qb_data)
                return JSONResponse({
                    "success": True,
                    "source": "qbittorrent",
                    "metadata": metadata.get_metadata()
                })
        except Exception as qb_err:
            LOGGER.debug(f"qBittorrent lookup failed: {qb_err}")

        # Try Aria2 as fallback
        try:
            aria2_data = await get_aria2_torrent_files(torrent_hash)
            if aria2_data:
                metadata = browser.parse_torrent_metadata(aria2_data)
                return JSONResponse({
                    "success": True,
                    "source": "aria2",
                    "metadata": metadata.get_metadata()
                })
        except Exception as aria2_err:
            LOGGER.debug(f"Aria2 lookup failed: {aria2_err}")

        raise HTTPException(status_code=404, detail="Torrent not found")
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"Error fetching torrent files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/torrent/{torrent_hash}/select")
async def select_torrent_files(
    torrent_hash: str,
    file_indices: List[int],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Select specific files in a torrent"""
    auth = AdminAuth()
    if not auth.verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        # Try qBittorrent first
        try:
            await select_qb_files(torrent_hash, file_indices)
            return JSONResponse({
                "success": True,
                "source": "qbittorrent",
                "message": f"Selected {len(file_indices)} files"
            })
        except Exception as qb_err:
            LOGGER.debug(f"qBittorrent select failed: {qb_err}")

        # Try Aria2
        try:
            await select_aria2_files(torrent_hash, file_indices)
            return JSONResponse({
                "success": True,
                "source": "aria2",
                "message": f"Selected {len(file_indices)} files"
            })
        except Exception as aria2_err:
            LOGGER.debug(f"Aria2 select failed: {aria2_err}")

        raise HTTPException(status_code=404, detail="Could not select files in any client")
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"Error selecting files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/torrent/{torrent_hash}/select-pattern")
async def select_files_by_pattern(
    torrent_hash: str,
    pattern: str,
    pattern_type: str = "fnmatch",
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Select files matching a pattern (fnmatch or regex)"""
    auth = AdminAuth()
    if not auth.verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    async def _find_torrent_files(hash_value: str):
        try:
            return await get_qb_torrent_files(hash_value), "qbittorrent"
        except:
            pass
        try:
            return await get_aria2_torrent_files(hash_value), "aria2"
        except:
            return None, None

    async def _apply_pattern_selection(hash_value: str, source_name: str, file_indices: List[int]):
        if source_name == "qbittorrent":
            await select_qb_files(hash_value, file_indices)
            return
        await select_aria2_files(hash_value, file_indices)

    try:
        browser = TorrentFileBrowser()

        # Get torrent files
        torrent_data, source = await _find_torrent_files(torrent_hash)

        if not torrent_data:
            raise HTTPException(status_code=404, detail="Torrent not found")

        browser.parse_torrent_metadata(torrent_data)
        selected = browser.select_files_by_pattern(pattern, pattern_type)

        # Apply selection to appropriate client
        file_indices = [f['index'] for f in selected if 'index' in f]
        await _apply_pattern_selection(torrent_hash, source, file_indices)

        return JSONResponse({
            "success": True,
            "source": source,
            "pattern": pattern,
            "pattern_type": pattern_type,
            "files_selected": len(selected),
            "total_size": sum(f.get('size', 0) for f in selected)
        })
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"Error selecting by pattern: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Phase 4: Download History & Analytics Endpoints
@router.get("/api/history")
async def get_download_history_api(
    limit: int = 100,
    operation: Optional[str] = None,
    days: int = 30,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get download history with optional operation filter"""
    auth = AdminAuth()
    if not auth.verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        history = history_db.get_download_history(limit=limit, operation=operation)
        return JSONResponse({
            "success": True,
            "count": len(history),
            "downloads": history
        })
    except Exception as e:
        LOGGER.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/history/stats")
async def get_history_statistics(
    days: int = 30,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get aggregated download statistics"""
    auth = AdminAuth()
    if not auth.verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        stats = history_db.get_statistics(days=days)
        return JSONResponse({
            "success": True,
            "days": days,
            "statistics": stats
        })
    except Exception as e:
        LOGGER.error(f"Error fetching statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/history/success-rate")
async def get_success_rates(
    days: int = 30,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get success rates by operation type"""
    auth = AdminAuth()
    if not auth.verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        rates = history_db.get_success_rate(days=days)
        return JSONResponse({
            "success": True,
            "days": days,
            "success_rates": rates
        })
    except Exception as e:
        LOGGER.error(f"Error fetching success rates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/history/top-downloads")
async def get_top_downloads_api(
    limit: int = 10,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get top downloads by size"""
    auth = AdminAuth()
    if not auth.verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        top = history_db.get_top_downloads(limit=limit)
        return JSONResponse({
            "success": True,
            "limit": limit,
            "downloads": top
        })
    except Exception as e:
        LOGGER.error(f"Error fetching top downloads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions for torrent file retrieval
async def get_qb_torrent_files(torrent_hash: str):
    """Get torrent files from qBittorrent"""
    from integrations.clients.qbittorrent import QBittorrentClient
    try:
        qb = QBittorrentClient()
        return await qb.get_torrent_files(torrent_hash)
    except:
        return None


async def get_aria2_torrent_files(torrent_hash: str):
    """Get torrent files from Aria2"""
    from integrations.clients.aria2 import Aria2Client
    try:
        aria2 = Aria2Client()
        return await aria2.get_torrent_files(torrent_hash)
    except:
        return None


async def select_qb_files(torrent_hash: str, file_indices: List[int]):
    """Select files in qBittorrent torrent"""
    from integrations.clients.qbittorrent import QBittorrentClient
    try:
        qb = QBittorrentClient()
        return await qb.select_files(torrent_hash, file_indices)
    except Exception as e:
        LOGGER.error(f"qBittorrent select failed: {e}")
        raise


async def select_aria2_files(torrent_hash: str, file_indices: List[int]):
    """Select files in Aria2 torrent"""
    from integrations.clients.aria2 import Aria2Client
    try:
        aria2 = Aria2Client()
        return await aria2.select_files(torrent_hash, file_indices)
    except Exception as e:
        LOGGER.error(f"Aria2 select failed: {e}")
        raise


# Phase 5: Advanced Download Management Endpoints

# === Scheduled Downloads ===
@router.post("/api/schedules/add")
async def add_scheduled_download(
    request: ScheduleDownloadRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Add a scheduled download (one-time, daily, weekly, monthly)"""
    auth = AdminAuth()
    if not auth.verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        scheduled_db.add_scheduled_download(
            download_id=request.download_id,
            url=request.url,
            operation=request.operation,
            schedule_type=request.schedule_type,
            schedule_data=request.schedule_data,
            destination=request.destination or "/app/downloads"
        )
        return JSONResponse({
            "success": True,
            "download_id": request.download_id,
            "schedule_type": request.schedule_type,
            "message": "Scheduled download created"
        })
    except Exception as e:
        LOGGER.error(f"Error adding scheduled download: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/schedules")
async def get_scheduled_downloads(
    status: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all scheduled downloads"""
    auth = AdminAuth()
    if not auth.verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        downloads = scheduled_db.get_scheduled_downloads(status=status)
        return JSONResponse({
            "success": True,
            "count": len(downloads),
            "scheduled": downloads
        })
    except Exception as e:
        LOGGER.error(f"Error fetching schedules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/schedules/{download_id}/update")
async def update_scheduled_download(
    download_id: str,
    status: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a scheduled download status (active/paused/completed)"""
    auth = AdminAuth()
    if not auth.verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        if status:
            scheduled_db.update_scheduled_status(download_id, status)

        return JSONResponse({
            "success": True,
            "download_id": download_id,
            "status": status
        })
    except Exception as e:
        LOGGER.error(f"Error updating schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Download Templates ===
@router.post("/api/templates/add")
async def create_template(
    request: TemplateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a download template for quick reuse"""
    auth = AdminAuth()
    if not auth.verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        scheduled_db.add_template(
            template_id=request.template_id,
            name=request.name,
            operation=request.operation,
            destination=request.destination or "/app/downloads",
            options=request.options,
            description=request.description
        )
        return JSONResponse({
            "success": True,
            "template_id": request.template_id,
            "name": request.name,
            "message": "Template created"
        })
    except Exception as e:
        LOGGER.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/templates")
async def get_templates(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all download templates"""
    auth = AdminAuth()
    if not auth.verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        templates = scheduled_db.get_templates()
        return JSONResponse({
            "success": True,
            "count": len(templates),
            "templates": templates
        })
    except Exception as e:
        LOGGER.error(f"Error fetching templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/templates/{template_id}")
async def delete_template(
    template_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a download template"""
    auth = AdminAuth()
    if not auth.verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        scheduled_db.delete_template(template_id)
        return JSONResponse({
            "success": True,
            "template_id": template_id,
            "message": "Template deleted"
        })
    except Exception as e:
        LOGGER.error(f"Error deleting template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Batch Download ===
@router.post("/api/batch-download")
async def batch_download(
    request: BatchDownloadRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Add multiple URLs for download in one request"""
    auth = AdminAuth()
    if not auth.verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        if not request.urls or len(request.urls) == 0:
            raise HTTPException(status_code=400, detail="No URLs provided")

        download_ids = []
        request.destination or "/app/downloads"

        for idx, url in enumerate(request.urls):
            if url.strip():
                download_id = f"batch_{int(datetime.now().timestamp())}_{idx}"
                scheduled_db.enqueue_download(
                    download_id=download_id,
                    priority=5,
                    url=url.strip(),
                    operation=request.operation
                )
                download_ids.append(download_id)

        return JSONResponse({
            "success": True,
            "count": len(download_ids),
            "download_ids": download_ids,
            "message": f"Added {len(download_ids)} downloads to queue"
        })
    except Exception as e:
        LOGGER.error(f"Error batch downloading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Pause/Resume ===
@router.post("/api/download/{download_id}/pause")
async def pause_download(
    download_id: str,
    reason: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Pause an active download"""
    auth = AdminAuth()
    if not auth.verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        scheduled_db.pause_download(download_id, reason=reason or "User paused")

        # Broadcast pause event
        try:
            from web.websocket_handler import broadcast_notification
            broadcast_notification("Download Paused", f"Download {download_id} paused", "warning")
        except:
            pass

        return JSONResponse({
            "success": True,
            "download_id": download_id,
            "status": "paused",
            "reason": reason
        })
    except Exception as e:
        LOGGER.error(f"Error pausing download: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/download/{download_id}/resume")
async def resume_download(
    download_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Resume a paused download"""
    auth = AdminAuth()
    if not auth.verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        scheduled_db.resume_download(download_id)

        # Broadcast resume event
        try:
            from web.websocket_handler import broadcast_notification
            broadcast_notification("Download Resumed", f"Download {download_id} resumed", "success")
        except:
            pass

        return JSONResponse({
            "success": True,
            "download_id": download_id,
            "status": "resumed"
        })
    except Exception as e:
        LOGGER.error(f"Error resuming download: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Queue Management ===
@router.post("/api/queue/{download_id}/priority")
async def set_download_priority(
    download_id: str,
    priority: int = 5,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Change priority of a queued download (1=highest, 10=lowest)"""
    auth = AdminAuth()
    if not auth.verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        if priority < 1 or priority > 10:
            raise HTTPException(status_code=400, detail="Priority must be between 1 and 10")

        scheduled_db.change_priority(download_id, priority)
        return JSONResponse({
            "success": True,
            "download_id": download_id,
            "priority": priority,
            "message": "Priority updated"
        })
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"Error setting priority: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/queue/status")
async def get_queue_status(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current download queue status"""
    auth = AdminAuth()
    if not auth.verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        status = scheduled_db.get_queue_status()
        return JSONResponse({
            "success": True,
            "queue": status
        })
    except Exception as e:
        LOGGER.error(f"Error getting queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_dashboard_html() -> str:
    """Return the admin dashboard HTML with WebSocket support"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Dashboard - Mirror Leech Bot</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }

            .container {
                max-width: 1400px;
                margin: 0 auto;
            }

            .header {
                background: rgba(255, 255, 255, 0.95);
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .header h1 {
                color: #667eea;
                font-size: 28px;
            }

            .connection-status {
                display: inline-block;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 500;
                margin-right: 15px;
            }

            .connection-status.connected {
                background: #d4edda;
                color: #155724;
            }

            .connection-status.disconnected {
                background: #f8d7da;
                color: #721c24;
            }

            .logout-btn {
                background: #e74c3c;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
            }

            .logout-btn:hover {
                background: #c0392b;
            }

            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }

            .card {
                background: rgba(255, 255, 255, 0.95);
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }

            .card h2 {
                color: #667eea;
                font-size: 18px;
                margin-bottom: 15px;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }

            .stat-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
            }

            .stat {
                background: #f8f9fa;
                padding: 10px;
                border-radius: 5px;
                border-left: 4px solid #667eea;
            }

            .stat-label {
                font-size: 12px;
                color: #7f8c8d;
                text-transform: uppercase;
            }

            .stat-value {
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
                margin-top: 5px;
            }

            .download-form {
                display: grid;
                gap: 10px;
            }

            .form-group {
                display: flex;
                flex-direction: column;
            }

            .form-group label {
                font-size: 14px;
                font-weight: 500;
                color: #2c3e50;
                margin-bottom: 5px;
            }

            .form-group input,
            .form-group select {
                padding: 10px;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
            }

            .form-group input:focus,
            .form-group select:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }

            .btn {
                background: #667eea;
                color: white;
                padding: 12px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: background 0.3s ease;
            }

            .btn:hover {
                background: #5568d3;
            }

            .btn-danger {
                background: #e74c3c;
            }

            .btn-danger:hover {
                background: #c0392b;
            }

            .download-list {
                max-height: 400px;
                overflow-y: auto;
            }

            .download-item {
                background: #f8f9fa;
                padding: 12px;
                margin-bottom: 10px;
                border-radius: 5px;
                border-left: 4px solid #3498db;
                transition: all 0.3s ease;
            }

            .download-item.error {
                border-left-color: #e74c3c;
            }

            .download-item.completed {
                border-left-color: #27ae60;
            }

            .download-item-name {
                font-weight: 500;
                color: #2c3e50;
                margin-bottom: 5px;
                word-break: break-all;
            }

            .progress-bar {
                background: #ecf0f1;
                height: 8px;
                border-radius: 4px;
                overflow: hidden;
                margin: 8px 0;
            }

            .progress-fill {
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                height: 100%;
                transition: width 0.3s ease;
            }

            .download-meta {
                display: flex;
                justify-content: space-between;
                font-size: 12px;
                color: #7f8c8d;
                margin-bottom: 8px;
            }

            .download-actions {
                display: flex;
                gap: 5px;
            }

            .download-actions button {
                padding: 5px 10px;
                font-size: 12px;
                border: none;
                border-radius: 3px;
                cursor: pointer;
            }

            .status-badge {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: 500;
            }

            .status-pending {
                background: #fff3cd;
                color: #856404;
            }

            .status-downloading {
                background: #cce5ff;
                color: #004085;
            }

            .status-downloaded {
                background: #d1ecf1;
                color: #0c5460;
            }

            .status-uploading {
                background: #d4edda;
                color: #155724;
            }

            .status-upload_completed {
                background: #c3e6cb;
                color: #155724;
            }

            .status-error {
                background: #f8d7da;
                color: #721c24;
            }

            .notifications {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1000;
                max-width: 350px;
            }

            .notification {
                background: white;
                padding: 15px;
                margin-bottom: 10px;
                border-radius: 5px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                animation: slideIn 0.3s ease;
            }

            .notification.info {
                border-left: 4px solid #3498db;
            }

            .notification.success {
                border-left: 4px solid #27ae60;
            }

            .notification.warning {
                border-left: 4px solid #f39c12;
            }

            .notification.error {
                border-left: 4px solid #e74c3c;
            }

            .notification-title {
                font-weight: 600;
                margin-bottom: 5px;
                color: #2c3e50;
            }

            .notification-message {
                font-size: 13px;
                color: #7f8c8d;
            }

            @keyframes slideIn {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            .alert {
                padding: 12px;
                margin-bottom: 10px;
                border-radius: 5px;
                display: none;
            }

            .alert-success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }

            .alert-error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }

            @media (max-width: 768px) {
                .grid {
                    grid-template-columns: 1fr;
                }

                .header {
                    flex-direction: column;
                    gap: 10px;
                }

                .notifications {
                    left: 20px;
                    right: 20px;
                    max-width: none;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <h1>🤖 Mirror Leech Admin Dashboard</h1>
                </div>
                <div>
                    <span id="ws-status" class="connection-status disconnected">⚫ Connecting...</span>
                    <button class="logout-btn" onclick="logout()">Logout</button>
                </div>
            </div>

            <div class="grid">
                <!-- System Stats -->
                <div class="card">
                    <h2>📊 System Stats (Real-time)</h2>
                    <div class="stat-grid" id="stats-grid">
                        <div class="stat">
                            <div class="stat-label">CPU Usage</div>
                            <div class="stat-value" id="cpu-usage">--</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">Memory</div>
                            <div class="stat-value" id="memory-usage">--</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">Disk</div>
                            <div class="stat-value" id="disk-usage">--</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">Status</div>
                            <div class="stat-value" id="bot-status">--</div>
                        </div>
                    </div>
                </div>

                <!-- Download Form -->
                <div class="card">
                    <h2>⬇️ New Download</h2>
                    <div id="alert-container"></div>
                    <form class="download-form" onsubmit="startDownload(event)">
                        <div class="form-group">
                            <label for="url">URL / Magnet / Link</label>
                            <input type="text" id="url" placeholder="https://... or magnet:..." required>
                        </div>
                        <div class="form-group">
                            <label for="operation">Operation</label>
                            <select id="operation" required>
                                <option value="">Choose operation...</option>
                                <option value="mirror">Mirror (to Cloud)</option>
                                <option value="leech">Leech (to Telegram)</option>
                                <option value="qm">qBittorrent Mirror</option>
                                <option value="jm">JDownloader Mirror</option>
                            </select>
                        </div>
                        <button type="submit" class="btn">✨ Start Download</button>
                    </form>
                </div>
            </div>

            <!-- Active Downloads -->
            <div class="card">
                <h2>📥 Active Downloads</h2>
                <div class="download-list" id="downloads-list">
                    <p style="color: #7f8c8d; text-align: center; padding: 20px;">No active downloads</p>
                </div>
            </div>

            <!-- Phase 4: Download History -->
            <div class="card" style="margin-top: 20px;">
                <h2>📝 Download History</h2>
                <div style="margin-bottom: 15px; display: flex; gap: 10px;">
                    <select id="history-operation" style="padding: 8px; border: 1px solid #bdc3c7; border-radius: 5px;">
                        <option value="">All Operations</option>
                        <option value="mirror">Mirror</option>
                        <option value="leech">Leech</option>
                        <option value="qm">qBittorrent Mirror</option>
                        <option value="jm">JDownloader Mirror</option>
                    </select>
                    <button class="btn" onclick="loadHistory()" style="padding: 8px 15px; font-size: 13px;">🔄 Refresh</button>
                </div>
                <div style="max-height: 300px; overflow-y: auto;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                        <thead style="background: #f8f9fa; position: sticky; top: 0;">
                            <tr style="border-bottom: 2px solid #bdc3c7;">
                                <th style="padding: 10px; text-align: left;">URL</th>
                                <th style="padding: 10px; text-align: center;">Operation</th>
                                <th style="padding: 10px; text-align: center;">Status</th>
                                <th style="padding: 10px; text-align: right;">Size</th>
                            </tr>
                        </thead>
                        <tbody id="history-table">
                            <tr><td colspan="4" style="padding: 20px; text-align: center; color: #7f8c8d;">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Phase 4: Analytics -->
            <div class="grid" style="margin-top: 20px;">
                <div class="card">
                    <h2>📊 Download Statistics (30 days)</h2>
                    <div class="stat-grid" id="analytics-stats">
                        <div class="stat">
                            <div class="stat-label">Total Downloads</div>
                            <div class="stat-value" id="stats-total">--</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">Successful</div>
                            <div class="stat-value" id="stats-successful">--</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">Failed</div>
                            <div class="stat-value" id="stats-failed">--</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">Total Data</div>
                            <div class="stat-value" id="stats-total-size">--</div>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <h2>✅ Success Rates by Operation</h2>
                    <div id="success-rates" style="font-size: 13px; line-height: 1.8;">
                        <p style="color: #7f8c8d; text-align: center; padding: 20px;">Loading...</p>
                    </div>
                </div>

                <div class="card">
                    <h2>🔝 Top Downloads (by size)</h2>
                    <div id="top-downloads" style="font-size: 12px; line-height: 1.6;">
                        <p style="color: #7f8c8d; text-align: center; padding: 20px;">Loading...</p>
                    </div>
                </div>
            </div>

            <!-- Phase 5: Advanced Download Management -->
            <div style="margin-top: 30px; padding: 20px; background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); border-radius: 10px; border: 2px solid #667eea;">
                <h2 style="color: #667eea; margin-bottom: 20px;">🚀 Phase 5: Advanced Download Management</h2>

                <div class="grid">
                    <!-- Batch Upload -->
                    <div class="card">
                        <h2>📦 Batch Upload</h2>
                        <div class="form-group">
                            <label for="batch-urls">URLs (one per line)</label>
                            <textarea id="batch-urls" placeholder="https://example.com/file1&#10;https://example.com/file2" style="padding: 10px; border: 1px solid #bdc3c7; border-radius: 5px; min-height: 100px; font-size: 12px; font-family: monospace;"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="batch-operation">Operation</label>
                            <select id="batch-operation" style="padding: 10px; border: 1px solid #bdc3c7; border-radius: 5px;">
                                <option value="mirror">Mirror</option>
                                <option value="leech">Leech</option>
                                <option value="qm">qBittorrent Mirror</option>
                            </select>
                        </div>
                        <button class="btn" onclick="batchUpload()" style="width: 100%;">Upload All</button>
                    </div>

                    <!-- Templates -->
                    <div class="card">
                        <h2>📋 Download Templates</h2>
                        <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                            <input type="text" id="template-name" placeholder="Template name" style="flex: 1; padding: 8px; border: 1px solid #bdc3c7; border-radius: 5px; font-size: 13px;">
                            <button class="btn" onclick="createTemplate()" style="padding: 8px 15px; font-size: 13px;">Create</button>
                        </div>
                        <div id="templates-list" style="max-height: 150px; overflow-y: auto; border: 1px solid #ecf0f1; border-radius: 5px; padding: 10px;">
                            <p style="color: #7f8c8d; text-align: center;">Loading templates...</p>
                        </div>
                    </div>

                    <!-- Queue Status -->
                    <div class="card">
                        <h2>📊 Queue Status</h2>
                        <div class="stat-grid">
                            <div class="stat">
                                <div class="stat-label">Queued</div>
                                <div class="stat-value" id="queue-queued">--</div>
                            </div>
                            <div class="stat">
                                <div class="stat-label">In Progress</div>
                                <div class="stat-value" id="queue-progress">--</div>
                            </div>
                            <div class="stat">
                                <div class="stat-label">Total Size</div>
                                <div class="stat-value" id="queue-size">--</div>
                            </div>
                            <div class="stat">
                                <div class="stat-label">Status</div>
                                <div class="stat-value" id="queue-status" style="font-size: 14px;">--</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Scheduled Downloads -->
                <div class="card" style="margin-top: 20px;">
                    <h2>⏰ Scheduled Downloads</h2>
                    <div style="display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap;">
                        <input type="text" id="schedule-url" placeholder="URL to download" style="flex: 1; min-width: 250px; padding: 8px; border: 1px solid #bdc3c7; border-radius: 5px;">
                        <select id="schedule-type" style="padding: 8px; border: 1px solid #bdc3c7; border-radius: 5px; min-width: 120px;">
                            <option value="once">Once</option>
                            <option value="daily">Daily</option>
                            <option value="weekly">Weekly</option>
                            <option value="monthly">Monthly</option>
                        </select>
                        <button class="btn" onclick="scheduleDownload()" style="padding: 8px 15px;">Schedule</button>
                    </div>
                    <div style="max-height: 250px; overflow-y: auto;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                            <thead style="background: #f8f9fa; position: sticky; top: 0;">
                                <tr style="border-bottom: 2px solid #bdc3c7;">
                                    <th style="padding: 8px; text-align: left;">URL</th>
                                    <th style="padding: 8px; text-align: center;">Schedule</th>
                                    <th style="padding: 8px; text-align: center;">Status</th>
                                    <th style="padding: 8px; text-align: center;">Runs</th>
                                    <th style="padding: 8px; text-align: center;">Actions</th>
                                </tr>
                            </thead>
                            <tbody id="schedules-table">
                                <tr><td colspan="5" style="padding: 20px; text-align: center; color: #7f8c8d;">Loading...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- Notifications -->
        <div class="notifications" id="notifications-container"></div>

        <script>
            let authToken = localStorage.getItem('auth_token');
            let ws = null;
            let reconnectAttempt = 0;
            const downloadsMap = new Map();

            if (!authToken) {
                window.location.href = '/admin/login';
            }

            const API_BASE = '/admin/api';

            // Initialize WebSocket connection
            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/admin/ws`;

                ws = new WebSocket(wsUrl);

                ws.onopen = () => {
                    console.log('WebSocket connected');
                    reconnectAttempt = 0;
                    document.getElementById('ws-status').className = 'connection-status connected';
                    document.getElementById('ws-status').textContent = '🟢 Connected';
                };

                ws.onmessage = (event) => {
                    const message = JSON.parse(event.data);
                    handleWebSocketMessage(message);
                };

                ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                };

                ws.onclose = () => {
                    console.log('WebSocket disconnected');
                    document.getElementById('ws-status').className = 'connection-status disconnected';
                    document.getElementById('ws-status').textContent = '⚫ Reconnecting...';

                    // Attempt reconnect with exponential backoff
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttempt), 30000);
                    reconnectAttempt++;
                    setTimeout(connectWebSocket, delay);
                };
            }

            function handleWebSocketMessage(message) {
                console.log('WebSocket message:', message);

                switch (message.type) {
                    case 'connected':
                        console.log('WebSocket handshake complete');
                        break;

                    case 'download_update':
                        updateDownload(message.download_id, message.data);
                        break;

                    case 'system_stats':
                        updateSystemStats(message.data);
                        break;

                    case 'notification':
                        showNotification(message.title, message.message, message.level);
                        break;

                    case 'keepalive':
                        // Send pong
                        ws.send(JSON.stringify({type: 'ping'}));
                        break;
                }
            }

            function updateDownload(downloadId, data) {
                downloadsMap.set(downloadId, {
                    ...downloadsMap.get(downloadId),
                    ...data
                });
                renderDownloads();
            }

            function updateSystemStats(stats) {
                if (stats.cpu !== undefined) {
                    document.getElementById('cpu-usage').textContent = stats.cpu.toFixed(1) + '%';
                }
                if (stats.memory !== undefined) {
                    document.getElementById('memory-usage').textContent = stats.memory.toFixed(1) + '%';
                }
                if (stats.disk !== undefined) {
                    document.getElementById('disk-usage').textContent = stats.disk.toFixed(1) + '%';
                }
            }

            function showNotification(title, message, level = 'info') {
                const container = document.getElementById('notifications-container');
                const notification = document.createElement('div');
                notification.className = `notification ${level}`;
                notification.innerHTML = `
                    <div class="notification-title">${title}</div>
                    <div class="notification-message">${message}</div>
                `;
                container.appendChild(notification);

                // Auto-remove after 5 seconds
                setTimeout(() => {
                    notification.style.opacity = '0';
                    notification.style.transform = 'translateX(400px)';
                    setTimeout(() => notification.remove(), 300);
                }, 5000);
            }

            // Initialize
            connectWebSocket();
            loadStats();
            loadDownloads();

            // Fallback polling for stats (every 10 seconds)
            setInterval(loadStats, 10000);
            // Refresh download list every 5 seconds (WebSocket updates in real-time)
            setInterval(loadDownloads, 5000);

            async function loadStats() {
                try {
                    const response = await fetch(`${API_BASE}/stats`, {
                        headers: {
                            'Authorization': `Bearer ${authToken}`
                        }
                    });

                    if (response.status === 401) {
                        localStorage.removeItem('auth_token');
                        window.location.href = '/admin/login';
                        return;
                    }

                    if (response.ok) {
                        const data = await response.json();
                        document.getElementById('cpu-usage').textContent = data.cpu_percent.toFixed(1) + '%';
                        document.getElementById('memory-usage').textContent =
                            (data.memory_used_gb.toFixed(1)) + ' / ' + (data.memory_total_gb.toFixed(1)) + ' GB';
                        document.getElementById('disk-usage').textContent =
                            (data.disk_used_gb.toFixed(0)) + ' / ' + (data.disk_total_gb.toFixed(0)) + ' GB';
                        document.getElementById('bot-status').textContent = '✅ Online';
                    }
                } catch (error) {
                    console.error('Error loading stats:', error);
                }
            }

            async function loadDownloads() {
                try {
                    const response = await fetch(`${API_BASE}/downloads`, {
                        headers: {
                            'Authorization': `Bearer ${authToken}`
                        }
                    });

                    if (response.status === 401) {
                        localStorage.removeItem('auth_token');
                        window.location.href = '/admin/login';
                        return;
                    }

                    if (response.ok) {
                        const data = await response.json();

                        // Update downloads map
                        data.downloads.forEach(download => {
                            downloadsMap.set(download.id, download);
                        });

                        renderDownloads();
                    }
                } catch (error) {
                    console.error('Error loading downloads:', error);
                }
            }

            function renderDownloads() {
                const list = document.getElementById('downloads-list');
                const downloads = Array.from(downloadsMap.values());

                if (downloads.length === 0) {
                    list.innerHTML = '<p style=\"color: #7f8c8d; text-align: center; padding: 20px;\">No active downloads</p>';
                    return;
                }

                list.innerHTML = downloads.map(download => {
                    const progress = download.progress || 0;
                    const speed = download.speed || 0;
                    const status = download.status || 'pending';
                    const url = download.url || '';
                    const name = url.split('/').pop() || 'Download';

                    return `
                        <div class="download-item ${status}">
                            <div class="download-item-name">${name}</div>
                            <div class="download-meta">
                                <span>${progress.toFixed(1)}% - ${(speed / 1024 / 1024).toFixed(2)} MB/s</span>
                                <span class="status-badge status-${status}">${status.replace('_', ' ')}</span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${progress}%"></div>
                            </div>
                            ${download.message ? `<div class="download-meta"><span>${download.message}</span></div>` : ''}
                            ${download.error ? `<div class="download-meta" style="color: #e74c3c;"><span>❌ ${download.error}</span></div>` : ''}
                            <div class="download-actions">
                                <button onclick="cancelDownload('${download.id}')" class="btn btn-danger" style="padding: 5px 10px; font-size: 12px;">❌ Cancel</button>
                            </div>
                        </div>
                    `;
                }).join('');
            }

            async function startDownload(event) {
                event.preventDefault();

                const url = document.getElementById('url').value;
                const operation = document.getElementById('operation').value;
                const alertContainer = document.getElementById('alert-container');

                try {
                    const response = await fetch(`${API_BASE}/download/start`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${authToken}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            url: url,
                            operation: operation
                        })
                    });

                    if (response.ok) {
                        const data = await response.json();
                        showAlert('Download queued! ID: ' + data.download_id, 'success', alertContainer);
                        document.getElementById('url').value = '';
                        document.getElementById('operation').value = '';
                        loadDownloads();
                    } else {
                        const error = await response.json();
                        showAlert('Error: ' + (error.detail || 'Unknown error'), 'error', alertContainer);
                    }
                } catch (error) {
                    showAlert('Error: ' + error.message, 'error', alertContainer);
                }
            }

            async function cancelDownload(downloadId) {
                if (!confirm('Are you sure you want to cancel this download?')) return;

                try {
                    const response = await fetch(`${API_BASE}/download/${downloadId}/cancel`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${authToken}`
                        }
                    });

                    if (response.ok) {
                        downloadsMap.delete(downloadId);
                        renderDownloads();
                    }
                } catch (error) {
                    console.error('Error cancelling download:', error);
                }
            }

            function showAlert(message, type, container) {
                const alert = document.createElement('div');
                alert.className = `alert alert-${type}`;
                alert.textContent = message;
                alert.style.display = 'block';
                container.innerHTML = '';
                container.appendChild(alert);

                setTimeout(() => {
                    alert.style.display = 'none';
                }, 5000);
            }

            function logout() {
                localStorage.removeItem('auth_token');
                window.location.href = '/admin/login';
            }

            // Phase 4: Load and display download history
            async function loadHistory() {
                try {
                    const operation = document.getElementById('history-operation').value;
                    const url = operation ? `${API_BASE}/history?operation=${operation}` : `${API_BASE}/history`;

                    const response = await fetch(url, {
                        headers: {
                            'Authorization': `Bearer ${authToken}`
                        }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        const tbody = document.getElementById('history-table');

                        if (!data.downloads || data.downloads.length === 0) {
                            tbody.innerHTML = '<tr><td colspan="4" style="padding: 20px; text-align: center; color: #7f8c8d;">No downloads yet</td></tr>';
                            return;
                        }

                        tbody.innerHTML = data.downloads.map(d => {
                            const url_text = d.url ? d.url.substring(0, 40) + (d.url.length > 40 ? '...' : '') : 'N/A';
                            const size_mb = d.total_size ? (d.total_size / 1024 / 1024).toFixed(1) : '--';
                            return `
                                <tr style="border-bottom: 1px solid #ecf0f1;">
                                    <td style="padding: 8px;">${url_text}</td>
                                    <td style="padding: 8px; text-align: center;">${d.operation}</td>
                                    <td style="padding: 8px; text-align: center;"><span class="status-badge status-${d.status}">${d.status}</span></td>
                                    <td style="padding: 8px; text-align: right;">${size_mb} MB</td>
                                </tr>
                            `;
                        }).join('');
                    }
                } catch (error) {
                    console.error('Error loading history:', error);
                }
            }

            // Phase 4: Load analytics data
            async function loadAnalytics() {
                try {
                    // Load statistics
                    const statsResponse = await fetch(`${API_BASE}/history/stats?days=30`, {
                        headers: {
                            'Authorization': `Bearer ${authToken}`
                        }
                    });

                    if (statsResponse.ok) {
                        const statsData = await statsResponse.json();
                        const stats = statsData.statistics.overall || {};

                        document.getElementById('stats-total').textContent = stats.total || 0;
                        document.getElementById('stats-successful').textContent = stats.successful || 0;
                        document.getElementById('stats-failed').textContent = stats.failed || 0;

                        const total_size_gb = stats.total_size ? (stats.total_size / 1024 / 1024 / 1024).toFixed(2) : 0;
                        document.getElementById('stats-total-size').textContent = total_size_gb + ' GB';
                    }

                    // Load success rates
                    const rateResponse = await fetch(`${API_BASE}/history/success-rate?days=30`, {
                        headers: {
                            'Authorization': `Bearer ${authToken}`
                        }
                    });

                    if (rateResponse.ok) {
                        const rateData = await rateResponse.json();
                        const rates = rateData.success_rates.by_operation || [];

                        const ratesHtml = rates.map(r => `
                            <div style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <span style="font-weight: 500;">${r.operation}</span>
                                    <span style="color: #667eea; font-weight: 600;">${r.success_rate.toFixed(1)}%</span>
                                </div>
                                <div style="background: #ecf0f1; height: 8px; border-radius: 4px; overflow: hidden;">
                                    <div style="background: linear-gradient(90deg, #27ae60 0%, #667eea 100%); height: 100%; width: ${r.success_rate}%;" />
                                </div>
                                <div style="font-size: 11px; color: #7f8c8d; margin-top: 5px;">
                                    ${r.successful} / ${r.total} successful
                                </div>
                            </div>
                        `).join('');

                        document.getElementById('success-rates').innerHTML = ratesHtml || '<p style="color: #7f8c8d; text-align: center;">No data available</p>';
                    }

                    // Load top downloads
                    const topResponse = await fetch(`${API_BASE}/history/top-downloads?limit=5`, {
                        headers: {
                            'Authorization': `Bearer ${authToken}`
                        }
                    });

                    if (topResponse.ok) {
                        const topData = await topResponse.json();
                        const downloads = topData.downloads || [];

                        const topHtml = downloads.map((d, idx) => {
                            const size_gb = (d.total_size / 1024 / 1024 / 1024).toFixed(2);
                            return `
                                <div style="padding: 10px; border-bottom: 1px solid #ecf0f1; display: flex; justify-content: space-between;">
                                    <div>
                                        <div style="font-weight: 500; color: #2c3e50;">
                                            #${idx + 1} - ${d.url ? d.url.substring(0, 30) + '...' : 'N/A'}
                                        </div>
                                        <div style="font-size: 11px; color: #7f8c8d; margin-top: 3px;">${d.operation}</div>
                                    </div>
                                    <div style="text-align: right; font-weight: 600; color: #667eea;">${size_gb} GB</div>
                                </div>
                            `;
                        }).join('');

                        document.getElementById('top-downloads').innerHTML = topHtml || '<p style="color: #7f8c8d; text-align: center; padding: 20px;">No downloads tracked yet</p>';
                    }
                } catch (error) {
                    console.error('Error loading analytics:', error);
                }
            }

            // Phase 5: Advanced Download Management Functions

            // Batch upload URLs
            async function batchUpload() {
                const urls = document.getElementById('batch-urls').value
                    .split('\\n')
                    .filter(url => url.trim().length > 0);
                const operation = document.getElementById('batch-operation').value;

                if (urls.length === 0) {
                    showNotification('Batch Upload', 'Please enter at least one URL', 'warning');
                    return;
                }

                try {
                    const response = await fetch(`${API_BASE}/batch-download`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${authToken}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            urls: urls,
                            operation: operation
                        })
                    });

                    if (response.ok) {
                        const data = await response.json();
                        showNotification('Success', `Added ${data.count} downloads to queue`, 'success');
                        document.getElementById('batch-urls').value = '';
                        loadQueueStatus();
                    }
                } catch (error) {
                    showNotification('Error', error.message, 'error');
                }
            }

            // Create download template
            async function createTemplate() {
                const name = prompt('Template name:');
                if (!name) return;

                const operation = document.getElementById('operation').value || 'mirror';

                try {
                    const response = await fetch(`${API_BASE}/templates/add`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${authToken}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            template_id: 'tpl_' + Date.now(),
                            name: name,
                            operation: operation
                        })
                    });

                    if (response.ok) {
                        showNotification('Success', 'Template created', 'success');
                        loadTemplates();
                    }
                } catch (error) {
                    showNotification('Error', error.message, 'error');
                }
            }

            // Load templates
            async function loadTemplates() {
                try {
                    const response = await fetch(`${API_BASE}/templates`, {
                        headers: {
                            'Authorization': `Bearer ${authToken}`
                        }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        const list = document.getElementById('templates-list');

                        if (!data.templates || data.templates.length === 0) {
                            list.innerHTML = '<p style="color: #7f8c8d; text-align: center;">No templates yet</p>';
                            return;
                        }

                        list.innerHTML = data.templates.map(t => `
                            <div style="padding: 8px; border-bottom: 1px solid #ecf0f1; display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="font-weight: 500; color: #2c3e50;">${t.name}</div>
                                    <div style="font-size: 11px; color: #7f8c8d;">${t.operation}</div>
                                </div>
                                <button onclick="deleteTemplate('${t.id}')" style="padding: 5px 10px; font-size: 11px; background: #e74c3c; color: white; border: none; border-radius: 3px; cursor: pointer;">Delete</button>
                            </div>
                        `).join('');
                    }
                } catch (error) {
                    console.error('Error loading templates:', error);
                }
            }

            // Delete template
            async function deleteTemplate(templateId) {
                if (!confirm('Delete this template?')) return;

                try {
                    const response = await fetch(`${API_BASE}/templates/${templateId}`, {
                        method: 'DELETE',
                        headers: {
                            'Authorization': `Bearer ${authToken}`
                        }
                    });

                    if (response.ok) {
                        loadTemplates();
                    }
                } catch (error) {
                    console.error('Error deleting template:', error);
                }
            }

            // Load queue status
            async function loadQueueStatus() {
                try {
                    const response = await fetch(`${API_BASE}/queue/status`, {
                        headers: {
                            'Authorization': `Bearer ${authToken}`
                        }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        const queue = data.queue || {};

                        document.getElementById('queue-queued').textContent = queue.queued || 0;
                        document.getElementById('queue-progress').textContent = queue.in_progress || 0;
                        document.getElementById('queue-size').textContent = queue.total_size || 0;
                        document.getElementById('queue-status').textContent = queue.queued ? '🟡 Active' : '✅ Empty';
                    }
                } catch (error) {
                    console.error('Error loading queue status:', error);
                }
            }

            // Schedule download
            async function scheduleDownload() {
                const url = document.getElementById('schedule-url').value;
                const scheduleType = document.getElementById('schedule-type').value;

                if (!url) {
                    showNotification('Schedule', 'Please enter a URL', 'warning');
                    return;
                }

                try {
                    const response = await fetch(`${API_BASE}/schedules/add`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${authToken}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            download_id: 'sch_' + Date.now(),
                            url: url,
                            operation: 'mirror',
                            schedule_type: scheduleType
                        })
                    });

                    if (response.ok) {
                        showNotification('Success', 'Download scheduled', 'success');
                        document.getElementById('schedule-url').value = '';
                        loadSchedules();
                    }
                } catch (error) {
                    showNotification('Error', error.message, 'error');
                }
            }

            // Load schedules
            async function loadSchedules() {
                try {
                    const response = await fetch(`${API_BASE}/schedules`, {
                        headers: {
                            'Authorization': `Bearer ${authToken}`
                        }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        const tbody = document.getElementById('schedules-table');

                        if (!data.scheduled || data.scheduled.length === 0) {
                            tbody.innerHTML = '<tr><td colspan="5" style="padding: 20px; text-align: center; color: #7f8c8d;">No schedules yet</td></tr>';
                            return;
                        }

                        tbody.innerHTML = data.scheduled.map(s => {
                            const url_text = s.url ? s.url.substring(0, 30) + (s.url.length > 30 ? '...' : '') : 'N/A';
                            return `
                                <tr style="border-bottom: 1px solid #ecf0f1;">
                                    <td style="padding: 8px;">${url_text}</td>
                                    <td style="padding: 8px; text-align: center;">${s.schedule_type}</td>
                                    <td style="padding: 8px; text-align: center;"><span class="status-badge" style="background: ${s.status === 'active' ? '#d4edda' : '#f8d7da'}; color: ${s.status === 'active' ? '#155724' : '#721c24'};">${s.status}</span></td>
                                    <td style="padding: 8px; text-align: center;">${s.run_count || 0}</td>
                                    <td style="padding: 8px; text-align: center;">
                                        <button onclick="updateScheduleStatus('${s.id}', '${s.status === 'active' ? 'paused' : 'active'}')" style="padding: 4px 8px; font-size: 11px; background: #667eea; color: white; border: none; border-radius: 3px; cursor: pointer; margin-right: 5px;">
                                            ${s.status === 'active' ? 'Pause' : 'Resume'}
                                        </button>
                                    </td>
                                </tr>
                            `;
                        }).join('');
                    }
                } catch (error) {
                    console.error('Error loading schedules:', error);
                }
            }

            // Update schedule status
            async function updateScheduleStatus(downloadId, status) {
                try {
                    await fetch(`${API_BASE}/schedules/${downloadId}/update`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${authToken}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ status: status })
                    });

                    loadSchedules();
                } catch (error) {
                    console.error('Error updating schedule:', error);
                }
            }

            // Load Phase 4 data on page load and refresh periodically
            window.addEventListener('load', () => {
                loadHistory();
                loadAnalytics();
                loadTemplates();
                loadSchedules();
                loadQueueStatus();
            });

            // Refresh data every 30 seconds
            setInterval(() => {
                loadHistory();
                loadAnalytics();
                loadQueueStatus();
            }, 30000);

            // Refresh schedules every 60 seconds
            setInterval(() => {
                loadSchedules();
            }, 60000);
        </script>
    </body>
    </html>
    """
