import sys

try:
    import uvloop
    if sys.version_info < (3, 12):
        uvloop.install()
except Exception:
    pass
import asyncio
from asyncio import sleep
from contextlib import asynccontextmanager
from logging import INFO, WARNING, FileHandler, StreamHandler, basicConfig, getLogger
from os import environ
from pathlib import Path
from time import perf_counter, time
from uuid import uuid4

import psutil
from aioaria2 import Aria2HttpClient
from aiohttp.client_exceptions import ClientError
from aioqbt.client import create_client
from aioqbt.exc import AQError
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from bot.core.config_manager import Config
from bot.core.redis_manager import redis_client
from integrations.sabnzbdapi import SabnzbdClient
from web.admin_login import get_login_html
from web.admin_routes import router as admin_router
from web.nodes import extract_file_ids, make_tree
from web.stream_handler import add_stream_routes

try:
    from bot.core.api_endpoints import add_enhanced_endpoints
    ENHANCED_API_AVAILABLE = True
except Exception as e:
    ENHANCED_API_AVAILABLE = False
    LOGGER_INIT = getLogger(__name__)
    LOGGER_INIT.warning(f"Enhanced API endpoints not available: {e}")

# Try to import GraphQL schema (Phase 3 optional)
try:
    from bot.core.graphql_api import schema as graphql_schema
    GRAPHQL_AVAILABLE = True
except Exception as e:
    graphql_schema = None
    GRAPHQL_AVAILABLE = False
    LOGGER_INIT = getLogger(__name__)
    LOGGER_INIT.warning(f"GraphQL API not available: {e}")

# Phase 3: Security & Hardening Integration
try:
    from bot.core.security_middleware import integrate_security_features
    SECURITY_FEATURES_AVAILABLE = True
except Exception as e:
    SECURITY_FEATURES_AVAILABLE = False
    LOGGER_INIT = getLogger(__name__)
    LOGGER_INIT.warning(f"Phase 3 security features not available: {e}")

# Optional OpenTelemetry tracing (enabled via environment)
try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    OTEL_AVAILABLE = True
except Exception as e:
    OTEL_AVAILABLE = False
    LOGGER_INIT = getLogger(__name__)
    LOGGER_INIT.warning(f"OpenTelemetry not available: {e}")

getLogger("httpx").setLevel(WARNING)
getLogger("aiohttp").setLevel(WARNING)

aria2 = None
qbittorrent = None
sabnzbd_client = SabnzbdClient(
    host="http://localhost",
    api_key="mltb",
    port="8070",
)


def _load_service_connection_config():
    return {
        "aria2_host": environ.get("ARIA2_HOST", "localhost"),
        "aria2_port": environ.get("ARIA2_PORT", "6800"),
        "qb_host": environ.get("QB_HOST", "localhost"),
        "qb_port": environ.get("QB_PORT", "8090"),
        "qb_username": environ.get("QB_USERNAME") or environ.get("WEBUI_USERNAME", "admin"),
        "qb_password": environ.get("QB_PASSWORD") or environ.get("WEBUI_PASSWORD", "mltbmltb"),
        "redis_host": environ.get("REDIS_HOST", getattr(Config, "REDIS_HOST", "redis")),
        "redis_port": int(environ.get("REDIS_PORT", getattr(Config, "REDIS_PORT", 6379))),
        "redis_db": int(environ.get("REDIS_DB", getattr(Config, "REDIS_DB", 0))),
    }


async def _initialize_aria2_client(config):
    global aria2
    try:
        aria2 = Aria2HttpClient(f"http://{config['aria2_host']}:{config['aria2_port']}/jsonrpc")
    except Exception as e:
        aria2 = None
        LOGGER.warning(f"Aria2 not available: {e}")


async def _initialize_qbittorrent_client(config):
    global qbittorrent
    try:
        qbittorrent = await create_client(
            f"http://{config['qb_host']}:{config['qb_port']}/api/v2/",
            username=config["qb_username"],
            password=config["qb_password"],
        )
    except Exception as e:
        qbittorrent = None
        LOGGER.warning(f"qBittorrent not available: {e}")


async def _initialize_redis_client(config):
    try:
        await redis_client.initialize(
            host=config["redis_host"],
            port=config["redis_port"],
            db=config["redis_db"],
        )
    except Exception as e:
        LOGGER.warning(f"Redis not available for stream links: {e}")


async def _initialize_torrent_manager():
    try:
        from bot.core.torrent_manager import TorrentManager

        await TorrentManager.initiate()
        LOGGER.info("✅ Torrent manager initialized in web server")
    except Exception as e:
        LOGGER.warning(f"Torrent manager init failed in web server: {e}")


async def _start_admin_download_processor_task():
    try:
        from web.admin_download_handler import start_admin_download_processor

        processor_task = asyncio.create_task(start_admin_download_processor())
        LOGGER.info("✅ Admin download processor started in web server")
        return processor_task
    except Exception as e:
        LOGGER.warning(f"⚠️  Admin download processor failed to start: {e}")
        return None


async def _cleanup_lifespan_resources(processor_task):
    if processor_task and not processor_task.done():
        processor_task.cancel()
        try:
            await processor_task
        except asyncio.CancelledError:
            pass

    if aria2 is not None:
        await aria2.close()
    if qbittorrent is not None:
        await qbittorrent.close()
    await redis_client.close()


def _is_reverify_consistent(res, paused, resumed):
    for i in res:
        if i.index in paused and i.priority != 0:
            return False
        if i.index in resumed and i.priority == 0:
            return False
    return True


async def _apply_reverify_corrections(paused, resumed, hash_id):
    if paused:
        try:
            await qbittorrent.torrents.file_prio(
                hash=hash_id, id=paused, priority=0
            )
        except (ClientError, TimeoutError, Exception, AQError) as e:
            LOGGER.error(f"{e} Errored in reverification paused!")
    if resumed:
        try:
            await qbittorrent.torrents.file_prio(
                hash=hash_id, id=resumed, priority=1
            )
        except (ClientError, TimeoutError, Exception, AQError) as e:
            LOGGER.error(f"{e} Errored in reverification resumed!")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global aria2, qbittorrent
    config = _load_service_connection_config()
    await _initialize_aria2_client(config)
    await _initialize_qbittorrent_client(config)
    await _initialize_redis_client(config)
    await _initialize_torrent_manager()
    processor_task = await _start_admin_download_processor_task()

    yield

    await _cleanup_lifespan_resources(processor_task)


app = FastAPI(lifespan=lifespan)

if ENHANCED_API_AVAILABLE:
    add_enhanced_endpoints(app)

add_stream_routes(app)

# Add admin routes
app.include_router(admin_router)

# Add admin login page
@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page():
    return get_login_html()

# Phase 3: Integrate security features
if SECURITY_FEATURES_AVAILABLE:
    # Get security settings from environment
    enable_csrf = environ.get("ENABLE_CSRF_PROTECTION", "true").lower() == "true"
    enable_https = environ.get("ENABLE_HTTPS_REDIRECT", "false").lower() == "true"
    enable_audit = environ.get("ENABLE_SECURITY_AUDIT", "true").lower() == "true"

    # Integrate all Phase 3 security features
    app = integrate_security_features(
        app,
        enable_middleware=True,
        enable_csrf_endpoint=True,
        enable_status_endpoint=True,
        enable_csrf=enable_csrf,
        enable_input_validation=True,
        enable_audit_logging=enable_audit,
        enable_https_redirect=enable_https,
        exempt_paths=["/health", "/metrics", "/docs", "/openapi.json", "/api/dashboard/tasks", "/api/dashboard/stats", "/webstat", "/", "/dashboard"]
    )
    LOGGER_INIT = getLogger(__name__)
    LOGGER_INIT.info("✅ Phase 3 security features integrated")

if OTEL_AVAILABLE:
    enable_otel = environ.get("ENABLE_OTEL_TRACING", "false").lower() == "true"
    if enable_otel:
        service_name = environ.get("OTEL_SERVICE_NAME", "mltb-web")
        otlp_endpoint = environ.get(
            "OTEL_EXPORTER_OTLP_ENDPOINT",
            "http://localhost:4318/v1/traces",
        )
        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
        )
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
        LOGGER_INIT = getLogger(__name__)
        LOGGER_INIT.info("✅ OpenTelemetry tracing enabled")

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))

basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[FileHandler("data/logs/log.txt"), StreamHandler()],
    level=INFO,
)

LOGGER = getLogger(__name__)
START_TIME = time()
RETRY_MAX_ATTEMPTS = int(environ.get("RETRY_MAX_ATTEMPTS", "3"))
RETRY_MAX_WAIT_SECONDS = float(environ.get("RETRY_MAX_WAIT_SECONDS", "2.0"))
RETRY_EXCEPTIONS = (ClientError, TimeoutError, AQError)
DASHBOARD_CACHE_TTL_SECONDS = float(environ.get("DASHBOARD_CACHE_TTL_SECONDS", "2.0"))
_dashboard_cache = {
    "stats": {"ts": 0.0, "payload": None},
    "tasks": {"ts": 0.0, "payload": None},
}


async def _call_with_retry(label, func, *args, **kwargs):
    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(RETRY_MAX_ATTEMPTS),
            wait=wait_exponential_jitter(initial=0.2, max=RETRY_MAX_WAIT_SECONDS),
            retry=retry_if_exception_type(RETRY_EXCEPTIONS),
            reraise=True,
        ):
            with attempt:
                return await func(*args, **kwargs)
    except Exception as e:
        LOGGER.warning("retry_failed op=%s error=%s", label, e)
        raise


@app.middleware("http")
async def request_context_logger(request: Request, call_next):
    request_id = (
        request.headers.get("x-request-id")
        or request.headers.get("x-correlation-id")
        or str(uuid4())
    )
    request.state.request_id = request_id
    start_time = perf_counter()
    response = await call_next(request)
    duration_ms = (perf_counter() - start_time) * 1000
    response.headers["x-request-id"] = request_id
    client_host = request.client.host if request.client else "unknown"
    LOGGER.info(
        "request_id=%s method=%s path=%s status=%s duration_ms=%.2f client=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        client_host,
    )
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "type": "http_error",
                "request_id": request_id,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "message": "Validation failed",
                "type": "validation_error",
                "request_id": request_id,
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)
    LOGGER.exception("Unhandled error request_id=%s", request_id)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "type": "server_error",
                "request_id": request_id,
            }
        },
    )


async def re_verify(paused, resumed, hash_id):
    attempts = 0
    while True:
        res = await _call_with_retry("qbittorrent.torrents.files", qbittorrent.torrents.files, hash_id)
        if _is_reverify_consistent(res, paused, resumed):
            break
        LOGGER.info("Reverification Failed! Correcting stuff...")
        await sleep(0.5)
        await _apply_reverify_corrections(paused, resumed, hash_id)
        attempts += 1
        if attempts > 5:
            return False
    LOGGER.info(f"Verified! Hash: {hash_id}")
    return True


@app.get("/app/files", response_class=HTMLResponse)
async def files(request: Request):
    return templates.TemplateResponse("page.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


def _to_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _safe_get(item, key, default=None):
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _map_status(raw_status: str):
    if not raw_status:
        return "unknown"
    raw = raw_status.lower()
    if raw in {"active", "downloading", "forceddl", "queueddl"}:
        return "downloading"
    if raw in {"uploading", "forcedup", "queuedup", "seeding"}:
        return "uploading"
    if "pause" in raw:
        return "paused"
    if raw in {"error", "missingfiles"}:
        return "error"
    if raw in {"complete", "completed"}:
        return "completed"
    return raw


async def _collect_aria2_tasks():
    tasks = []
    if not aria2:
        return tasks
    try:
        active = await _call_with_retry("aria2.tellActive", aria2.tellActive)
        for item in active:
            total = _to_int(item.get("totalLength", 0))
            completed = _to_int(item.get("completedLength", 0))
            progress = (completed / total * 100) if total > 0 else 0
            tasks.append(
                {
                    "gid": item.get("gid"),
                    "name": (item.get("bittorrent", {}) or {}).get("info", {}).get("name")
                    or (item.get("files", [{}])[0] or {}).get("path", "Aria2 Task"),
                    "engine": "aria2",
                    "status": _map_status(item.get("status")),
                    "progress": progress,
                    "speed": _to_int(item.get("downloadSpeed", 0)),
                    "eta": _to_int(item.get("eta", 0)),
                    "total_length": total,
                    "completed_length": completed,
                }
            )
    except Exception as e:
        LOGGER.error(f"Dashboard aria2 error: {e}")
    return tasks


async def _collect_qbittorrent_tasks():
    tasks = []
    if not qbittorrent:
        return tasks
    try:
        torrents = await _call_with_retry("qbittorrent.torrents.info", qbittorrent.torrents.info)
        for item in torrents:
            total = _to_int(_safe_get(item, "size", 0))
            completed = _to_int(_safe_get(item, "downloaded", 0))
            progress = _safe_get(item, "progress", 0) * 100
            tasks.append(
                {
                    "gid": _safe_get(item, "hash", ""),
                    "name": _safe_get(item, "name", "qBittorrent Task"),
                    "engine": "qbittorrent",
                    "status": _map_status(_safe_get(item, "state", "")),
                    "progress": progress,
                    "speed": _to_int(_safe_get(item, "dlspeed", 0)),
                    "eta": _to_int(_safe_get(item, "eta", 0)),
                    "total_length": total,
                    "completed_length": completed,
                }
            )
    except Exception as e:
        LOGGER.error(f"Dashboard qBittorrent error: {e}")
    return tasks


@app.get("/api/dashboard/tasks")
async def dashboard_tasks():
    if DASHBOARD_CACHE_TTL_SECONDS > 0:
        cached = _dashboard_cache["tasks"]
        if cached["payload"] is not None and (time() - cached["ts"]) <= DASHBOARD_CACHE_TTL_SECONDS:
            return JSONResponse(cached["payload"])
    aria2_tasks = await _collect_aria2_tasks()
    qbittorrent_tasks = await _collect_qbittorrent_tasks()
    tasks = aria2_tasks + qbittorrent_tasks
    payload = {"tasks": tasks, "total": len(tasks)}
    if DASHBOARD_CACHE_TTL_SECONDS > 0:
        _dashboard_cache["tasks"] = {"ts": time(), "payload": payload}
    return JSONResponse(payload)


@app.get("/api/dashboard/stats")
@app.get("/webstat")
async def dashboard_stats():
    """Dashboard statistics endpoint (also available as /webstat)"""
    if DASHBOARD_CACHE_TTL_SECONDS > 0:
        cached = _dashboard_cache["stats"]
        if cached["payload"] is not None and (time() - cached["ts"]) <= DASHBOARD_CACHE_TTL_SECONDS:
            return JSONResponse(cached["payload"])
    total_speed = 0
    try:
        if aria2:
            global_stats = await _call_with_retry("aria2.getGlobalStat", aria2.getGlobalStat)
            total_speed += _to_int(global_stats.get("downloadSpeed", 0))
        if qbittorrent:
            transfer = await _call_with_retry("qbittorrent.transfer.info", qbittorrent.transfer.info)
            total_speed += _to_int(_safe_get(transfer, "dl_info_speed", 0))
    except Exception as e:
        LOGGER.error(f"Dashboard stats error: {e}")

    cpu_usage = round(psutil.cpu_percent(interval=None), 2)
    memory_usage = round(psutil.virtual_memory().percent, 2)

    aria2_tasks = await _collect_aria2_tasks()
    qbittorrent_tasks = await _collect_qbittorrent_tasks()
    active_tasks = len(aria2_tasks) + len(qbittorrent_tasks)

    payload = {
        "active_tasks": active_tasks,
        "total_speed": total_speed,
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
        "uptime": int(time() - START_TIME),
    }
    if DASHBOARD_CACHE_TTL_SECONDS > 0:
        _dashboard_cache["stats"] = {"ts": time(), "payload": payload}
    return JSONResponse(payload)


@app.api_route(
    "/app/files/torrent", methods=["GET", "POST"]
)
def _validate_pin(gid, pin):
    """Validate PIN against GID"""
    extracted_code = "".join([nbr for nbr in gid if nbr.isdigit()][:4])
    if extracted_code and extracted_code != pin:
        return False
    return True

async def _handle_torrent_post(gid, mode, data):
    """Handle POST requests for torrent file selection/rename"""
    if mode == "rename":
        if len(gid) > 20:
            await handle_rename(gid, data)
            return {
                "files": [],
                "engine": "",
                "error": "",
                "message": "Rename successfully.",
            }
        else:
            return {
                "files": [],
                "engine": "",
                "error": "Rename failed.",
                "message": "Cannot rename aria2c torrent file",
            }
    else:
        selected_files, unselected_files = extract_file_ids(data)
        if gid.startswith("SABnzbd_nzo"):
            await set_sabnzbd(gid, unselected_files)
        elif len(gid) > 20:
            await set_qbittorrent(gid, selected_files, unselected_files)
        else:
            selected_files = ",".join(selected_files)
            await set_aria2(gid, selected_files)
        return {
            "files": [],
            "engine": "",
            "error": "",
            "message": "Your selection has been submitted successfully.",
        }

async def _handle_torrent_get(gid):
    """Handle GET requests to retrieve torrent files"""
    if gid.startswith("SABnzbd_nzo"):
        res = await sabnzbd_client.get_files(gid)
        return make_tree(res, "sabnzbd")
    elif len(gid) > 20:
        res = await _call_with_retry("qbittorrent.torrents.files", qbittorrent.torrents.files, gid)
        return make_tree(res, "qbittorrent")
    else:
        res = await _call_with_retry("aria2.getFiles", aria2.getFiles, gid)
        op = await _call_with_retry("aria2.getOption", aria2.getOption, gid)
        fpath = f"{op['dir']}/"
        return make_tree(res, "aria2", fpath)

async def handle_torrent(request: Request):
    params = request.query_params

    if not (gid := params.get("gid")):
        return JSONResponse(
            {
                "files": [],
                "engine": "",
                "error": "GID is missing",
                "message": "GID not specified",
            },
            status_code=400
        )

    if not (pin := params.get("pin")):
        return JSONResponse(
            {
                "files": [],
                "engine": "",
                "error": "Pin is missing",
                "message": "PIN not specified",
            },
            status_code=400
        )

    if not _validate_pin(gid, pin):
        return JSONResponse(
            {
                "files": [],
                "engine": "",
                "error": "Invalid pin",
                "message": "The PIN you entered is incorrect",
            },
            status_code=401
        )

    if request.method == "POST":
        if not (mode := params.get("mode")):
            return JSONResponse(
                {
                    "files": [],
                    "engine": "",
                    "error": "Mode is not specified",
                    "message": "Mode is not specified",
                },
                status_code=400
            )
        data = await request.json()
        content = await _handle_torrent_post(gid, mode, data)
    else:
        try:
            content = await _handle_torrent_get(gid)
        except (ClientError, TimeoutError, Exception, AQError) as e:
            error_text = str(e)
            LOGGER.error(error_text)
            if "NotFoundError" in error_text or "status=404" in error_text:
                return JSONResponse(
                    {
                        "files": [],
                        "engine": "",
                        "error": "Files not ready",
                        "message": "Torrent metadata not available yet. Please retry in a few seconds.",
                    },
                    status_code=404
                )
            return JSONResponse(
                {
                    "files": [],
                    "engine": "",
                    "error": "Error getting files",
                    "message": error_text,
                },
                status_code=500
            )

    return JSONResponse(content)


async def handle_rename(gid, data):
    try:
        _type = data["type"]
        del data["type"]
        if _type == "file":
            await _call_with_retry(
                "qbittorrent.torrents.rename_file",
                qbittorrent.torrents.rename_file,
                hash=gid,
                **data,
            )
        else:
            await _call_with_retry(
                "qbittorrent.torrents.rename_folder",
                qbittorrent.torrents.rename_folder,
                hash=gid,
                **data,
            )
    except (ClientError, TimeoutError, Exception, AQError) as e:
        LOGGER.error(f"{e} Errored in renaming")


async def set_sabnzbd(gid, unselected_files):
    await sabnzbd_client.remove_file(gid, unselected_files)
    LOGGER.info(f"Verified! nzo_id: {gid}")


async def set_qbittorrent(gid, selected_files, unselected_files):
    if unselected_files:
        try:
            await _call_with_retry(
                "qbittorrent.torrents.file_prio",
                qbittorrent.torrents.file_prio,
                hash=gid,
                id=unselected_files,
                priority=0,
            )
        except (ClientError, TimeoutError, Exception, AQError) as e:
            LOGGER.error(f"{e} Errored in paused")
    if selected_files:
        try:
            await _call_with_retry(
                "qbittorrent.torrents.file_prio",
                qbittorrent.torrents.file_prio,
                hash=gid,
                id=selected_files,
                priority=1,
            )
        except (ClientError, TimeoutError, Exception, AQError) as e:
            LOGGER.error(f"{e} Errored in resumed")
    await sleep(0.5)
    if not await re_verify(unselected_files, selected_files, gid):
        LOGGER.error(f"Verification Failed! Hash: {gid}")


async def set_aria2(gid, selected_files):
    res = await _call_with_retry(
        "aria2.changeOption",
        aria2.changeOption,
        gid,
        {"select-file": selected_files},
    )
    if res == "OK":
        LOGGER.info(f"Verified! Gid: {gid}")
    else:
        LOGGER.info(f"Verification Failed! Report! Gid: {gid}")


@app.post("/graphql")
@app.get("/graphql", response_class=HTMLResponse)
async def graphql_endpoint(request: Request):
    """GraphQL API endpoint (Phase 3)"""
    if not GRAPHQL_AVAILABLE:
        return JSONResponse({"error": "GraphQL API not available"}, status_code=503)

    if request.method == "POST":
        data = await request.json()
        query = data.get("query")
        variables = data.get("variables", {})

        result = graphql_schema.execute(query, variable_values=variables)

        response = {
            "data": result.data,
        }
        if result.errors:
            response["errors"] = [str(err) for err in result.errors]

        return JSONResponse(response)
    else:
        # GraphQL Playground HTML for GET requests
        return """
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>GraphQL Playground</title>
            <style>
              body {
                margin: 0;
                padding: 0;
              }
            </style>
          </head>
          <body>
            <div id="root"></div>
            <script src="https://cdn.jsdelivr.net/npm/graphql-playground-react@latest/umd/graphql-playground.min.js"></script>
            <script>
              GraphQLPlayground.init(document.getElementById('root'), {
                endpoint: '/graphql',
                settings: {
                  'editor.theme': 'dark',
                }
              })
            </script>
          </body>
        </html>
        """


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    # Redirect to dashboard
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.exception_handler(Exception)
async def page_not_found(_, exc):
    return HTMLResponse(
        f"<h1>404: Task not found! Mostly wrong input. <br><br>Error: {exc}</h1>",
        status_code=404,
    )
