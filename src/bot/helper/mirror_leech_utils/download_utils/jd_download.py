from asyncio import Event, sleep, wait_for
from base64 import b64encode
from functools import partial
from secrets import token_urlsafe
from time import time

from aiofiles import open as aiopen
from aiofiles.os import path as aiopath
from aiofiles.os import remove
from pyrogram.filters import regex, user
from pyrogram.handlers import CallbackQueryHandler

from integrations.myjd.exception import MYJDException

from .... import LOGGER, jd_downloads, jd_listener_lock, task_dict, task_dict_lock
from ....core.config_manager import Config
from ....core.jdownloader_booter import jdownloader
from ...ext_utils.bot_utils import new_task
from ...ext_utils.task_manager import check_running_tasks, stop_duplicate_check
from ...listeners.jdownloader_listener import on_download_start
from ...mirror_leech_utils.status_utils.jdownloader_status import JDownloaderStatus
from ...mirror_leech_utils.status_utils.queue_status import QueueStatus
from ...telegram_helper.button_build import ButtonMaker
from ...telegram_helper.message_utils import delete_message, edit_message, send_message, send_status_message


@new_task
async def configureDownload(_, query, obj):
    data = query.data.split()
    message = query.message
    await query.answer()
    if data[1] == "sdone":
        obj.event.set()
    elif data[1] == "cancel":
        await edit_message(message, "Task has been cancelled.")
        obj.listener.is_cancelled = True
        obj.event.set()


class JDownloaderHelper:
    def __init__(self, listener):
        self._timeout = 600
        self._reply_to = ""
        self.listener = listener
        self.event = Event()

    async def _event_handler(self):
        pfunc = partial(configureDownload, obj=self)
        handler = self.listener.client.add_handler(
            CallbackQueryHandler(
                pfunc, filters=regex("^jdq") & user(self.listener.user_id)
            ),
            group=-1,
        )
        try:
            await wait_for(self.event.wait(), timeout=self._timeout)
        except TimeoutError:
            await edit_message(self._reply_to, "Timed Out. Task has been cancelled!")
            self.listener.is_cancelled = True
            self.event.set()
        except Exception as e:
            LOGGER.error(f"JDownloader configuration error: {e}")
            self.listener.is_cancelled = True
            self.event.set()
        finally:
            self.listener.client.remove_handler(*handler)

    async def wait_for_configurations(self):
        buttons = ButtonMaker()
        buttons.url_button("Select", "https://my.jdownloader.org")
        buttons.data_button("Done Selecting", "jdq sdone")
        buttons.data_button("Cancel", "jdq cancel")
        button = buttons.build_menu(2)
        msg = f"Remove the unwanted files or change variants or edit files names from myJdownloader site for <b>{self.listener.name}</b>.\nDon't start it manually!\n\nAfter finish press Done Selecting!\nTimeout: 10 min"
        self._reply_to = await send_message(self.listener.message, msg, button)
        await self._event_handler()
        if not self.listener.is_cancelled:
            await delete_message(self._reply_to)
        return not self.listener.is_cancelled


async def get_online_packages(path, state="grabbing"):
    if state == "grabbing":
        queued_downloads = await jdownloader.device.linkgrabber.query_packages(
            [{"saveTo": True}]
        )
        return [qd["uuid"] for qd in queued_downloads if qd["saveTo"].startswith(path)]
    else:
        download_packages = await jdownloader.device.downloads.query_packages(
            [{"saveTo": True}]
        )
        return [dl["uuid"] for dl in download_packages if dl["saveTo"].startswith(path)]


def trim_path(path):
    path_components = path.split("/")

    trimmed_components = [
        component[:255] if len(component) > 255 else component
        for component in path_components
    ]

    return "/".join(trimmed_components)


async def get_jd_download_directory():
    res = await jdownloader.device.config.get(
        "org.jdownloader.settings.GeneralSettings", None, "DefaultDownloadFolder"
    )
    return f'/{res.strip("/")}/'


async def _ensure_jd_connected():
    if not jdownloader.is_connected:
        if getattr(Config, "JD_EMAIL", "") and getattr(Config, "JD_PASS", ""):
            await jdownloader.boot()
        if not jdownloader.is_connected:
            raise MYJDException(jdownloader.error)


async def _cleanup_existing_jd_lists(default_path):
    if not jd_downloads:
        await jdownloader.device.linkgrabber.clear_list()
        if odl := await jdownloader.device.downloads.query_packages([{}]):
            odl_list = [od["uuid"] for od in odl]
            await jdownloader.device.downloads.remove_links(package_ids=odl_list)
    elif odl := await jdownloader.device.linkgrabber.query_packages([{}]):
        if odl_list := [
            od["uuid"] for od in odl if od.get("saveTo", "").startswith(default_path)
        ]:
            await jdownloader.device.linkgrabber.remove_links(package_ids=odl_list)


async def _add_listener_link_to_jd(listener):
    if await aiopath.exists(listener.link):
        async with aiopen(listener.link, "rb") as dlc:
            content = await dlc.read()
        content = b64encode(content)
        await jdownloader.device.linkgrabber.add_container(
            "DLC", f"data:;base64,{content.decode()}"
        )
    else:
        await jdownloader.device.linkgrabber.add_links(
            [
                {
                    "autoExtract": False,
                    "links": listener.link,
                    "deepDecrypt": True,
                    "overwritePackagizerRules": listener.join,
                }
            ],
        )


async def _wait_for_jd_package_collection(listener):
    await sleep(1)
    LOGGER.info(f"JDownloader Collecting Data: {listener.link}")
    while await jdownloader.device.linkgrabber.is_collecting():
        await sleep(0.5)
    LOGGER.info(f"JDownloader Finished Collecting Data: {listener.link}")


def _initialize_jd_collection_state():
    return {
        "start_time": time(),
        "online_packages": [],
        "corrupted_packages": [],
        "remove_unknown": False,
        "name": "",
        "error": "",
    }


async def _query_jd_linkgrabber_packages():
    return await jdownloader.device.linkgrabber.query_packages(
        [
            {
                "bytesTotal": True,
                "saveTo": True,
                "availableOnlineCount": True,
                "availableOfflineCount": True,
                "availableTempUnknownCount": True,
                "availableUnknownCount": True,
            }
        ],
    )


async def _raise_if_corrupted_without_online(state):
    if not state["online_packages"] and state["corrupted_packages"] and state["error"]:
        await jdownloader.device.linkgrabber.remove_links(
            package_ids=state["corrupted_packages"],
        )
        raise MYJDException(state["error"])


async def _process_jd_queued_packages(queued_downloads, listener, path, default_path, state):
    for pack in queued_downloads:
        pack_result = await _process_package(pack, listener, path, default_path)
        if pack_result:
            state["online_packages"].append(pack_result["uuid"])
            if not state["name"]:
                state["name"] = pack_result["name"]
            state["remove_unknown"] = state["remove_unknown"] or pack_result["has_unknown"]
            continue

        state["error"] = pack.get("name", "")
        LOGGER.error(state["error"])
        state["corrupted_packages"].append(pack["uuid"])


async def _handle_jd_collection_timeout(state):
    error = state["name"] or "Download Not Added! Maybe some issues in jdownloader or site!"
    if state["corrupted_packages"] or state["online_packages"]:
        packages_to_remove = state["corrupted_packages"] + state["online_packages"]
        await jdownloader.device.linkgrabber.remove_links(package_ids=packages_to_remove)
    raise MYJDException(error)


async def _collect_jd_packages(listener, path, default_path):
    await _wait_for_jd_package_collection(listener)
    state = _initialize_jd_collection_state()

    while (time() - state["start_time"]) < 90:
        queued_downloads = await _query_jd_linkgrabber_packages()
        await _raise_if_corrupted_without_online(state)
        await _process_jd_queued_packages(
            queued_downloads,
            listener,
            path,
            default_path,
            state,
        )

        if state["online_packages"]:
            return (
                state["online_packages"],
                state["corrupted_packages"],
                state["remove_unknown"],
                state["name"],
            )

    await _handle_jd_collection_timeout(state)


async def _process_package(pack, listener, path, default_path):
    if pack.get("onlineCount", 1) == 0:
        return None
    
    has_unknown = (
        pack.get("tempUnknownCount", 0) > 0
        or pack.get("unknownCount", 0) > 0
        or pack.get("offlineCount", 0) > 0
    )
    
    listener.size += pack.get("bytesTotal", 0)
    name = pack.get("name", "").replace("/", "").split("/")[0]
    
    save_to = pack["saveTo"]
    if save_to.startswith(default_path):
        save_to = trim_path(save_to)
        await jdownloader.device.linkgrabber.set_download_directory(
            save_to.replace(default_path, f"{path}/", 1),
            [pack["uuid"]],
        )
    
    return {"uuid": pack["uuid"], "name": name, "has_unknown": has_unknown}


async def _remove_corrupted_jd_links(online_packages, corrupted_packages, remove_unknown):
    corrupted_links = []
    if remove_unknown:
        links = await jdownloader.device.linkgrabber.query_links(
            [{"packageUUIDs": online_packages, "availability": True}],
        )
        corrupted_links = [
            link["uuid"] for link in links if link["availability"].lower() != "online"
        ]
    if corrupted_packages or corrupted_links:
        await jdownloader.device.linkgrabber.remove_links(
            corrupted_links,
            corrupted_packages,
        )


async def _handle_duplicate_for_jd(listener, gid, online_packages):
    msg, button = await stop_duplicate_check(listener)
    if not msg:
        return True
    await jdownloader.device.linkgrabber.remove_links(package_ids=online_packages)
    await listener.on_download_error(msg, button)
    async with jd_listener_lock:
        del jd_downloads[gid]
    return False


async def _handle_jd_selection(listener, path, gid, online_packages):
    if not listener.select:
        return online_packages
    if not await JDownloaderHelper(listener).wait_for_configurations():
        await jdownloader.device.linkgrabber.remove_links(package_ids=online_packages)
        await listener.remove_from_same_dir()
        async with jd_listener_lock:
            del jd_downloads[gid]
        return None

    online_packages = await get_online_packages(path)
    if not online_packages:
        raise MYJDException("Select: This Download have been removed manually!")
    async with jd_listener_lock:
        jd_downloads[gid]["ids"] = online_packages
    return online_packages


async def _wait_download_queue_if_needed(listener, gid, path):
    add_to_queue, event = await check_running_tasks(listener)
    if not add_to_queue:
        return add_to_queue

    LOGGER.info(f"Added to Queue/Download: {listener.name}")
    async with task_dict_lock:
        task_dict[listener.mid] = QueueStatus(listener, gid, "dl")
    await listener.on_download_start()
    if listener.multi <= 1:
        await send_status_message(listener.message)
    await event.wait()
    if listener.is_cancelled:
        return add_to_queue

    online_packages = await get_online_packages(path)
    if not online_packages:
        raise MYJDException("Queue: This Download have been removed manually!")
    async with jd_listener_lock:
        jd_downloads[gid]["ids"] = online_packages
    return add_to_queue


async def _move_packages_to_download_list(path, online_packages):
    await jdownloader.device.linkgrabber.move_to_downloadlist(package_ids=online_packages)
    await sleep(0.5)

    moved_packages = await get_online_packages(path, "down")
    if moved_packages:
        return moved_packages

    moved_packages = await get_online_packages(path)
    if not moved_packages:
        raise MYJDException("Linkgrabber: This Download have been removed manually!")

    await jdownloader.device.linkgrabber.move_to_downloadlist(package_ids=moved_packages)
    await sleep(0.5)
    moved_packages = await get_online_packages(path, "down")
    if not moved_packages:
        raise MYJDException("Download List: This Download have been removed manually!")
    return moved_packages


async def _finalize_jd_download(listener, gid, online_packages, add_to_queue):
    async with jd_listener_lock:
        jd_downloads[gid]["status"] = "down"
        jd_downloads[gid]["ids"] = online_packages

    await jdownloader.device.downloads.force_download(package_ids=online_packages)

    async with task_dict_lock:
        task_dict[listener.mid] = JDownloaderStatus(listener, gid)

    await on_download_start()

    if add_to_queue:
        LOGGER.info(f"Start Queued Download from JDownloader: {listener.name}")
    else:
        LOGGER.info(f"Download with JDownloader: {listener.name}")
        await listener.on_download_start()
        if listener.multi <= 1:
            await send_status_message(listener.message)


async def _fix_invalid_download_links(online_packages):
    await sleep(2)
    links = await jdownloader.device.downloads.query_links(
        [{"packageUUIDs": online_packages, "status": True}],
    )
    links_to_remove = []
    force_download = False
    for dlink in links:
        if dlink.get("status", "") == "Invalid download directory":
            force_download = True
            new_name, ext = dlink["name"].rsplit(".", 1)
            new_name = new_name[: 250 - len(f".{ext}".encode())]
            new_name = f"{new_name}.{ext}"
            await jdownloader.device.downloads.rename_link(dlink["uuid"], new_name)
        elif dlink.get("status", "") == "HLS stream broken?":
            links_to_remove.append(dlink["uuid"])

    if links_to_remove:
        await jdownloader.device.downloads.remove_links(links_to_remove)
    if force_download:
        await jdownloader.device.downloads.force_download(package_ids=online_packages)


async def _prepare_jd_packages(listener, path, gid):
    async with jd_listener_lock:
        await _ensure_jd_connected()

        default_path = await get_jd_download_directory()
        await _cleanup_existing_jd_lists(default_path)

        jd_downloads[gid] = {"status": "collect", "path": path}

        await _add_listener_link_to_jd(listener)
        online_packages, corrupted_packages, remove_unknown, name = (
            await _collect_jd_packages(listener, path, default_path)
        )

        jd_downloads[gid]["ids"] = online_packages
        await _remove_corrupted_jd_links(
            online_packages,
            corrupted_packages,
            remove_unknown,
        )

    return online_packages, name


async def _run_jd_download_flow(listener, path, gid, online_packages):
    if not await _handle_duplicate_for_jd(listener, gid, online_packages):
        return None

    online_packages = await _handle_jd_selection(listener, path, gid, online_packages)
    if online_packages is None:
        return None

    add_to_queue = await _wait_download_queue_if_needed(listener, gid, path)
    if listener.is_cancelled:
        return None

    online_packages = await _move_packages_to_download_list(path, online_packages)
    await _finalize_jd_download(listener, gid, online_packages, add_to_queue)
    return online_packages


async def _cleanup_jd_add_failure(listener, gid, error):
    await listener.on_download_error(f"{error}".strip())
    async with jd_listener_lock:
        if gid in jd_downloads:
            del jd_downloads[gid]


async def add_jd_download(listener, path):
    gid = token_urlsafe(12)
    online_packages = []
    try:
        online_packages, name = await _prepare_jd_packages(listener, path, gid)

        listener.name = listener.name or name
        online_packages = await _run_jd_download_flow(listener, path, gid, online_packages)
        if online_packages is None:
            return
    except (Exception, MYJDException) as e:
        await _cleanup_jd_add_failure(listener, gid, e)
        return
    finally:
        if await aiopath.exists(listener.link):
            await remove(listener.link)
    if online_packages:
        await _fix_invalid_download_links(online_packages)
