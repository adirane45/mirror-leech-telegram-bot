from . import LOGGER, bot_loop
from .core.telegram_manager import TgClient
from .core.config_manager import Config, validate_required_config

Config.load()
validate_required_config(strict=True)




_main_executed = False

async def main():
    global _main_executed
    if _main_executed:
        LOGGER.error("❌ main() called more than once - preventing restart!")
        return
    _main_executed = True
    
    from asyncio import gather, to_thread
    import aiohttp
    from .core.startup import (
        load_settings,
        load_configurations,
        save_settings,
        update_aria2_options,
        update_nzb_options,
        update_qb_options,
        update_variables,
    )
    from .core.task_scheduler import TaskScheduler
    
    # Safe Innovation Path - Phase 1 Initialization
    LOGGER.info("="*50)
    LOGGER.info("🚀 Starting Enhanced MLTB v3.1.0")
    LOGGER.info("Safe Innovation Path - All enhancements are optional")
    LOGGER.info("="*50)
    
    # Initialize Redis (optional, non-breaking)
    try:
        from .core.redis_manager import redis_client
        await redis_client.initialize(
            host=getattr(Config, 'REDIS_HOST', 'redis'),
            port=getattr(Config, 'REDIS_PORT', 6379),
            db=getattr(Config, 'REDIS_DB', 0)
        )
    except Exception as e:
        LOGGER.info(f"Redis initialization skipped: {e}")
    
    # Initialize Metrics (optional, non-breaking)
    try:
        from .core.metrics import metrics
        metrics.enable()
        if metrics.is_enabled():
            LOGGER.info("📊 Metrics collection enabled on port 9090")
            # Start metrics HTTP server
            try:
                from .core.metrics_server import metrics_server
                metrics_server.start()
            except Exception as e:
                LOGGER.warning(f"Metrics HTTP server failed to start: {e}")
    except Exception as e:
        LOGGER.info(f"Metrics initialization skipped: {e}")
    
    
    # Initialize Phase 5 Services (optional, non-breaking)
    # Consolidated: Phase 1-5 in single module for maintenance
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

    # Initialize Automation System (optional, non-breaking)
    try:
        if getattr(Config, "ENABLE_AUTOMATION_SYSTEM", True):
            from .core.automation_system import automation_system
            from .core.alert_manager import alert_manager, AlertType, AlertSeverity

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
    
    # Initialize Config Watcher (optional, non-breaking)
    try:
        if getattr(Config, "ENABLE_CONFIG_WATCHER", True):
            from .core.config_watcher import config_watcher
            
            # Add config files to watch
            import os
            if await to_thread(os.path.exists, "config/.env"):
                config_watcher.add_watch("config/.env")
            if await to_thread(os.path.exists, ".env"):
                config_watcher.add_watch(".env")
            
            await config_watcher.start()
            LOGGER.info("✅ Config watcher initialized")
    except Exception as e:
        LOGGER.info(f"⚠️  Config watcher initialization skipped: {e}")

    LOGGER.info("Loading settings...")
    await load_settings()
    LOGGER.info("✅ Settings loaded")

    async def _drop_pending_updates():
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
                        LOGGER.warning(
                            "Pending update cleanup failed: %s %s",
                            resp.status,
                            body,
                        )
        except Exception as exc:
            LOGGER.warning("Pending update cleanup failed: %s", exc)
    
    LOGGER.info("Initializing task scheduler...")
    await TaskScheduler.init()
    LOGGER.info("✅ Task scheduler initialized")
    
    # Start APScheduler in async context to avoid event loop errors
    from . import scheduler
    if not scheduler.running:
        scheduler.start()
        LOGGER.info("✅ APScheduler event loop started")

    LOGGER.info("Starting Telegram clients...")
    await _drop_pending_updates()
    await gather(TgClient.start_bot(), TgClient.start_user())
    LOGGER.info("✅ Telegram clients started")
    
    LOGGER.info("Loading configurations...")
    await gather(load_configurations(), update_variables())
    LOGGER.info("✅ Configurations loaded")

    from .core.torrent_manager import TorrentManager

    LOGGER.info("Initiating torrent manager...")
    await TorrentManager.initiate()
    LOGGER.info("✅ Torrent manager initiated")
    
    LOGGER.info("Updating download client options...")
    await gather(
        update_qb_options(),
        update_aria2_options(),
        update_nzb_options(),
    )
    LOGGER.info("✅ Download client options updated")
    LOGGER.info("📦 Importing clean_all...")
    from .helper.ext_utils.files_utils import clean_all
    LOGGER.info("📦 Importing jdownloader...")
    from .core.jdownloader_booter import jdownloader
    LOGGER.info("📦 Importing telegraph...")
    from .helper.ext_utils.telegraph_helper import telegraph
    LOGGER.info("📦 Importing rclone_serve_booter...")
    from .helper.mirror_leech_utils.rclone_utils.serve import rclone_serve_booter
    LOGGER.info("📦 Importing modules functions...")
    from .modules import (
        initiate_search_tools,
        get_packages_version,
        restart_notification,
    )
    LOGGER.info("✅ All modules imported")

    # Start metrics update loop if enabled
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
    
    LOGGER.info("Running final initialization tasks...")
    from asyncio import wait_for, TimeoutError as AsyncioTimeoutError
    
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
            # JDownloader needs more time for Java startup and initialization
            if task_name == "jdownloader.boot":
                timeout = 120.0  # 2 minutes for Java to fully initialize
            else:
                timeout = 15.0
            LOGGER.info(f"Running {task_name}...")
            await wait_for(task_coro, timeout=timeout)
            LOGGER.info(f"✅ {task_name} completed")
        except AsyncioTimeoutError:
            LOGGER.warning(f"⏱️  {task_name} timed out ({timeout}s)")
        except Exception as e:
            LOGGER.warning(f"⚠️  {task_name} failed: {e}")
    
    LOGGER.info("✅ Final initialization tasks completed")
    
    # Initialize Category B features (Advanced reliability & performance)
    if getattr(Config, "ENABLE_CATEGORY_B", True):
        LOGGER.info("🚀 Initializing Category B features...")
        try:
            from .core.category_b_integration import category_b
            await wait_for(category_b.initialize(), timeout=15.0)
            LOGGER.info("✅ Category B features initialized")
        except AsyncioTimeoutError:
            LOGGER.warning("⏱️  Category B initialization timed out (15s)")
        except Exception as e:
            LOGGER.warning(f"⚠️  Category B initialization failed: {e}")
    
    # Set bot commands for Telegram menu
    LOGGER.info("Setting bot commands...")
    try:
        from .helper.ext_utils.bot_commands_setup import set_bot_commands
        await wait_for(set_bot_commands(), timeout=15.0)
        LOGGER.info("✅ Bot commands set")
    except AsyncioTimeoutError:
        LOGGER.warning("⏱️  Setting bot commands timed out (15s) - menu may not appear immediately")
    except Exception as e:
        LOGGER.warning(f"⚠️  Setting bot commands failed: {e} - try /help to see commands")
    
    LOGGER.info("🎉 Main initialization completed!")


bot_loop.run_until_complete(main())
LOGGER.info("✅ main() completed successfully")
LOGGER.info("📝 Proceeding to handler registration and start bot listener loop...")

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

from .helper.ext_utils.bot_utils import create_help_buttons
from .helper.listeners.aria2_listener import add_aria2_callbacks
from .core.handlers import add_handlers
from .modules.settings_ui import init_ui_monitor

LOGGER.info("📝 Adding aria2 callbacks...")
add_aria2_callbacks()
LOGGER.info("📝 Creating help buttons...")
create_help_buttons()
LOGGER.info("📝 Calling add_handlers()...")
add_handlers()
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
