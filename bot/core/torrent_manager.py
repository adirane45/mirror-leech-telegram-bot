from aioaria2 import Aria2WebsocketClient
from aioqbt.client import create_client
from asyncio import gather, TimeoutError
from aiohttp import ClientError
from pathlib import Path
from inspect import iscoroutinefunction
from os import environ
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .. import LOGGER, aria2_options


def wrap_with_retry(obj, max_retries=3):
    for attr_name in dir(obj):
        if attr_name.startswith("_"):
            continue

        attr = getattr(obj, attr_name)
        if iscoroutinefunction(attr):
            retry_policy = retry(
                stop=stop_after_attempt(max_retries),
                wait=wait_exponential(multiplier=1, min=1, max=5),
                retry=retry_if_exception_type(
                    (ClientError, TimeoutError, RuntimeError)
                ),
            )
            wrapped = retry_policy(attr)
            setattr(obj, attr_name, wrapped)
    return obj


class TorrentManager:
    aria2 = None
    qbittorrent = None

    @classmethod
    async def initiate(cls):
        aria2_host = environ.get("ARIA2_HOST", "localhost")
        aria2_port = environ.get("ARIA2_PORT", "6800")
        aria2_secret = environ.get("ARIA2_SECRET", "")
        qb_host = environ.get("QB_HOST", "localhost")
        qb_port = environ.get("QB_PORT", "8090")
        
        # Try different authentication methods for qBittorrent
        qb_url = f"http://{qb_host}:{qb_port}/api/v2/"
        qb_client = None
        
        # Try with password first
        try:
            qb_client = await create_client(
                qb_url,
                username="admin",
                password="mltbmltb",
            )
        except Exception as e:
            LOGGER.warning(f"qBittorrent auth with password failed: {e}, trying without password...")
            try:
                # Try with empty password
                qb_client = await create_client(
                    qb_url,
                    username="admin",
                    password="",
                )
            except Exception as e2:
                LOGGER.warning(f"qBittorrent auth without password failed: {e2}, trying unauthenticated...")
                try:
                    # Try unauthenticated
                    qb_client = await create_client(qb_url)
                except Exception as e3:
                    LOGGER.error(f"All qBittorrent authentication methods failed: {e3}")
                    raise
        
        # Connect to aria2 with secret if provided
        if aria2_secret:
            cls.aria2 = await Aria2WebsocketClient.new(
                f"http://{aria2_host}:{aria2_port}/jsonrpc",
                token=aria2_secret
            )
        else:
            cls.aria2 = await Aria2WebsocketClient.new(f"http://{aria2_host}:{aria2_port}/jsonrpc")
        cls.qbittorrent = qb_client
        cls.qbittorrent = wrap_with_retry(cls.qbittorrent)

    @classmethod
    async def close_all(cls):
        await gather(cls.aria2.close(), cls.qbittorrent.close())

    @classmethod
    async def aria2_remove(cls, download):
        if download.get("status", "") in ["active", "paused", "waiting"]:
            await cls.aria2.forceRemove(download.get("gid", ""))
        else:
            try:
                await cls.aria2.removeDownloadResult(download.get("gid", ""))
            except:
                pass

    @classmethod
    async def remove_all(cls):
        await cls.pause_all()
        await gather(
            cls.qbittorrent.torrents.delete("all", False),
            cls.aria2.purgeDownloadResult(),
        )
        downloads = []
        results = await gather(cls.aria2.tellActive(), cls.aria2.tellWaiting(0, 1000))
        for res in results:
            downloads.extend(res)
        tasks = []
        tasks.extend(
            cls.aria2.forceRemove(download.get("gid")) for download in downloads
        )
        try:
            await gather(*tasks)
        except:
            pass

    @classmethod
    async def overall_speed(cls):
        s1, s2 = await gather(
            cls.qbittorrent.transfer.info(), cls.aria2.getGlobalStat()
        )
        download_speed = s1.dl_info_speed + int(s2.get("downloadSpeed", "0"))
        upload_speed = s1.up_info_speed + int(s2.get("uploadSpeed", "0"))
        return download_speed, upload_speed

    @classmethod
    async def pause_all(cls):
        await gather(cls.aria2.forcePauseAll(), cls.qbittorrent.torrents.stop("all"))

    @classmethod
    async def change_aria2_option(cls, key, value):
        downloads = []
        results = await gather(cls.aria2.tellActive(), cls.aria2.tellWaiting(0, 1000))
        for res in results:
            downloads.extend(res)
            tasks = []
        for download in downloads:
            if download.get("status", "") != "complete":
                tasks.append(cls.aria2.changeOption(download.get("gid"), {key: value}))
        if tasks:
            try:
                await gather(*tasks)
            except Exception as e:
                LOGGER.error(e)
        if key not in ["checksum", "index-out", "out", "pause", "select-file"]:
            await cls.aria2.changeGlobalOption({key: value})
            aria2_options[key] = value


def aria2_name(download_info):
    if "bittorrent" in download_info and download_info["bittorrent"].get("info"):
        return download_info["bittorrent"]["info"]["name"]
    elif download_info.get("files"):
        if download_info["files"][0]["path"].startswith("[METADATA]"):
            return download_info["files"][0]["path"]
        file_path = download_info["files"][0]["path"]
        dir_path = download_info["dir"]
        if file_path.startswith(dir_path):
            return Path(file_path[len(dir_path) + 1 :]).parts[0]
        else:
            return ""
    else:
        return ""


def is_metadata(download_info):
    return any(
        f["path"].startswith("[METADATA]") for f in download_info.get("files", [])
    )
