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

    await load_settings()
    await TaskScheduler.init()

    await gather(TgClient.start_bot(), TgClient.start_user())
    await gather(load_configurations(), update_variables())

    from .core.torrent_manager import TorrentManager

    await TorrentManager.initiate()
    await gather(
        update_qb_options(),
        update_aria2_options(),
        update_nzb_options(),
    )
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
    
    await gather(
        save_settings(),
        jdownloader.boot(),
        clean_all(),
        initiate_search_tools(),
        get_packages_version(),
        restart_notification(),
        telegraph.create_account(),
        rclone_serve_booter(),
    )
    
    # Set bot commands for Telegram menu
    from .helper.ext_utils.bot_commands_setup import set_bot_commands
    await set_bot_commands()


bot_loop.run_until_complete(main())

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
