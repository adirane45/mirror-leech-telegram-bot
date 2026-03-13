from asyncio import TimeoutError, sleep

from aiohttp.client_exceptions import ClientError

from ... import LOGGER
from ...core.torrent_manager import TorrentManager, aria2_name


class DirectListener:
    def __init__(self, path, listener, a2c_opt):
        self.listener = listener
        self._path = path
        self._a2c_opt = a2c_opt
        self._proc_bytes = 0
        self._failed = 0
        self.download_task = None
        self.name = self.listener.name

    @property
    def processed_bytes(self):
        if self.download_task:
            return self._proc_bytes + int(
                self.download_task.get("completedLength", "0")
            )
        return self._proc_bytes

    @property
    def speed(self):
        return (
            int(self.download_task.get("downloadSpeed", "0"))
            if self.download_task
            else 0
        )

    def _set_download_dir(self, content):
        if content["path"]:
            self._a2c_opt["dir"] = f"{self._path}/{content['path']}"
            return
        self._a2c_opt["dir"] = self._path

    async def _add_content_to_aria2(self, content):
        filename = content["filename"]
        self._a2c_opt["out"] = filename
        try:
            gid = await TorrentManager.aria2.addUri(
                uris=[content["url"]], options=self._a2c_opt, position=0
            )
            return gid
        except (TimeoutError, ClientError, Exception) as e:
            self._failed += 1
            LOGGER.error(f"Unable to download {filename} due to: {e}")
            return None

    async def _handle_cancelled_download(self):
        if not self.listener.is_cancelled:
            return False
        if self.download_task:
            await TorrentManager.aria2_remove(self.download_task)
        return True

    async def _poll_content_status(self, gid):
        self.download_task = await TorrentManager.aria2.tellStatus(gid)
        while True:
            if await self._handle_cancelled_download():
                return False

            self.download_task = await TorrentManager.aria2.tellStatus(gid)
            if error_message := self.download_task.get("errorMessage"):
                self._failed += 1
                LOGGER.error(
                    f"Unable to download {aria2_name(self.download_task)} due to: {error_message}"
                )
                await TorrentManager.aria2_remove(self.download_task)
                return False

            if self.download_task.get("status", "") == "complete":
                self._proc_bytes += int(self.download_task.get("totalLength", "0"))
                await TorrentManager.aria2_remove(self.download_task)
                return True

            await sleep(1)

    async def download(self, contents):
        self.is_downloading = True
        for content in contents:
            if self.listener.is_cancelled:
                break

            self._set_download_dir(content)
            gid = await self._add_content_to_aria2(content)
            if not gid:
                continue

            await self._poll_content_status(gid)
            self.download_task = None

        if self.listener.is_cancelled:
            return
        if self._failed == len(contents):
            await self.listener.on_download_error("All files are failed to download!")
            return
        await self.listener.on_download_complete()
        return

    async def cancel_task(self):
        self.listener.is_cancelled = True
        LOGGER.info(f"Cancelling Download: {self.listener.name}")
        await self.listener.on_download_error("Download Cancelled by User!")
        if self.download_task:
            await TorrentManager.aria2_remove(self.download_task)
