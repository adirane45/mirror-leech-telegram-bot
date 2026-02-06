from . import LOGGER, bot_loop
from .core.telegram_manager import TgClient
from .core.config_manager import Config

Config.load()


async def main():
    from asyncio import gather
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
    
    # Initialize Phase 2 Services (optional, non-breaking)
    try:
        LOGGER.info("="*50)
        LOGGER.info("🔧 Initializing Phase 2: Enhanced Logging & Monitoring")
        LOGGER.info("="*50)
        from .core.enhanced_startup_phase2 import initialize_phase2_services
        phase2_status = await initialize_phase2_services()
        enabled = sum(1 for v in phase2_status.values() if v)
        LOGGER.info(f"✅ Phase 2: {enabled}/5 services enabled")
    except Exception as e:
        LOGGER.info(f"⚠️  Phase 2 initialization skipped: {e}")

    # Initialize Phase 3 Services (optional, non-breaking)
    try:
        LOGGER.info("="*50)
        LOGGER.info("🚀 Initializing Phase 3: Advanced Features")
        LOGGER.info("="*50)
        from .core.enhanced_startup_phase3 import initialize_phase3_services
        phase3_status = await initialize_phase3_services()
        enabled = sum(1 for v in phase3_status.values() if v)
        LOGGER.info(f"✅ Phase 3: {enabled}/3 services enabled")
    except Exception as e:
        LOGGER.info(f"⚠️  Phase 3 initialization skipped: {e}")

    # Initialize Phase 4 Services (optional, non-breaking)
    try:
        from .core.enhanced_startup_phase4 import initialize_phase4_services
        phase4_status = await initialize_phase4_services()
        if phase4_status.get('success'):
            services_count = len(phase4_status.get('services_initialized', []))
            LOGGER.info(f"✅ Phase 4: {services_count} performance optimization services enabled")
        else:
            errors = phase4_status.get('errors', [])
            if errors:
                LOGGER.info(f"⚠️  Phase 4 initialization: {errors[0]}")
            else:
                LOGGER.info("⚠️  Phase 4 initialization skipped")
    except Exception as e:
        LOGGER.info(f"⚠️  Phase 4 initialization skipped: {e}")

    LOGGER.info("Loading settings...")
    await load_settings()
    LOGGER.info("✅ Settings loaded")
    
    LOGGER.info("Initializing task scheduler...")
    await TaskScheduler.init()
    LOGGER.info("✅ Task scheduler initialized")

    LOGGER.info("Starting Telegram clients...")
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
    from .helper.ext_utils.files_utils import clean_all
    from .core.jdownloader_booter import jdownloader
    from .helper.ext_utils.telegraph_helper import telegraph
    from .helper.mirror_leech_utils.rclone_utils.serve import rclone_serve_booter
    from .modules import (
        initiate_search_tools,
        get_packages_version,
        restart_notification,
    )

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

# Register Phase 4 shutdown handler
import atexit

def shutdown_phase4():
    """Shutdown Phase 4 services on exit"""
    try:
        from .core.enhanced_startup_phase4 import shutdown_phase4_services
        bot_loop.run_until_complete(shutdown_phase4_services())
    except Exception as e:
        LOGGER.debug(f"Phase 4 shutdown error: {e}")

atexit.register(shutdown_phase4)

from .helper.ext_utils.bot_utils import create_help_buttons
from .helper.listeners.aria2_listener import add_aria2_callbacks
from .core.handlers import add_handlers
from .modules.settings_ui import init_ui_monitor

add_aria2_callbacks()
create_help_buttons()
add_handlers()
init_ui_monitor()

LOGGER.info("Bot Started!")
bot_loop.run_forever()
