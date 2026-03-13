from asyncio import create_subprocess_exec, create_subprocess_shell, gather, sleep
from functools import partial
from io import BytesIO
from os import getcwd
from time import time

from aiofiles import open as aiopen
from aiofiles.os import path as aiopath
from aiofiles.os import remove, rename
from aioshutil import rmtree
from pyrogram.filters import create
from pyrogram.handlers import MessageHandler

from .. import (
    LOGGER,
    aria2_options,
    auth_chats,
    drives_ids,
    drives_names,
    excluded_extensions,
    included_extensions,
    index_urls,
    intervals,
    jd_listener_lock,
    nzb_options,
    qbit_options,
    sabnzbd_client,
    sudo_users,
    task_dict,
)
from ..core.config_manager import Config
from ..core.jdownloader_booter import jdownloader
from ..core.startup import update_nzb_options, update_qb_options, update_variables
from ..core.telegram_manager import TgClient
from ..core.torrent_manager import TorrentManager
from ..helper.ext_utils.bot_utils import SetInterval, new_task
from ..helper.ext_utils.db_handler import database
from ..helper.ext_utils.task_manager import start_from_queued
from ..helper.mirror_leech_utils.rclone_utils.serve import rclone_serve_booter
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.message_utils import (
    delete_message,
    edit_message,
    send_file,
    send_message,
    update_status_message,
)
from .rss import add_job
from .search import initiate_search_tools

start = 0
state = "view"
handler_dict = {}
DEFAULT_VALUES = {
    "LEECH_SPLIT_SIZE": TgClient.MAX_SPLIT_SIZE,
    "RSS_DELAY": 600,
    "STATUS_UPDATE_INTERVAL": 15,
    "SEARCH_LIMIT": 0,
    "UPSTREAM_BRANCH": "master",
    "DEFAULT_UPLOAD": "rc",
}


def _build_root_buttons(buttons):
    buttons.data_button("Config Variables", "botset var")
    buttons.data_button("Private Files", "botset private")
    buttons.data_button("Qbit Settings", "botset qbit")
    buttons.data_button("Aria2c Settings", "botset aria")
    buttons.data_button("Sabnzbd Settings", "botset nzb")
    buttons.data_button("JDownloader Sync", "botset syncjd")
    buttons.data_button("Close", "botset close")
    return "Bot Settings:"


def _build_botvar_prompt(buttons, key):
    msg = ""
    buttons.data_button("Back", "botset var")
    if key not in ["TELEGRAM_HASH", "TELEGRAM_API", "OWNER_ID", "BOT_TOKEN"]:
        buttons.data_button("Default", f"botset resetvar {key}")
    buttons.data_button("Close", "botset close")
    if key in [
        "CMD_SUFFIX",
        "OWNER_ID",
        "USER_SESSION_STRING",
        "TELEGRAM_HASH",
        "TELEGRAM_API",
        "BOT_TOKEN",
        "TG_PROXY",
    ]:
        msg += "Restart required for this edit to take effect! You will not see the changes in bot vars, the edit will be in database only!\n\n"
    msg += f"Send a valid value for {key}. Current value is '{Config.get(key)}'. Timeout: 60 sec"
    return msg


def _build_ariavar_prompt(buttons, key):
    buttons.data_button("Back", "botset aria")
    if key != "newkey":
        buttons.data_button("Empty String", f"botset emptyaria {key}")
    buttons.data_button("Close", "botset close")
    return (
        "Send a key with value. Example: https-proxy-user:value. Timeout: 60 sec"
        if key == "newkey"
        else f"Send a valid value for {key}. Current value is '{aria2_options[key]}'. Timeout: 60 sec"
    )


def _build_qbitvar_prompt(buttons, key):
    buttons.data_button("Back", "botset qbit")
    buttons.data_button("Empty String", f"botset emptyqbit {key}")
    buttons.data_button("Close", "botset close")
    return f"Send a valid value for {key}. Current value is '{qbit_options[key]}'. Timeout: 60 sec"


def _build_nzbvar_prompt(buttons, key):
    buttons.data_button("Back", "botset nzb")
    buttons.data_button("Default", f"botset resetnzb {key}")
    buttons.data_button("Empty String", f"botset emptynzb {key}")
    buttons.data_button("Close", "botset close")
    return f"Send a valid value for {key}. Current value is '{nzb_options[key]}'.\nIf the value is list then separate them by space or ,\nExample: .exe,info or .exe .info\nTimeout: 60 sec"


def _build_nzbsevar_prompt(buttons, key, edit_type):
    index = 0 if key == "newser" else int(edit_type.replace("nzbsevar", ""))
    if key == "newser":
        buttons.data_button("Back", "botset nzbserver")
        msg = "Send one server as dictionary {}, like in config.py without []. Timeout: 60 sec"
    else:
        buttons.data_button("Empty", f"botset emptyserkey {index} {key}")
        buttons.data_button("Back", f"botset nzbser{index}")
        msg = f"Send a valid value for {key} in server {Config.USENET_SERVERS[index]['name']}. Current value is {Config.USENET_SERVERS[index][key]}. Timeout: 60 sec"
    buttons.data_button("Close", "botset close")
    return msg


def _build_edit_prompt(buttons, key, edit_type):
    if edit_type == "botvar":
        return _build_botvar_prompt(buttons, key)
    if edit_type == "ariavar":
        return _build_ariavar_prompt(buttons, key)
    if edit_type == "qbitvar":
        return _build_qbitvar_prompt(buttons, key)
    if edit_type == "nzbvar":
        return _build_nzbvar_prompt(buttons, key)
    if edit_type.startswith("nzbsevar"):
        return _build_nzbsevar_prompt(buttons, key, edit_type)
    return ""


def _build_var_buttons(buttons):
    conf_dict = Config.get_all()
    for k in list(conf_dict.keys())[start : 10 + start]:
        if k in ["DATABASE_URL", "DATABASE_NAME"] and state != "view":
            continue
        buttons.data_button(k, f"botset botvar {k}")
    if state == "view":
        buttons.data_button("Edit", "botset edit var")
    else:
        buttons.data_button("View", "botset view var")
    buttons.data_button("Back", "botset back")
    buttons.data_button("Close", "botset close")
    for x in range(0, len(conf_dict), 10):
        buttons.data_button(f"{int(x / 10)}", f"botset start var {x}", position="footer")
    return f"Config Variables | Page: {int(start / 10)} | State: {state}"


def _build_private_buttons(buttons):
    buttons.data_button("Back", "botset back")
    buttons.data_button("Close", "botset close")
    return """Send private file: config.py, token.pickle, rclone.conf, accounts.zip, list_drives.txt, cookies.txt, .netrc or any other private file!
To delete private file send only the file name as text message.
Note: Changing .netrc will not take effect for aria2c until restart.
Timeout: 60 sec"""


def _build_aria_buttons(buttons):
    for k in list(aria2_options.keys())[start : 10 + start]:
        if k not in ["checksum", "index-out", "out", "pause", "select-file"]:
            buttons.data_button(k, f"botset ariavar {k}")
    if state == "view":
        buttons.data_button("Edit", "botset edit aria")
    else:
        buttons.data_button("View", "botset view aria")
    buttons.data_button("Add new key", "botset ariavar newkey")
    buttons.data_button("Back", "botset back")
    buttons.data_button("Close", "botset close")
    for x in range(0, len(aria2_options), 10):
        buttons.data_button(f"{int(x / 10)}", f"botset start aria {x}", position="footer")
    return f"Aria2c Options | Page: {int(start / 10)} | State: {state}"


def _build_qbit_buttons(buttons):
    for k in list(qbit_options.keys())[start : 10 + start]:
        buttons.data_button(k, f"botset qbitvar {k}")
    if state == "view":
        buttons.data_button("Edit", "botset edit qbit")
    else:
        buttons.data_button("View", "botset view qbit")
    buttons.data_button("Sync Qbittorrent", "botset syncqbit")
    buttons.data_button("Back", "botset back")
    buttons.data_button("Close", "botset close")
    for x in range(0, len(qbit_options), 10):
        buttons.data_button(f"{int(x / 10)}", f"botset start qbit {x}", position="footer")
    return f"Qbittorrent Options | Page: {int(start / 10)} | State: {state}"


def _build_nzb_buttons(buttons):
    for k in list(nzb_options.keys())[start : 10 + start]:
        buttons.data_button(k, f"botset nzbvar {k}")
    if state == "view":
        buttons.data_button("Edit", "botset edit nzb")
    else:
        buttons.data_button("View", "botset view nzb")
    buttons.data_button("Servers", "botset nzbserver")
    buttons.data_button("Sync Sabnzbd", "botset syncnzb")
    buttons.data_button("Back", "botset back")
    buttons.data_button("Close", "botset close")
    for x in range(0, len(nzb_options), 10):
        buttons.data_button(f"{int(x / 10)}", f"botset start nzb {x}", position="footer")
    return f"Sabnzbd Options | Page: {int(start / 10)} | State: {state}"


def _build_nzbserver_buttons(buttons):
    if len(Config.USENET_SERVERS) > 0:
        for index, k in enumerate(Config.USENET_SERVERS[start : 10 + start]):
            buttons.data_button(k["name"], f"botset nzbser{index}")
    buttons.data_button("Add New", "botset nzbsevar newser")
    buttons.data_button("Back", "botset nzb")
    buttons.data_button("Close", "botset close")
    if len(Config.USENET_SERVERS) > 10:
        for x in range(0, len(Config.USENET_SERVERS), 10):
            buttons.data_button(f"{int(x / 10)}", f"botset start nzbser {x}", position="footer")
    return f"Usenet Servers | Page: {int(start / 10)} | State: {state}"


def _build_nzbser_buttons(buttons, key):
    index = int(key.replace("nzbser", ""))
    for k in list(Config.USENET_SERVERS[index].keys())[start : 10 + start]:
        buttons.data_button(k, f"botset nzbsevar{index} {k}")
    if state == "view":
        buttons.data_button("Edit", f"botset edit {key}")
    else:
        buttons.data_button("View", f"botset view {key}")
    buttons.data_button("Remove Server", f"botset remser {index}")
    buttons.data_button("Back", "botset nzbserver")
    buttons.data_button("Close", "botset close")
    if len(Config.USENET_SERVERS[index].keys()) > 10:
        for x in range(0, len(Config.USENET_SERVERS[index]), 10):
            buttons.data_button(f"{int(x / 10)}", f"botset start {key} {x}", position="footer")
    return f"Server Keys | Page: {int(start / 10)} | State: {state}"


async def get_buttons(key=None, edit_type=None):
    buttons = ButtonMaker()
    msg = "Bot Settings:"

    if key is None:
        msg = _build_root_buttons(buttons)
    elif edit_type is not None:
        msg = _build_edit_prompt(buttons, key, edit_type)
    else:
        msg = _build_settings_section(buttons, key)

    button = buttons.build_menu(1) if key is None else buttons.build_menu(2)
    return msg, button


def _build_settings_section(buttons, key):
    section_builders = {
        "var": _build_var_buttons,
        "private": _build_private_buttons,
        "aria": _build_aria_buttons,
        "qbit": _build_qbit_buttons,
        "nzb": _build_nzb_buttons,
        "nzbserver": _build_nzbserver_buttons,
    }

    builder = section_builders.get(key)
    if builder:
        return builder(buttons)
    if key.startswith("nzbser"):
        return _build_nzbser_buttons(buttons, key)
    return "Bot Settings:"


async def update_buttons(message, key=None, edit_type=None):
    msg, button = await get_buttons(key, edit_type)
    await edit_message(message, msg, button)


def _normalize_extension_values(raw_value):
    values = []
    for value in raw_value.split():
        value = value.lstrip(".")
        values.append(value.strip().lower())
    return values


def _apply_authorized_chats(raw_value):
    aid = raw_value.split()
    auth_chats.clear()
    for id_ in aid:
        chat_id, *thread_ids = id_.split("|")
        chat_id = int(chat_id.strip())
        if thread_ids:
            thread_ids = list(map(lambda x: int(x.strip()), thread_ids))
            auth_chats[chat_id] = thread_ids
        else:
            auth_chats[chat_id] = []


def _apply_sudo_users(raw_value):
    sudo_users.clear()
    for id_ in raw_value.split():
        sudo_users.append(int(id_.strip()))


async def _transform_status_update_interval(raw_value):
    """Transform STATUS_UPDATE_INTERVAL with interval cancellation."""
    interval_value = int(raw_value)
    if len(task_dict) != 0 and (st := intervals["status"]):
        for cid, intvl in list(st.items()):
            intvl.cancel()
            intervals["status"][cid] = SetInterval(
                interval_value, update_status_message, cid
            )
    return interval_value


async def _transform_base_url_port(raw_value):
    """Transform BASE_URL_PORT and restart gunicorn."""
    port_value = int(raw_value)
    if Config.BASE_URL:
        await (await create_subprocess_exec("pkill", "-9", "-f", "gunicorn")).wait()
        await create_subprocess_shell(
            f"gunicorn -k uvicorn.workers.UvicornWorker -w 1 web.wserver:app --bind 0.0.0.0:{port_value}"
        )
    return port_value


async def _transform_extensions(key, raw_value):
    """Transform EXCLUDED_EXTENSIONS or INCLUDED_EXTENSIONS."""
    if key == "EXCLUDED_EXTENSIONS":
        excluded_extensions.clear()
        excluded_extensions.extend(["aria2", "!qB"])
        excluded_extensions.extend(_normalize_extension_values(raw_value))
    elif key == "INCLUDED_EXTENSIONS":
        included_extensions.clear()
        included_extensions.extend(_normalize_extension_values(raw_value))
    return raw_value


async def _transform_drive_id(raw_value):
    """Transform GDRIVE_ID and update drives list."""
    if drives_names and drives_names[0] == "Main":
        drives_ids[0] = raw_value
    else:
        drives_ids.insert(0, raw_value)
    return raw_value


async def _transform_index_url(raw_value):
    """Transform INDEX_URL and update index_urls list."""
    if drives_names and drives_names[0] == "Main":
        index_urls[0] = raw_value
    else:
        index_urls.insert(0, raw_value)
    return raw_value


async def _transform_torrent_timeout(raw_value):
    await TorrentManager.change_aria2_option("bt-stop-timeout", raw_value)
    return int(raw_value)


def _transform_leech_split_size(raw_value):
    return min(int(raw_value), TgClient.MAX_SPLIT_SIZE)


async def _transform_excluded_extensions(raw_value):
    return await _transform_extensions("EXCLUDED_EXTENSIONS", raw_value)


async def _transform_included_extensions(raw_value):
    return await _transform_extensions("INCLUDED_EXTENSIONS", raw_value)


def _transform_authorized_chats(raw_value):
    _apply_authorized_chats(raw_value)
    return raw_value


def _transform_sudo_users_value(raw_value):
    _apply_sudo_users(raw_value)
    return raw_value


async def _transform_false_boolean_effects(key):
    if key == "INCOMPLETE_TASK_NOTIFIER" and Config.DATABASE_URL:
        await database.trunc_table("tasks")


async def _transform_boolean_value(key, lower_value):
    if lower_value == "true":
        return True
    if lower_value == "false":
        await _transform_false_boolean_effects(key)
        return False
    return None


def _transform_generic_edit_value(raw_value):
    if raw_value.isdigit():
        return int(raw_value)
    if raw_value.startswith("[") and raw_value.endswith("]"):
        return eval(raw_value)
    if raw_value.startswith("{") and raw_value.endswith("}"):
        return eval(raw_value)
    return raw_value


ASYNC_EDIT_VARIABLE_TRANSFORMERS = {
    "STATUS_UPDATE_INTERVAL": _transform_status_update_interval,
    "TORRENT_TIMEOUT": _transform_torrent_timeout,
    "BASE_URL_PORT": _transform_base_url_port,
    "EXCLUDED_EXTENSIONS": _transform_excluded_extensions,
    "INCLUDED_EXTENSIONS": _transform_included_extensions,
    "GDRIVE_ID": _transform_drive_id,
    "INDEX_URL": _transform_index_url,
}


SYNC_EDIT_VARIABLE_TRANSFORMERS = {
    "LEECH_SPLIT_SIZE": _transform_leech_split_size,
    "AUTHORIZED_CHATS": _transform_authorized_chats,
    "SUDO_USERS": _transform_sudo_users_value,
}


async def _transform_edit_variable_value(key, raw_value):
    """Transform raw input value to configured type for given key."""
    lower_value = raw_value.lower()
    boolean_value = await _transform_boolean_value(key, lower_value)
    if boolean_value is not None:
        return boolean_value

    async_transformer = ASYNC_EDIT_VARIABLE_TRANSFORMERS.get(key)
    if async_transformer is not None:
        return await async_transformer(raw_value)

    sync_transformer = SYNC_EDIT_VARIABLE_TRANSFORMERS.get(key)
    if sync_transformer is not None:
        return sync_transformer(raw_value)

    return _transform_generic_edit_value(raw_value)


async def _run_edit_variable_post_hooks(key, value):
    if key in ["SEARCH_PLUGINS", "SEARCH_API_LINK"]:
        await initiate_search_tools()
    elif key in ["QUEUE_ALL", "QUEUE_DOWNLOAD", "QUEUE_UPLOAD"]:
        await start_from_queued()
    elif key in [
        "RCLONE_SERVE_URL",
        "RCLONE_SERVE_PORT",
        "RCLONE_SERVE_USER",
        "RCLONE_SERVE_PASS",
    ]:
        await rclone_serve_booter()
    elif key in ["JD_EMAIL", "JD_PASS"]:
        await jdownloader.boot()
    elif key == "RSS_DELAY":
        add_job()
    elif key == "USET_SERVERS":
        for s in value:
            await sabnzbd_client.set_special_config("servers", s)


@new_task
async def edit_variable(_, message, pre_message, key):
    handler_dict[message.chat.id] = False
    raw_value = str(message.text)
    value = await _transform_edit_variable_value(key, raw_value)
    Config.set(key, value)
    await update_buttons(pre_message, "var")
    await delete_message(message)
    await database.update_config({key: value})
    await _run_edit_variable_post_hooks(key, value)


@new_task
async def edit_aria(_, message, pre_message, key):
    handler_dict[message.chat.id] = False
    value = str(message.text)
    if key == "newkey":
        key, value = [x.strip() for x in value.split(":", 1)]
    elif value.lower() == "true":
        value = "true"
    elif value.lower() == "false":
        value = "false"
    await TorrentManager.change_aria2_option(key, value)
    await update_buttons(pre_message, "aria")
    await delete_message(message)
    await database.update_aria2(key, value)


@new_task
async def edit_qbit(_, message, pre_message, key):
    handler_dict[message.chat.id] = False
    value = str(message.text)
    if value.lower() == "true":
        value = True
    elif value.lower() == "false":
        value = False
    elif key == "max_ratio":
        value = float(value)
    elif value.isdigit():
        value = int(value)
    await TorrentManager.qbittorrent.app.set_preferences({key: value})
    qbit_options[key] = value
    await update_buttons(pre_message, "qbit")
    await delete_message(message)
    await database.update_qbittorrent(key, value)


@new_task
async def edit_nzb(_, message, pre_message, key):
    handler_dict[message.chat.id] = False
    value = str(message.text)
    if value.isdigit():
        value = int(value)
    elif value.startswith("[") and value.endswith("]"):
        try:
            value = ",".join(eval(value))
        except Exception as e:
            LOGGER.error(e)
            await update_buttons(pre_message, "nzb")
            return
    res = await sabnzbd_client.set_config("misc", key, value)
    nzb_options[key] = res["config"]["misc"][key]
    await update_buttons(pre_message, "nzb")
    await delete_message(message)
    await database.update_nzb_config()


@new_task
async def edit_nzb_server(_, message, pre_message, key, index=0):
    handler_dict[message.chat.id] = False
    value = str(message.text)
    if key == "newser":
        if value.startswith("{") and value.endswith("}"):
            try:
                value = eval(value)
            except (SyntaxError, ValueError, TypeError) as e:
                await send_message(message, f"Invalid dict format: {e}")
                await update_buttons(pre_message, "nzbserver")
                return
            res = await sabnzbd_client.add_server(value)
            if not res["config"]["servers"][0]["host"]:
                await send_message(message, "Invalid server!")
                await update_buttons(pre_message, "nzbserver")
                return
            Config.USENET_SERVERS.append(value)
            await update_buttons(pre_message, "nzbserver")
        else:
            await send_message(message, "Invalid dict format!")
            await update_buttons(pre_message, "nzbserver")
            return
    else:
        if value.isdigit():
            value = int(value)
        res = await sabnzbd_client.add_server(
            {"name": Config.USENET_SERVERS[index]["name"], key: value}
        )
        if res["config"]["servers"][0][key] == "":
            await send_message(message, "Invalid value")
            return
        Config.USENET_SERVERS[index][key] = value
        await update_buttons(pre_message, f"nzbser{index}")
    await delete_message(message)
    await database.update_config({"USENET_SERVERS": Config.USENET_SERVERS})


async def sync_jdownloader():
    async with jd_listener_lock:
        if not Config.DATABASE_URL or not jdownloader.is_connected:
            return
        await jdownloader.device.system.exit_jd()
    if await aiopath.exists("cfg.zip"):
        await remove("cfg.zip")
    await (
        await create_subprocess_exec("7z", "a", "cfg.zip", "/JDownloader/cfg")
    ).wait()
    await database.update_private_file("cfg.zip")


@new_task
async def _handle_text_input_file(file_name):
    """Handle file deletion/operation from text input."""
    if await aiopath.isfile(file_name) and file_name != "config.py":
        await remove(file_name)
    if file_name == "accounts.zip":
        if await aiopath.exists("accounts"):
            await rmtree("accounts", ignore_errors=True)
        if await aiopath.exists("rclone_sa"):
            await rmtree("rclone_sa", ignore_errors=True)
        Config.USE_SERVICE_ACCOUNTS = False
        await database.update_config({"USE_SERVICE_ACCOUNTS": False})
    elif file_name in {".netrc", "netrc"}:
        await (await create_subprocess_exec("touch", ".netrc")).wait()
        await (await create_subprocess_exec("chmod", "600", ".netrc")).wait()
        await (await create_subprocess_exec("cp", ".netrc", "/root/.netrc")).wait()


async def _handle_accounts_zip_upload(fpath):
    """Handle accounts.zip upload extraction and cleanup."""
    if await aiopath.exists("accounts"):
        await rmtree("accounts", ignore_errors=True)
    if await aiopath.exists("rclone_sa"):
        await rmtree("rclone_sa", ignore_errors=True)
    await (
        await create_subprocess_exec(
            "7z", "x", "-o.", "-aoa", fpath, "accounts/*.json"
        )
    ).wait()
    await (
        await create_subprocess_exec("chmod", "-R", "777", "accounts")
    ).wait()


async def _handle_list_drives_upload(fpath):
    """Handle list_drives.txt upload and parse drives."""
    drives_ids.clear()
    drives_names.clear()
    index_urls.clear()
    if Config.GDRIVE_ID:
        drives_names.append("Main")
        drives_ids.append(Config.GDRIVE_ID)
        index_urls.append(Config.INDEX_URL)
    async with aiopen(fpath, "r+") as f:
        lines = await f.readlines()
        for line in lines:
            temp = line.strip().split()
            drives_ids.append(temp[1])
            drives_names.append(temp[0].replace("_", " "))
            if len(temp) > 2:
                index_urls.append(temp[2])
            else:
                index_urls.append("")


async def _handle_netrc_upload(fpath, file_name):
    """Handle .netrc file upload and setup permissions."""
    if file_name == "netrc":
        await rename(fpath, ".netrc")
        file_name = ".netrc"
        fpath = ".netrc"
    await (await create_subprocess_exec("chmod", "600", fpath)).wait()
    await (await create_subprocess_exec("cp", fpath, "/root/.netrc")).wait()
    return file_name


async def _handle_uploaded_document(file_name, fpath):
    """Handle uploaded document based on file type."""
    if file_name == "accounts.zip":
        await _handle_accounts_zip_upload(fpath)
    elif file_name == "list_drives.txt":
        await _handle_list_drives_upload(fpath)
    elif file_name in [".netrc", "netrc"]:
        file_name = await _handle_netrc_upload(fpath, file_name)
    elif file_name == "config.py":
        await load_config()
    return file_name


async def _show_push_confirmation(message, file_name):
    """Show push to upstream confirmation or delete message."""
    if "@github.com" in Config.UPSTREAM_REPO:
        buttons = ButtonMaker()
        msg = "Push to UPSTREAM_REPO ?"
        buttons.data_button("Yes!", f"botset push {file_name}")
        buttons.data_button("No", "botset close")
        await send_message(message, msg, buttons.build_menu(2))
    else:
        await delete_message(message)


async def update_private_file(_, message, pre_message):
    """Handle private file uploads/deletes from text or document."""
    handler_dict[message.chat.id] = False
    file_name = None

    # Handle text input (file path as string)
    if not message.media and (file_name := str(message.text)):
        await _handle_text_input_file(file_name)
        await delete_message(message)
    
    # Handle document upload
    elif doc := message.document:
        file_name = doc.file_name
        fpath = f"{getcwd()}/{file_name}"
        if await aiopath.exists(fpath):
            await remove(fpath)
        await message.download(file_name=fpath)
        file_name = await _handle_uploaded_document(file_name, fpath)
        await _show_push_confirmation(message, file_name)

    # Post-upload/delete actions
    if file_name == "rclone.conf":
        await rclone_serve_booter()
    await update_buttons(pre_message)
    if file_name:
        await database.update_private_file(file_name)


async def event_handler(client, query, pfunc, rfunc, document=False):
    chat_id = query.message.chat.id
    handler_dict[chat_id] = True
    start_time = time()

    async def event_filter(_, __, event):
        user = event.from_user or event.sender_chat
        return bool(
            user.id == query.from_user.id
            and event.chat.id == chat_id
            and (event.text or event.document and document)
        )

    handler = client.add_handler(
        MessageHandler(pfunc, filters=create(event_filter)), group=-1
    )
    while handler_dict[chat_id]:
        await sleep(0.5)
        if time() - start_time > 60:
            handler_dict[chat_id] = False
            await rfunc()
    client.remove_handler(*handler)


async def _answer_value_or_send_file(query, message, key, value):
    if len(value) > 200:
        await query.answer()
        with BytesIO(str.encode(value)) as out_file:
            out_file.name = f"{key}.txt"
            await send_file(message, out_file)
        return True
    if value == "":
        value = None
    await query.answer(f"{value}", show_alert=True)
    return True


def _get_resetvar_default_value(key):
    expected_type = type(getattr(Config, key))
    if expected_type == bool:
        return False
    if expected_type == int:
        return 0
    if expected_type == str:
        return ""
    if expected_type == list:
        return []
    if expected_type == dict:
        return {}
    return ""


async def _reset_status_interval(value):
    """Reset STATUS_UPDATE_INTERVAL and restart interval timers."""
    if len(task_dict) != 0 and (st := intervals["status"]):
        for status_key, intvl in list(st.items()):
            intvl.cancel()
            intervals["status"][status_key] = SetInterval(
                value, update_status_message, status_key
            )
    return value


async def _reset_torrent_timeout():
    """Reset TORRENT_TIMEOUT to 0."""
    await TorrentManager.change_aria2_option("bt-stop-timeout", "0")
    await database.update_aria2("bt-stop-timeout", "0")


async def _reset_base_url_port():
    """Reset BASE_URL_PORT to 80 and restart gunicorn."""
    value = 80
    if Config.BASE_URL:
        await (await create_subprocess_exec("pkill", "-9", "-f", "gunicorn")).wait()
        await create_subprocess_shell(
            f"gunicorn -k uvicorn.workers.UvicornWorker -w 1 web.wserver:app --bind 0.0.0.0:{value}"
        )
    return value


def _reset_excluded_extensions(_):
    excluded_extensions.clear()
    excluded_extensions.extend(["aria2", "!qB"])


def _reset_included_extensions(_):
    included_extensions.clear()


def _reset_gdrive_id(_):
    if drives_names and drives_names[0] == "Main":
        drives_names.pop(0)
        drives_ids.pop(0)
        index_urls.pop(0)


def _reset_index_url(_):
    if drives_names and drives_names[0] == "Main":
        index_urls[0] = ""


def _reset_authorized_chats(_):
    auth_chats.clear()


def _reset_sudo_users(_):
    sudo_users.clear()


async def _reset_base_url(_):
    await (await create_subprocess_exec("pkill", "-9", "-f", "gunicorn")).wait()


async def _reset_incomplete_task_notifier(_):
    await database.trunc_table("tasks")


async def _reset_jdownloader_credentials(_):
    await create_subprocess_exec("pkill", "-9", "-f", "java")


async def _reset_usenet_servers(_):
    for s in Config.USENET_SERVERS:
        await sabnzbd_client.delete_config("servers", s["name"])


SYNC_RESETVAR_HANDLERS = {
    "EXCLUDED_EXTENSIONS": _reset_excluded_extensions,
    "INCLUDED_EXTENSIONS": _reset_included_extensions,
    "GDRIVE_ID": _reset_gdrive_id,
    "INDEX_URL": _reset_index_url,
    "AUTHORIZED_CHATS": _reset_authorized_chats,
    "SUDO_USERS": _reset_sudo_users,
}


ASYNC_RESETVAR_HANDLERS = {
    "TORRENT_TIMEOUT": _reset_torrent_timeout,
    "BASE_URL": _reset_base_url,
    "INCOMPLETE_TASK_NOTIFIER": _reset_incomplete_task_notifier,
    "JD_EMAIL": _reset_jdownloader_credentials,
    "JD_PASS": _reset_jdownloader_credentials,
    "USENET_SERVERS": _reset_usenet_servers,
}


async def _apply_resetvar_key_effects(key, value):
    """Apply reset logic for given key, return final reset value."""
    if key in DEFAULT_VALUES:
        value = DEFAULT_VALUES[key]
        if key == "STATUS_UPDATE_INTERVAL":
            value = await _reset_status_interval(value)
        return value

    if key == "BASE_URL_PORT":
        value = await _reset_base_url_port()

    sync_handler = SYNC_RESETVAR_HANDLERS.get(key)
    if sync_handler is not None:
        sync_handler(value)

    async_handler = ASYNC_RESETVAR_HANDLERS.get(key)
    if async_handler is not None:
        await async_handler(value)
    
    return value


async def _run_resetvar_post_hooks(key):
    if key in ["SEARCH_PLUGINS", "SEARCH_API_LINK"]:
        await initiate_search_tools()
    elif key in ["QUEUE_ALL", "QUEUE_DOWNLOAD", "QUEUE_UPLOAD"]:
        await start_from_queued()
    elif key in [
        "RCLONE_SERVE_URL",
        "RCLONE_SERVE_PORT",
        "RCLONE_SERVE_USER",
        "RCLONE_SERVE_PASS",
    ]:
        await rclone_serve_booter()


async def _handle_resetvar_action(query, message, key):
    await query.answer()
    value = _get_resetvar_default_value(key)
    value = await _apply_resetvar_key_effects(key, value)

    Config.set(key, value)
    await update_buttons(message, "var")
    if key == "DATABASE_URL":
        await database.disconnect()
    await database.update_config({key: value})
    await _run_resetvar_post_hooks(key)


async def _handle_botvar_action(client, query, message, data):
    """Handle bot variable edit/view."""
    if state == "edit":
        await query.answer()
        await update_buttons(message, data[2], data[1])
        pfunc = partial(edit_variable, pre_message=message, key=data[2])
        rfunc = partial(update_buttons, message, "var")
        await event_handler(client, query, pfunc, rfunc)
        return True
    if state == "view":
        return await _answer_value_or_send_file(
            query, message, data[2], f"{Config.get(data[2])}"
        )


async def _handle_ariavar_action(client, query, message, data):
    """Handle Aria2c option edit/view."""
    if state == "edit" or data[2] == "newkey":
        await query.answer()
        await update_buttons(message, data[2], data[1])
        pfunc = partial(edit_aria, pre_message=message, key=data[2])
        rfunc = partial(update_buttons, message, "aria")
        await event_handler(client, query, pfunc, rfunc)
        return True
    if state == "view":
        return await _answer_value_or_send_file(
            query, message, data[2], f"{aria2_options[data[2]]}"
        )


async def _handle_qbitvar_action(client, query, message, data):
    """Handle qBittorrent option edit/view."""
    if state == "edit":
        await query.answer()
        await update_buttons(message, data[2], data[1])
        pfunc = partial(edit_qbit, pre_message=message, key=data[2])
        rfunc = partial(update_buttons, message, "qbit")
        await event_handler(client, query, pfunc, rfunc)
        return True
    if state == "view":
        return await _answer_value_or_send_file(
            query, message, data[2], f"{qbit_options[data[2]]}"
        )


async def _handle_nzbvar_action(client, query, message, data):
    """Handle SABnzbd option edit/view."""
    if state == "edit":
        await query.answer()
        await update_buttons(message, data[2], data[1])
        pfunc = partial(edit_nzb, pre_message=message, key=data[2])
        rfunc = partial(update_buttons, message, "nzb")
        await event_handler(client, query, pfunc, rfunc)
        return True
    if state == "view":
        return await _answer_value_or_send_file(
            query, message, data[2], f"{nzb_options[data[2]]}"
        )


async def _handle_nzbsevar_action(client, query, message, data):
    """Handle Usenet server option edit/view."""
    action = data[1]
    if state == "edit" or data[2] == "newser":
        index = 0 if data[2] == "newser" else int(action.replace("nzbsevar", ""))
        await query.answer()
        await update_buttons(message, data[2], action)
        pfunc = partial(edit_nzb_server, pre_message=message, key=data[2], index=index)
        rfunc = partial(
            update_buttons,
            message,
            f"nzbser{index}" if data[2] != "newser" else "nzbserver",
        )
        await event_handler(client, query, pfunc, rfunc)
        return True
    if state == "view":
        index = int(action.replace("nzbsevar", ""))
        value = f"{Config.USENET_SERVERS[index][data[2]]}"
        return await _answer_value_or_send_file(query, message, data[2], value)


async def _handle_config_value_actions(client, query, message, data):
    """Dispatch config value action to appropriate handler."""
    action = data[1]
    
    if action == "botvar":
        return await _handle_botvar_action(client, query, message, data)
    if action == "ariavar":
        return await _handle_ariavar_action(client, query, message, data)
    if action == "qbitvar":
        return await _handle_qbitvar_action(client, query, message, data)
    if action == "nzbvar":
        return await _handle_nzbvar_action(client, query, message, data)
    if action.startswith("nzbsevar"):
        return await _handle_nzbsevar_action(client, query, message, data)
    
    return False


async def _handle_resetnzb_action(query, message, key):
    """Reset SABnzbd config option to default."""
    await query.answer()
    res = await sabnzbd_client.set_config_default(key)
    nzb_options[key] = res["config"]["misc"][key]
    await update_buttons(message, "nzb")
    await database.update_nzb_config()


async def _handle_syncnzb_action(query):
    """Sync SABnzbd configuration."""
    await query.answer("Synchronization Started. It takes up to 2 sec!", show_alert=True)
    nzb_options.clear()
    await update_nzb_options()
    await database.update_nzb_config()


async def _handle_syncqbit_action(query):
    """Sync qBittorrent configuration."""
    await query.answer("Synchronization Started. It takes up to 2 sec!", show_alert=True)
    qbit_options.clear()
    await update_qb_options()
    await database.save_qbit_settings()


async def _handle_emptyaria_action(query, message, key):
    """Clear Aria2c option value."""
    await query.answer()
    aria2_options[key] = ""
    await update_buttons(message, "aria")
    await TorrentManager.change_aria2_option(key, "")
    await database.update_aria2(key, "")


async def _handle_emptyqbit_action(query, message, key):
    """Clear qBittorrent option value."""
    await query.answer()
    await TorrentManager.qbittorrent.app.set_preferences({key: ""})
    qbit_options[key] = ""
    await update_buttons(message, "qbit")
    await database.update_qbittorrent(key, "")


async def _handle_emptynzb_action(query, message, key):
    """Clear SABnzbd option value."""
    await query.answer()
    res = await sabnzbd_client.set_config("misc", key, "")
    nzb_options[key] = res["config"]["misc"][key]
    await update_buttons(message, "nzb")
    await database.update_nzb_config()


async def _handle_remser_action(query, message, index):
    """Remove Usenet server."""
    await sabnzbd_client.delete_config("servers", Config.USENET_SERVERS[index]["name"])
    del Config.USENET_SERVERS[index]
    await update_buttons(message, "nzbserver")
    await database.update_config({"USENET_SERVERS": Config.USENET_SERVERS})


async def _handle_private_action(client, query, message):
    """Handle private file upload."""
    await query.answer()
    await update_buttons(message, "private")
    pfunc = partial(update_private_file, pre_message=message)
    rfunc = partial(update_buttons, message)
    await event_handler(client, query, pfunc, rfunc, True)


async def _handle_emptyserkey_action(query, message, index, key):
    """Clear Usenet server key value."""
    await query.answer()
    await update_buttons(message, f"nzbser{index}")
    res = await sabnzbd_client.add_server(
        {"name": Config.USENET_SERVERS[index]["name"], key: ""}
    )
    Config.USENET_SERVERS[index][key] = res["config"]["servers"][0][key]
    await database.update_config({"USENET_SERVERS": Config.USENET_SERVERS})


async def _handle_state_action(query, message, new_state, key):
    """Switch between edit and view states."""
    await query.answer()
    globals()[f"state"] = new_state
    await update_buttons(message, key)


async def _handle_pagination_action(query, message, key, page_num):
    """Handle pagination in list views."""
    await query.answer()
    if start != page_num:
        globals()["start"] = page_num
        await update_buttons(message, key)


async def _handle_push_action(query, message, filename):
    """Push file changes to upstream git repo."""
    await query.answer()
    filename = filename.rsplit(".zip", 1)[0]
    if await aiopath.exists(filename):
        await (
            await create_subprocess_shell(
                f"git add -f {filename} \
                && git commit -sm botsettings -q \
                && git push origin {Config.UPSTREAM_BRANCH} -qf"
            )
        ).wait()
    else:
        await (
            await create_subprocess_shell(
                f"git rm -r --cached {filename} \
                && git commit -sm botsettings -q \
                && git push origin {Config.UPSTREAM_BRANCH} -qf"
            )
        ).wait()
    await delete_message(message.reply_to_message)
    await delete_message(message)


async def _handle_misc_bot_settings_action(client, query, message, data):
    """Dispatch misc bot settings actions to appropriate handlers."""
    action = data[1]

    handlers = {
        "resetnzb": lambda: _handle_resetnzb_action(query, message, data[2]),
        "syncnzb": lambda: _handle_syncnzb_action(query),
        "syncqbit": lambda: _handle_syncqbit_action(query),
        "emptyaria": lambda: _handle_emptyaria_action(query, message, data[2]),
        "emptyqbit": lambda: _handle_emptyqbit_action(query, message, data[2]),
        "emptynzb": lambda: _handle_emptynzb_action(query, message, data[2]),
        "remser": lambda: _handle_remser_action(query, message, int(data[2])),
        "private": lambda: _handle_private_action(client, query, message),
        "emptyserkey": lambda: _handle_emptyserkey_action(
            query, message, int(data[2]), data[3]
        ),
        "edit": lambda: _handle_state_action(query, message, "edit", data[2]),
        "view": lambda: _handle_state_action(query, message, "view", data[2]),
        "start": lambda: _handle_pagination_action(
            query, message, data[2], int(data[3])
        ),
        "push": lambda: _handle_push_action(query, message, data[2]),
    }

    handler = handlers.get(action)
    if handler is None:
        return False

    await handler()
    return True


async def _handle_close_or_back_action(query, message, action):
    if action == "close":
        await query.answer()
        await delete_message(message.reply_to_message)
        await delete_message(message)
        return True

    if action == "back":
        await query.answer()
        globals()["start"] = 0
        await update_buttons(message, None)
        return True

    return False


async def _handle_syncjd_action(query, action):
    if action != "syncjd":
        return False

    if not Config.JD_EMAIL or not Config.JD_PASS:
        await query.answer(
            "No Email or Password provided!",
            show_alert=True,
        )
        return True

    await query.answer(
        "Synchronization Started. JDownloader will get restarted. It takes up to 10 sec!",
        show_alert=True,
    )
    await sync_jdownloader()
    return True


async def _handle_section_navigation_action(query, message, action):
    if action not in ["var", "aria", "qbit", "nzb", "nzbserver"] and not action.startswith(
        "nzbser"
    ):
        return False

    if action == "nzbserver":
        globals()["start"] = 0

    await query.answer()
    await update_buttons(message, action)
    return True


@new_task
async def edit_bot_settings(client, query):
    data = query.data.split()
    message = query.message
    action = data[1]
    handler_dict[message.chat.id] = False

    if await _handle_close_or_back_action(query, message, action):
        return

    if await _handle_syncjd_action(query, action):
        return

    if await _handle_section_navigation_action(query, message, action):
        return

    if action == "resetvar":
        await _handle_resetvar_action(query, message, data[2])
        return

    if await _handle_misc_bot_settings_action(client, query, message, data):
        return

    await _handle_config_value_actions(client, query, message, data)


@new_task
async def send_bot_settings(_, message):
    handler_dict[message.chat.id] = False
    msg, button = await get_buttons()
    globals()["start"] = 0
    await send_message(message, msg, button)


async def load_config():
    Config.load()
    drives_ids.clear()
    drives_names.clear()
    index_urls.clear()
    await update_variables()

    if not await aiopath.exists("accounts"):
        Config.USE_SERVICE_ACCOUNTS = False

    if len(task_dict) != 0 and (st := intervals["status"]):
        for key, intvl in list(st.items()):
            intvl.cancel()
            intervals["status"][key] = SetInterval(
                Config.STATUS_UPDATE_INTERVAL, update_status_message, key
            )

    if Config.TORRENT_TIMEOUT:
        await TorrentManager.change_aria2_option(
            "bt-stop-timeout", f"{Config.TORRENT_TIMEOUT}"
        )
        await database.update_aria2("bt-stop-timeout", f"{Config.TORRENT_TIMEOUT}")

    if not Config.INCOMPLETE_TASK_NOTIFIER:
        await database.trunc_table("tasks")

    await (await create_subprocess_exec("pkill", "-9", "-f", "gunicorn")).wait()
    if Config.BASE_URL:
        await create_subprocess_shell(
            f"gunicorn -k uvicorn.workers.UvicornWorker -w 1 web.wserver:app --bind 0.0.0.0:{Config.BASE_URL_PORT}"
        )

    if Config.DATABASE_URL:
        await database.connect()
        config_dict = Config.get_all()
        await database.update_config(config_dict)
    else:
        await database.disconnect()
    await gather(initiate_search_tools(), start_from_queued(), rclone_serve_booter())
    add_job()
