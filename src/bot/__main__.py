from . import LOGGER, auth_chats, bot_loop, sudo_users
from .core.config_manager import Config, validate_required_config
from .core.telegram_manager import TgClient

Config.load()
validate_required_config(strict=True)




_main_executed = False


async def _init_redis():
    """Initialize Redis client (optional, non-breaking)."""
    try:
        from .core.redis_manager import redis_client
        await redis_client.initialize(
            host=getattr(Config, 'REDIS_HOST', 'redis'),
            port=getattr(Config, 'REDIS_PORT', 6379),
            db=getattr(Config, 'REDIS_DB', 0)
        )
    except Exception as e:
        LOGGER.info(f"Redis initialization skipped: {e}")


async def _init_metrics():
    """Initialize metrics collection and HTTP server (optional, non-breaking)."""
    try:
        from .core.metrics import metrics
        metrics.enable()
        if metrics.is_enabled():
            LOGGER.info("📊 Metrics collection enabled on port 9090")
            try:
                from .core.metrics_server import metrics_server
                metrics_server.start()
            except Exception as e:
                LOGGER.warning(f"Metrics HTTP server failed to start: {e}")
    except Exception as e:
        LOGGER.info(f"Metrics initialization skipped: {e}")


async def _init_phase5():
    """Initialize Phase 5 high availability services (optional, non-breaking)."""
    try:
        LOGGER.info("="*50)
        LOGGER.info("🚀 Initializing Phase 5: High Availability")
        LOGGER.info("="*50)
        from .core.enhanced_startup import initialize_phase5_services
        phase5_status = await initialize_phase5_services()
        enabled = sum(1 for v in phase5_status.get('components', {}).values() if v)
        total = len(phase5_status.get('components', {}))
        LOGGER.info(f"✅ Phase 5: {enabled}/{total} components initialized")
    except Exception as e:
        LOGGER.info(f"⚠️  Phase 5 initialization skipped: {e}")


async def _init_automation():
    """Initialize automation system with alert callbacks (optional, non-breaking)."""
    try:
        if not getattr(Config, "ENABLE_AUTOMATION_SYSTEM", True):
            return
        from .core.alert_manager import AlertSeverity, AlertType, alert_manager
        from .core.automation_system import automation_system

        alert_manager.enable()

        async def _notify_admin(component_id, severity, message):
            if alert_manager.is_enabled:
                await alert_manager.trigger_alert(
                    AlertType.CUSTOM,
                    AlertSeverity.HIGH,
                    f"Auto-Recovery: {component_id}",
                    message,
                    details={"severity": getattr(severity, "value", str(severity))},
                )

        await automation_system.enable_all(
            enable_client_selection=getattr(Config, "ENABLE_CLIENT_SELECTION", True),
            enable_auto_recovery=getattr(Config, "ENABLE_AUTO_RECOVERY", True),
            enable_thumbnails=getattr(Config, "ENABLE_SMART_THUMBNAILS", True),
            notify_callback=_notify_admin,
        )
        LOGGER.info("✅ Automation System initialized")
    except Exception as e:
        LOGGER.info(f"⚠️  Automation System initialization skipped: {e}")


async def _init_config_watcher(to_thread):
    """Initialize config file watcher (optional, non-breaking)."""
    try:
        if not getattr(Config, "ENABLE_CONFIG_WATCHER", True):
            return
        import os
        from .core.config_watcher import config_watcher
        
        if await to_thread(os.path.exists, "config/.env"):
            config_watcher.add_watch("config/.env")
        if await to_thread(os.path.exists, ".env"):
            config_watcher.add_watch(".env")

        await config_watcher.start()
        LOGGER.info("✅ Config watcher initialized")
    except Exception as e:
        LOGGER.info(f"⚠️  Config watcher initialization skipped: {e}")


async def _drop_pending_updates(aiohttp, Config):
    """Drop pending Telegram updates on startup if configured."""
    if not getattr(Config, "DROP_PENDING_UPDATES_ON_STARTUP", False):
        return
    if not getattr(Config, "BOT_TOKEN", ""):
        return
    url = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/deleteWebhook"
    params = {"drop_pending_updates": "true"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    LOGGER.info("✅ Cleared pending Telegram updates")
                else:
                    body = await resp.text()
                    LOGGER.warning("Pending update cleanup failed: %s %s", resp.status, body)
    except Exception as exc:
        LOGGER.warning("Pending update cleanup failed: %s", exc)


async def _init_task_scheduler():
    """Initialize task scheduler and APScheduler."""
    from .core.task_scheduler import TaskScheduler
    from . import scheduler
    
    LOGGER.info("Initializing task scheduler...")
    await TaskScheduler.init()
    LOGGER.info("✅ Task scheduler initialized")

    if not scheduler.running:
        scheduler.start()
        LOGGER.info("✅ APScheduler event loop started")


async def _start_telegram_clients(aiohttp):
    """Start Telegram bot and user clients."""
    LOGGER.info("Starting Telegram clients...")
    await _drop_pending_updates(aiohttp, Config)
    from asyncio import gather
    await gather(TgClient.start_bot(), TgClient.start_user())
    LOGGER.info("✅ Telegram clients started")


async def _load_and_verify_config(gather_fn, load_configurations, update_variables):
    """Load configurations and verify auth data, apply workarounds if needed."""
    LOGGER.info("Loading configurations...")
    await gather_fn(load_configurations(), update_variables())
    LOGGER.info("✅ Configurations loaded")

    LOGGER.info(f"🔍 DEBUG - auth_chats: {dict(auth_chats) if auth_chats else 'EMPTY - WILL FIX'}")
    LOGGER.info(f"🔍 DEBUG - sudo_users: {list(sudo_users) if sudo_users else 'EMPTY - WILL FIX'}")

    # Workaround: Forcefully repopulate auth_chats and sudo_users if they're empty
    if not auth_chats and Config.AUTHORIZED_CHATS:
        LOGGER.warning("⚠️  auth_chats is empty! Applying workaround...")
        aid = Config.AUTHORIZED_CHATS.replace(",", " ").split()
        for id_ in aid:
            chat_id, *thread_ids = id_.split("|")
            chat_id = int(chat_id.strip())
            if thread_ids:
                thread_ids = list(map(lambda x: int(x.strip()), thread_ids))
                auth_chats[chat_id] = thread_ids
            else:
                auth_chats[chat_id] = []
        LOGGER.info(f"✅ Fixed auth_chats: {dict(auth_chats)}")

    if not sudo_users and Config.SUDO_USERS:
        LOGGER.warning("⚠️  sudo_users is empty! Applying workaround...")
        aid = Config.SUDO_USERS.replace(",", " ").split()
        for id_ in aid:
            sudo_users.append(int(id_.strip()))
        LOGGER.info(f"✅ Fixed sudo_users: {list(sudo_users)}")


async def _init_torrent_manager(gather_fn, update_qb_options, update_aria2_options, update_nzb_options):
    """Initialize torrent manager and update download client options."""
    from .core.torrent_manager import TorrentManager

    LOGGER.info("Initiating torrent manager...")
    await TorrentManager.initiate()
    LOGGER.info("✅ Torrent manager initiated")

    LOGGER.info("Updating download client options...")
    await gather_fn(update_qb_options(), update_aria2_options(), update_nzb_options())
    LOGGER.info("✅ Download client options updated")


async def _import_core_modules():
    """Import all core modules needed for final initialization."""
    LOGGER.info("📦 Importing clean_all...")
    from .helper.ext_utils.files_utils import clean_all
    LOGGER.info("📦 Importing jdownloader...")
    from .core.jdownloader_booter import jdownloader
    LOGGER.info("📦 Importing telegraph...")
    from .helper.ext_utils.telegraph_helper import telegraph
    LOGGER.info("📦 Importing rclone_serve_booter...")
    from .helper.mirror_leech_utils.rclone_utils.serve import rclone_serve_booter
    LOGGER.info("📦 Importing modules functions...")
    from .modules import get_packages_version, initiate_search_tools, restart_notification
    LOGGER.info("✅ All modules imported")
    return clean_all, jdownloader, telegraph, rclone_serve_booter, get_packages_version, initiate_search_tools, restart_notification


async def _start_metrics_update_loop():
    """Start metrics update loop if enabled."""
    try:
        from .core.metrics import metrics
        if metrics.is_enabled():
            from .helper.ext_utils.bot_utils import SetInterval
            SetInterval(
                getattr(Config, 'METRICS_UPDATE_INTERVAL', 60),
                metrics.update_system_metrics
            )
            LOGGER.info("✅ System metrics monitoring started")
    except Exception as e:
        LOGGER.debug(f"Metrics update loop skipped: {e}")


async def _run_final_init_tasks(wait_for, AsyncioTimeoutError, save_settings, clean_all, jdownloader, telegraph, 
                                 rclone_serve_booter, get_packages_version, initiate_search_tools, restart_notification):
    """Run all final initialization tasks with timeout handling."""
    LOGGER.info("Running final initialization tasks...")

    tasks = [
        ("save_settings", save_settings()),
        ("jdownloader.boot", jdownloader.boot()),
        ("clean_all", clean_all()),
        ("initiate_search_tools", initiate_search_tools()),
        ("get_packages_version", get_packages_version()),
        ("restart_notification", restart_notification()),
        ("telegraph.create_account", telegraph.create_account()),
        ("rclone_serve_booter", rclone_serve_booter()),
    ]

    for task_name, task_coro in tasks:
        try:
            timeout = 120.0 if task_name == "jdownloader.boot" else 15.0
            LOGGER.info(f"Running {task_name}...")
            await wait_for(task_coro, timeout=timeout)
            LOGGER.info(f"✅ {task_name} completed")
        except AsyncioTimeoutError:
            LOGGER.warning(f"⏱️  {task_name} timed out ({timeout}s)")
        except Exception as e:
            LOGGER.warning(f"⚠️  {task_name} failed: {e}")

    LOGGER.info("✅ Final initialization tasks completed")


async def _init_category_b(wait_for, AsyncioTimeoutError):
    """Initialize Category B advanced features."""
    if not getattr(Config, "ENABLE_CATEGORY_B", True):
        return
    LOGGER.info("🚀 Initializing Category B features...")
    try:
        from .core.category_b_integration import category_b
        await wait_for(category_b.initialize(), timeout=15.0)
        LOGGER.info("✅ Category B features initialized")
    except AsyncioTimeoutError:
        LOGGER.warning("⏱️  Category B initialization timed out (15s)")
    except Exception as e:
        LOGGER.warning(f"⚠️  Category B initialization failed: {e}")


async def _set_bot_commands(wait_for, AsyncioTimeoutError):
    """Set bot commands for Telegram menu."""
    LOGGER.info("Setting bot commands...")
    try:
        from .helper.ext_utils.bot_commands_setup import set_bot_commands
        await wait_for(set_bot_commands(), timeout=15.0)
        LOGGER.info("✅ Bot commands set")
    except AsyncioTimeoutError:
        LOGGER.warning("⏱️  Setting bot commands timed out (15s) - menu may not appear immediately")
    except Exception as e:
        LOGGER.warning(f"⚠️  Setting bot commands failed: {e} - try /help to see commands")


async def main():
    global _main_executed
    if _main_executed:
        LOGGER.error("❌ main() called more than once - preventing restart!")
        return
    _main_executed = True

    from asyncio import gather, to_thread, TimeoutError as AsyncioTimeoutError, wait_for
    import aiohttp

    from .core.startup import (
        load_configurations,
        load_settings,
        save_settings,
        update_aria2_options,
        update_nzb_options,
        update_qb_options,
        update_variables,
    )

    LOGGER.info("="*50)
    LOGGER.info("🚀 Starting Enhanced MLTB v3.1.0")
    LOGGER.info("Safe Innovation Path - All enhancements are optional")
    LOGGER.info("="*50)

    # Initialize all optional services
    await _init_redis()
    await _init_metrics()
    await _init_phase5()
    await _init_automation()
    await _init_config_watcher(to_thread)

    LOGGER.info("Loading settings...")
    await load_settings()
    LOGGER.info("✅ Settings loaded")

    # Initialize core services
    await _init_task_scheduler()
    await _start_telegram_clients(aiohttp)
    await _load_and_verify_config(gather, load_configurations, update_variables)
    await _init_torrent_manager(gather, update_qb_options, update_aria2_options, update_nzb_options)

    # Import and run final initialization
    modules = await _import_core_modules()
    clean_all, jdownloader, telegraph, rclone_serve_booter, get_packages_version, initiate_search_tools, restart_notification = modules

    await _start_metrics_update_loop()
    await _run_final_init_tasks(wait_for, AsyncioTimeoutError, save_settings, clean_all, jdownloader, telegraph,
                                 rclone_serve_booter, get_packages_version, initiate_search_tools, restart_notification)

    # Initialize advanced features
    await _init_category_b(wait_for, AsyncioTimeoutError)
    await _set_bot_commands(wait_for, AsyncioTimeoutError)

    LOGGER.info("🎉 Main initialization completed!")


bot_loop.run_until_complete(main())
LOGGER.info("✅ main() completed successfully")
LOGGER.info("📝 Proceeding to handler registration and start bot listener loop...")

# Initialize Command Health Monitoring System
try:
    from .core.command_alert_system import command_alert_system
    from .core.command_health_monitor import command_health_monitor

    LOGGER.info("📊 Initializing command health monitoring...")
    command_health_monitor.enable()
    command_health_monitor.set_failure_threshold(3)  # Alert after 3 consecutive failures

    # Configure alerts
    owner_id = getattr(Config, 'OWNER_ID', None)
    if owner_id:
        command_alert_system.configure(
            owner_id=owner_id,
            alert_chat_id=getattr(Config, 'ALERT_CHAT_ID', owner_id),
            enabled=getattr(Config, 'COMMAND_ALERT_ENABLED', True)
        )
        LOGGER.info(f"✅ Command health monitoring enabled (Owner: {owner_id})")
    else:
        LOGGER.warning("⚠️  OWNER_ID not configured, monitoring enabled but alerts disabled")
        command_health_monitor.enable()  # Enable monitoring anyway
except Exception as e:
    LOGGER.error(f"❌ Command monitoring initialization failed: {e}", exc_info=True)

# Register Phase 5 shutdown handler (consolidated from all phases)
import atexit


def shutdown_services():
    """Shutdown Phase 5 services on exit (consolidated from phases 1-5)"""
    try:
        from .core.enhanced_startup import shutdown_phase5_services
        bot_loop.run_until_complete(shutdown_phase5_services())
    except Exception as e:
        LOGGER.debug(f"Phase 5 shutdown error: {e}")

atexit.register(shutdown_services)

from .core.handlers import add_handlers
from .helper.ext_utils.bot_utils import create_help_buttons
from .helper.listeners.aria2_listener import add_aria2_callbacks
from .modules.settings_ui import init_ui_monitor

LOGGER.info("📝 Adding aria2 callbacks...")
add_aria2_callbacks()
LOGGER.info("📝 Creating help buttons...")
create_help_buttons()
LOGGER.info("📝 Calling add_handlers()...")
add_handlers()

# Register command failure alerts
try:
    from .core.command_alert_system import command_alert_system
    from .core.telegram_manager import TgClient

    critical_commands = [
        "start", "leech", "mirror", "list",
        "stats", "help", "status", "queue", "dashboard"
    ]

    async def setup_alerts():
        await command_alert_system.register_alerts_for_all_commands(
            commands=critical_commands,
            tg_client=TgClient.bot
        )

    bot_loop.run_until_complete(setup_alerts())
    LOGGER.info("✅ Command failure alerts registered")
except Exception as e:
    LOGGER.warning(f"⚠️  Failed to register command alerts: {e}")

LOGGER.info("📝 Initializing UI monitor...")
init_ui_monitor()

# Start admin download processor
try:
    from web.admin_download_handler import start_admin_download_processor
    bot_loop.create_task(start_admin_download_processor())
    LOGGER.info("✅ Admin download processor started")
except Exception as e:
    LOGGER.warning(f"⚠️  Admin download processor failed to start: {e}")

LOGGER.info("Bot Started!")

bot_loop.run_forever()
