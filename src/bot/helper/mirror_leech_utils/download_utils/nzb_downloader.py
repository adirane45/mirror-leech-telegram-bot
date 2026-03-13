from asyncio import gather, sleep

from aiofiles.os import path as aiopath
from aiofiles.os import remove

from integrations.sabnzbdapi.exception import LoginFailed, NotLoggedIn

from .... import LOGGER, sabnzbd_client, task_dict, task_dict_lock
from ....core.config_manager import Config
from ...ext_utils.bot_utils import bt_selection_buttons
from ...ext_utils.db_handler import database
from ...ext_utils.task_manager import check_running_tasks
from ...listeners.nzb_listener import on_download_start
from ...mirror_leech_utils.status_utils.nzb_status import SabnzbdStatus
from ...telegram_helper.message_utils import delete_message, send_message, send_status_message


async def _ensure_server_login(listener):
    if not sabnzbd_client.LOGGED_IN:
        try:
            await add_servers()
        except Exception as e:
            await listener.on_download_error(str(e))
            return False
    return True


async def _submit_nzb_job(listener, path, add_to_queue):
    await sabnzbd_client.create_category(f"{listener.mid}", path)
    url = listener.link
    nzbpath = None
    if await aiopath.exists(listener.link):
        url = None
        nzbpath = listener.link
    res = await sabnzbd_client.add_uri(
        url,
        nzbpath,
        listener.name,
        listener.extract if isinstance(listener.extract, str) else "",
        f"{listener.mid}",
        priority=-2 if add_to_queue else 0,
        pp=3 if listener.extract else 1,
    )
    if not res["status"]:
        await listener.on_download_error(
            "Not added! Mostly issue in the link",
        )
        return None, None
    return res["nzo_ids"][0], nzbpath


async def _get_download_name_from_queue(job_id):
    downloads = await sabnzbd_client.get_downloads(nzo_ids=job_id)
    if downloads["queue"]["slots"]:
        return downloads["queue"]["slots"][0]["filename"]
    return None


async def _get_download_name_from_history(job_id, listener):
    history = await sabnzbd_client.get_history(nzo_ids=job_id)
    if err := history["history"]["slots"][0]["fail_message"]:
        await gather(
            listener.on_download_error(err),
            sabnzbd_client.delete_history(job_id, delete_files=True),
        )
        return None
    return history["history"]["slots"][0]["name"]


async def _retrieve_download_name(job_id, listener):
    await sleep(0.5)
    name = await _get_download_name_from_queue(job_id)
    if name:
        return name
    await sleep(1)
    return await _get_download_name_from_history(job_id, listener)


async def _wait_for_nzb_fetch(job_id, listener):
    metamsg = "Fetching URL, wait then you can select files. Use nzb file to avoid this wait."
    meta = await send_message(listener.message, metamsg)
    while True:
        nzb_info = await sabnzbd_client.get_downloads(nzo_ids=job_id)
        if nzb_info["queue"]["slots"]:
            if not nzb_info["queue"]["slots"][0]["filename"].startswith("Trying"):
                await delete_message(meta)
                return True
        else:
            await delete_message(meta)
            return False
        await sleep(1)


async def _handle_file_selection(listener, job_id, name, url, add_to_queue):
    if not Config.BASE_URL or not listener.select:
        return
    if url and name.startswith("Trying"):
        if not await _wait_for_nzb_fetch(job_id, listener):
            return
    if not add_to_queue:
        await sabnzbd_client.pause_job(job_id)
    SBUTTONS = bt_selection_buttons(job_id)
    msg = "Your download paused. Choose files then press Done Selecting button to start downloading."
    await send_message(listener.message, msg, SBUTTONS)


async def _handle_queue_resume(listener, job_id, name, event, add_to_queue):
    if not add_to_queue:
        return
    await event.wait()
    if listener.is_cancelled:
        return
    async with task_dict_lock:
        task_dict[listener.mid].queued = False
    await sabnzbd_client.resume_job(job_id)
    LOGGER.info(f"Start Queued Download from Sabnzbd: {name} - Job_id: {job_id}")


async def add_servers():
    res = await sabnzbd_client.check_login()
    if res and (servers := res["servers"]):
        await _handle_existing_login(servers)
    elif _should_reject_login():
        sabnzbd_client.LOGGED_IN = False
        raise NotLoggedIn("Set USENET_SERVERS in bsetting or config!")
    else:
        await _handle_new_login()


async def _handle_existing_login(servers):
    sabnzbd_client.LOGGED_IN = True
    tasks = []
    servers_hosts = [x["host"] for x in servers]
    for server in list(Config.USENET_SERVERS):
        if server["host"] not in servers_hosts:
            tasks.append(sabnzbd_client.add_server(server))
            Config.USENET_SERVERS.append(server)
    if Config.DATABASE_URL:
        tasks.append(
            database.update_config({"USENET_SERVERS": Config.USENET_SERVERS})
        )
    if tasks:
        try:
            await gather(*tasks)
        except LoginFailed as e:
            raise e


def _should_reject_login():
    if not Config.USENET_SERVERS:
        return True
    first_server = Config.USENET_SERVERS[0]
    return not first_server["host"] or not first_server["username"] or not first_server["password"]


async def _handle_new_login():
    if tasks := [
        sabnzbd_client.add_server(server) for server in Config.USENET_SERVERS
    ]:
        try:
            await gather(*tasks)
            sabnzbd_client.LOGGED_IN = True
        except LoginFailed as e:
            if len(tasks) == 1:
                sabnzbd_client.LOGGED_IN = False
            raise e


async def _set_nzb_task_status(listener, job_id, add_to_queue):
    async with task_dict_lock:
        task_dict[listener.mid] = SabnzbdStatus(
            listener, job_id, queued=add_to_queue
        )
    await on_download_start(job_id)


def _log_nzb_start(name, job_id, add_to_queue):
    if add_to_queue:
        LOGGER.info(f"Added to Queue/Download: {name} - Job_id: {job_id}")
        return
    LOGGER.info(f"NzbDownload started: {name} - Job_id: {job_id}")


async def add_nzb(listener, path):
    if not await _ensure_server_login(listener):
        return

    nzbpath = None
    try:
        add_to_queue, event = await check_running_tasks(listener)
        job_id, nzbpath = await _submit_nzb_job(listener, path, add_to_queue)
        if job_id is None:
            return

        name = await _retrieve_download_name(job_id, listener)
        if name is None:
            return

        await _set_nzb_task_status(listener, job_id, add_to_queue)
        _log_nzb_start(name, job_id, add_to_queue)

        await listener.on_download_start()

        await _handle_file_selection(
            listener, job_id, name, listener.link, add_to_queue
        )

        if listener.multi <= 1 and not (Config.BASE_URL and listener.select):
            await send_status_message(listener.message)

        await _handle_queue_resume(listener, job_id, name, event, add_to_queue)

    except Exception as e:
        await listener.on_download_error(f"{e}")
    finally:
        if nzbpath and await aiopath.exists(listener.link):
            await remove(listener.link)
