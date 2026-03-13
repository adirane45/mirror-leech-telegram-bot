from asyncio import create_subprocess_exec, create_subprocess_shell, sleep
from importlib import import_module
from os import environ

from aiofiles import open as aiopen
from aiofiles.os import makedirs
from aiofiles.os import path as aiopath
from aiofiles.os import remove
from aioshutil import rmtree

from .. import (
    LOGGER,
    aria2_options,
    auth_chats,
    drives_ids,
    drives_names,
    excluded_extensions,
    included_extensions,
    index_urls,
    nzb_options,
    qbit_options,
    rss_dict,
    sabnzbd_client,
    sudo_users,
    user_data,
)
from ..helper.ext_utils.db_handler import database
from .config_manager import Config
from .telegram_manager import TgClient
from .torrent_manager import TorrentManager


async def update_qb_options():
    LOGGER.info("Get qBittorrent options from server")
    try:
        qb_password = environ.get("QB_PASSWORD", "mltbmltb")
        if not qbit_options:
            opt = await TorrentManager.qbittorrent.app.preferences()
            qbit_options.update(opt)
            del qbit_options["listen_port"]
            for k in list(qbit_options.keys()):
                if k.startswith("rss"):
                    del qbit_options[k]
            qbit_options["web_ui_password"] = qb_password
            await TorrentManager.qbittorrent.app.set_preferences(
                {"web_ui_password": qb_password}
            )
        else:
            await TorrentManager.qbittorrent.app.set_preferences(qbit_options)
    except Exception as e:
        LOGGER.warning(f"qBittorrent options skipped: {e}")


async def update_aria2_options():
    LOGGER.info("Get aria2 options from server")
    try:
        if not aria2_options:
            op = await TorrentManager.aria2.getGlobalOption()
            aria2_options.update(op)
        else:
            await TorrentManager.aria2.changeGlobalOption(aria2_options)
    except Exception as e:
        LOGGER.warning(f"aria2 options skipped: {e}")


async def update_nzb_options():
    LOGGER.info("Get SABnzbd options from server")
    from asyncio import TimeoutError as AsyncioTimeoutError
    from asyncio import wait_for
    try:
        for _ in range(10):
            try:
                no = await wait_for(
                    sabnzbd_client.get_config(),
                    timeout=2.0
                )
                nzb_options.update(no["config"]["misc"])
                return
            except (Exception, AsyncioTimeoutError):
                await sleep(0.5)
    except Exception as e:
        LOGGER.warning(f"SABnzbd options error: {e}")
    LOGGER.warning("SABnzbd options skipped: service unavailable")


def _is_database_configured():
    return bool(Config.DATABASE_URL and Config.DATABASE_URL.strip())


async def _cleanup_user_artifacts():
    for p in ["thumbnails", "tokens", "rclone"]:
        if await aiopath.exists(p):
            await rmtree(p, ignore_errors=True)


async def _connect_database_with_timeout():
    LOGGER.info("🔌 Attempting MongoDB connection with 10-second timeout...")
    try:
        from asyncio import TimeoutError as AsyncTimeoutError
        from asyncio import wait_for

        LOGGER.info("⏳ Starting wait_for(database.connect(), timeout=10.0)...")
        await wait_for(database.connect(), timeout=10.0)
        LOGGER.info("✅ MongoDB connected successfully")
        return True
    except (AsyncTimeoutError, Exception) as e:
        LOGGER.warning(
            f"⏱️  MongoDB connection timeout/failed ({type(e).__name__}: {str(e)[:40]}). Continuing without database..."
        )
        return False


def _get_config_file_dict():
    settings = import_module("config")
    return {
        key: value.strip() if isinstance(value, str) else value
        for key, value in vars(settings).items()
        if not key.startswith("__")
    }


async def _load_deploy_config_with_timeout(bot_id):
    from asyncio import TimeoutError as AsyncTimeoutError
    from asyncio import wait_for

    try:
        LOGGER.info("🔍 START: Querying deployConfig (5s timeout)...")
        old_config = await wait_for(
            database.db.settings.deployConfig.find_one({"_id": bot_id}, {"_id": 0}),
            timeout=5.0,
        )
        LOGGER.info("🔍 END: deployConfig query complete")
        return old_config, False
    except AsyncTimeoutError:
        LOGGER.warning("⏱️  deployConfig query timed out (5s) - disabling database usage")
        database.db = None
        database._return = True
        return None, True
    except Exception as e:
        LOGGER.warning(
            f"MongoDB query compatibility issue (expected on MongoDB 4.4): {str(e)[:50]}"
        )
        return None, False


async def _sync_config_records(bot_id, old_config, config_file):
    if old_config is None:
        try:
            await database.db.settings.deployConfig.replace_one(
                {"_id": bot_id}, config_file, upsert=True
            )
        except Exception as e:
            LOGGER.warning(f"Could not save config to MongoDB: {str(e)[:50]}")
        return

    if old_config != config_file:
        LOGGER.info("Replacing existing deploy config in Database")
        try:
            await database.db.settings.deployConfig.replace_one(
                {"_id": bot_id}, config_file, upsert=True
            )
        except Exception as e:
            LOGGER.warning(f"Could not update config in MongoDB: {str(e)[:50]}")
        return

    try:
        config_dict = await database.db.settings.config.find_one({"_id": bot_id}, {"_id": 0})
        if config_dict:
            Config.load_dict(config_dict)
    except Exception as e:
        LOGGER.warning(f"Could not load config from MongoDB: {str(e)[:50]}")


async def _load_config_files(bot_id):
    try:
        if pf_dict := await database.db.settings.files.find_one({"_id": bot_id}, {"_id": 0}):
            for key, value in pf_dict.items():
                if value:
                    file_ = key.replace("__", ".")
                    async with aiopen(file_, "wb+") as f:
                        await f.write(value)
    except Exception as e:
        LOGGER.debug(f"No files config in MongoDB: {str(e)[:50]}")


async def _load_aria2_options(bot_id):
    try:
        if a2c_options_data := await database.db.settings.aria2c.find_one(
            {"_id": bot_id}, {"_id": 0}
        ):
            aria2_options.update(a2c_options_data)
    except Exception as e:
        LOGGER.debug(f"No aria2c config in MongoDB: {str(e)[:50]}")


async def _load_qbit_options(bot_id):
    try:
        if qbit_opt := await database.db.settings.qbittorrent.find_one(
            {"_id": bot_id}, {"_id": 0}
        ):
            qbit_options.update(qbit_opt)
    except Exception as e:
        LOGGER.debug(f"No qbittorrent config in MongoDB: {str(e)[:50]}")


async def _load_nzb_options(bot_id):
    try:
        if nzb_opt := await database.db.settings.nzb.find_one({"_id": bot_id}, {"_id": 0}):
            if await aiopath.exists("sabnzbd/SABnzbd.ini.bak"):
                await remove("sabnzbd/SABnzbd.ini.bak")
            ((key, value),) = nzb_opt.items()
            file_ = key.replace("__", ".")
            async with aiopen(f"sabnzbd/{file_}", "wb+") as f:
                await f.write(value)
    except Exception as e:
        LOGGER.debug(f"No nzb config in MongoDB: {str(e)[:50]}")


async def _load_users_data():
    try:
        if await database.db.users.find_one():
            for p in ["thumbnails", "tokens", "rclone"]:
                if not await aiopath.exists(p):
                    await makedirs(p)
            rows = database.db.users.find({})
            async for row in rows:
                uid = row["_id"]
                del row["_id"]
                thumb_path = f"thumbnails/{uid}.jpg"
                rclone_config_path = f"rclone/{uid}.conf"
                token_path = f"tokens/{uid}.pickle"
                if row.get("THUMBNAIL"):
                    async with aiopen(thumb_path, "wb+") as f:
                        await f.write(row["THUMBNAIL"])
                    row["THUMBNAIL"] = thumb_path
                if row.get("RCLONE_CONFIG"):
                    async with aiopen(rclone_config_path, "wb+") as f:
                        await f.write(row["RCLONE_CONFIG"])
                    row["RCLONE_CONFIG"] = rclone_config_path
                if row.get("TOKEN_PICKLE"):
                    async with aiopen(token_path, "wb+") as f:
                        await f.write(row["TOKEN_PICKLE"])
                    row["TOKEN_PICKLE"] = token_path
                user_data[uid] = row
            LOGGER.info("Users data has been imported from Database")
    except Exception as e:
        LOGGER.debug(f"No user data in MongoDB: {str(e)[:50]}")


async def _load_rss_data(bot_id):
    try:
        if await database.db.rss[bot_id].find_one():
            rows = database.db.rss[bot_id].find({})
            async for row in rows:
                user_id = row["_id"]
                del row["_id"]
                rss_dict[user_id] = row
            LOGGER.info("Rss data has been imported from Database.")
    except Exception as e:
        LOGGER.debug(f"No rss data in MongoDB: {str(e)[:50]}")


async def load_settings():
    LOGGER.info(
        f"🔍 DEBUG: DATABASE_URL is {'EMPTY' if not Config.DATABASE_URL else f'SET to {str(Config.DATABASE_URL)[:50]}'}"
    )
    if not _is_database_configured():
        LOGGER.info("📊 MongoDB disabled - using local config only")
        return

    await _cleanup_user_artifacts()

    if not await _connect_database_with_timeout():
        return

    if database.db is not None:
        LOGGER.info("📌 Entering database query block...")
        bot_id = Config.BOT_TOKEN.split(":", 1)[0]
        config_file = _get_config_file_dict()

        old_config, should_exit = await _load_deploy_config_with_timeout(bot_id)
        if should_exit:
            return

        await _sync_config_records(bot_id, old_config, config_file)
        await _load_config_files(bot_id)
        await _load_aria2_options(bot_id)
        await _load_qbit_options(bot_id)
        await _load_nzb_options(bot_id)
        await _load_users_data()
        await _load_rss_data(bot_id)


async def save_settings():
    if database.db is None or not TgClient or not hasattr(TgClient, 'ID'):
        return
    config_dict = Config.get_all()
    await database.db.settings.config.replace_one(
        {"_id": TgClient.ID}, config_dict, upsert=True
    )
    if await database.db.settings.aria2c.find_one({"_id": TgClient.ID}) is None:
        await database.db.settings.aria2c.update_one(
            {"_id": TgClient.ID}, {"$set": aria2_options}, upsert=True
        )
    if await database.db.settings.qbittorrent.find_one({"_id": TgClient.ID}) is None:
        await database.save_qbit_settings()
    if await database.db.settings.nzb.find_one({"_id": TgClient.ID}) is None:
        async with aiopen("sabnzbd/SABnzbd.ini", "rb+") as pf:
            nzb_conf = await pf.read()
        await database.db.settings.nzb.update_one(
            {"_id": TgClient.ID}, {"$set": {"SABnzbd__ini": nzb_conf}}, upsert=True
        )


def _update_split_size():
    """Update leech split size based on client limits."""
    if TgClient and hasattr(TgClient, 'MAX_SPLIT_SIZE'):
        if (
            Config.LEECH_SPLIT_SIZE > TgClient.MAX_SPLIT_SIZE
            or Config.LEECH_SPLIT_SIZE == 2097152000
            or not Config.LEECH_SPLIT_SIZE
        ):
            Config.LEECH_SPLIT_SIZE = TgClient.MAX_SPLIT_SIZE


def _update_premium_features():
    """Update premium-dependent features."""
    is_premium = TgClient and hasattr(TgClient, 'IS_PREMIUM_USER') and TgClient.IS_PREMIUM_USER
    Config.HYBRID_LEECH = bool(Config.HYBRID_LEECH and is_premium)
    Config.USER_TRANSMISSION = bool(Config.USER_TRANSMISSION and is_premium)


def _populate_auth_chats():
    """Populate authorized chats from config."""
    LOGGER.info(f"🔍 Populating auth_chats from AUTHORIZED_CHATS: {Config.AUTHORIZED_CHATS}")
    if Config.AUTHORIZED_CHATS:
        aid = Config.AUTHORIZED_CHATS.replace(",", " ").split()
        for id_ in aid:
            chat_id, *thread_ids = id_.split("|")
            chat_id = int(chat_id.strip())
            if thread_ids:
                thread_ids = list(map(lambda x: int(x.strip()), thread_ids))
                auth_chats[chat_id] = thread_ids
            else:
                auth_chats[chat_id] = []
        LOGGER.info(f"✅ auth_chats populated: {dict(auth_chats)}")
    else:
        LOGGER.warning("⚠️  AUTHORIZED_CHATS is empty or not set")


def _populate_sudo_users():
    """Populate sudo users from config."""
    LOGGER.info(f"🔍 Populating sudo_users from SUDO_USERS: {Config.SUDO_USERS}")
    if Config.SUDO_USERS:
        aid = Config.SUDO_USERS.replace(",", " ").split()
        for id_ in aid:
            sudo_users.append(int(id_.strip()))
        LOGGER.info(f"✅ sudo_users populated: {sudo_users}")
    else:
        LOGGER.warning("⚠️  SUDO_USERS is empty or not set")


def _populate_extensions():
    """Populate included and excluded extensions."""
    if Config.EXCLUDED_EXTENSIONS:
        fx = Config.EXCLUDED_EXTENSIONS.split()
        for x in fx:
            x = x.lstrip(".")
            excluded_extensions.append(x.strip().lower())

    if Config.INCLUDED_EXTENSIONS:
        fx = Config.INCLUDED_EXTENSIONS.split()
        for x in fx:
            x = x.lstrip(".")
            included_extensions.append(x.strip().lower())


def _populate_main_gdrive():
    """Populate main Google Drive configuration."""
    if Config.GDRIVE_ID:
        drives_names.append("Main")
        drives_ids.append(Config.GDRIVE_ID)
        index_urls.append(Config.INDEX_URL)


async def _populate_list_drives():
    """Populate additional drives from list_drives.txt."""
    if await aiopath.exists("list_drives.txt"):
        async with aiopen("list_drives.txt", "r+") as f:
            lines = await f.readlines()
            for line in lines:
                temp = line.split()
                drives_ids.append(temp[1])
                drives_names.append(temp[0].replace("_", " "))
                if len(temp) > 2:
                    index_urls.append(temp[2])
                else:
                    index_urls.append("")


async def update_variables():
    _update_split_size()
    _update_premium_features()
    _populate_auth_chats()
    _populate_sudo_users()
    _populate_extensions()
    _populate_main_gdrive()
    await _populate_list_drives()



async def load_configurations():

    if not await aiopath.exists(".netrc"):
        async with aiopen(".netrc", "w"):
            pass

    if await aiopath.exists("aria-nox-nzb.sh"):
        await (
            await create_subprocess_shell(
                "chmod 600 .netrc && cp .netrc /root/.netrc && chmod +x aria-nox-nzb.sh && ./aria-nox-nzb.sh"
            )
        ).wait()
    else:
        await create_subprocess_shell("chmod 600 .netrc && cp .netrc /root/.netrc")
        LOGGER.warning("aria-nox-nzb.sh not found; skipping aria-nox bootstrap")

    if Config.BASE_URL:
        await create_subprocess_shell(
            f"gunicorn -k uvicorn.workers.UvicornWorker -w 1 web.wserver:app --bind 0.0.0.0:8060"
        )

    if await aiopath.exists("cfg.zip"):
        if await aiopath.exists("/JDownloader/cfg"):
            await rmtree("/JDownloader/cfg", ignore_errors=True)
        await (
            await create_subprocess_exec("7z", "x", "cfg.zip", "-o/JDownloader")
        ).wait()

    if await aiopath.exists("accounts.zip"):
        if await aiopath.exists("accounts"):
            await rmtree("accounts")
        await (
            await create_subprocess_exec(
                "7z", "x", "-o.", "-aoa", "accounts.zip", "accounts/*.json"
            )
        ).wait()
        await (await create_subprocess_exec("chmod", "-R", "777", "accounts")).wait()
        await remove("accounts.zip")

    if not await aiopath.exists("accounts"):
        Config.USE_SERVICE_ACCOUNTS = False
