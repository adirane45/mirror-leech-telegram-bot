from asyncio import gather, sleep
from html import escape
from os import path as ospath

from aiofiles.os import listdir, makedirs
from aiofiles.os import path as aiopath
from aiofiles.os import remove
from requests import utils as rutils

from ... import (
    DOWNLOAD_DIR,
    LOGGER,
    intervals,
    non_queued_dl,
    non_queued_up,
    queue_dict_lock,
    queued_dl,
    queued_up,
    same_directory_lock,
    task_dict,
    task_dict_lock,
)
from ...core.config_manager import Config
from ...core.torrent_manager import TorrentManager
from ..common import TaskConfig
from ..ext_utils.bot_utils import sync_to_async
from ..ext_utils.db_handler import database
from ..ext_utils.files_utils import (
    clean_download,
    clean_target,
    create_recursive_symlink,
    get_path_size,
    join_files,
    move_and_merge,
    remove_excluded_files,
    remove_non_included_files,
)
from ..ext_utils.history_utils import add_history
from ..ext_utils.links_utils import is_gdrive_id
from ..ext_utils.status_utils import get_readable_file_size
from ..ext_utils.task_manager import check_running_tasks, start_from_queued
from ..mirror_leech_utils.gdrive_utils.upload import GoogleDriveUpload
from ..mirror_leech_utils.rclone_utils.transfer import RcloneTransferHelper
from ..mirror_leech_utils.status_utils.gdrive_status import GoogleDriveStatus
from ..mirror_leech_utils.status_utils.queue_status import QueueStatus
from ..mirror_leech_utils.status_utils.rclone_status import RcloneStatus
from ..mirror_leech_utils.status_utils.telegram_status import TelegramStatus
from ..mirror_leech_utils.telegram_uploader import TelegramUploader
from ..telegram_helper.button_build import ButtonMaker
from ..telegram_helper.message_utils import delete_status, send_message, update_status_message


class TaskListener(TaskConfig):
    def __init__(self):
        super().__init__()

    async def clean(self):
        try:
            if st := intervals["status"]:
                for intvl in list(st.values()):
                    intvl.cancel()
            intervals["status"].clear()
            await gather(TorrentManager.aria2.purgeDownloadResult(), delete_status())
        except:
            pass

    def clear(self):
        self.subname = ""
        self.subsize = 0
        self.files_to_proceed = []
        self.proceed_count = 0
        self.progress = True

    async def remove_from_same_dir(self):
        async with task_dict_lock:
            if (
                self.folder_name
                and self.same_dir
                and self.mid in self.same_dir[self.folder_name]["tasks"]
            ):
                self.same_dir[self.folder_name]["tasks"].remove(self.mid)
                self.same_dir[self.folder_name]["total"] -= 1

    async def on_download_start(self):
        if (
            self.is_super_chat
            and Config.INCOMPLETE_TASK_NOTIFIER
            and Config.DATABASE_URL
        ):
            await database.add_incomplete_task(
                self.message.chat.id, self.message.link, self.tag
            )

    async def _handle_same_dir_merge(self):
        multi_links = False
        if (
            self.folder_name
            and self.same_dir
            and self.mid in self.same_dir[self.folder_name]["tasks"]
        ):
            async with same_directory_lock:
                while True:
                    async with task_dict_lock:
                        if self.mid not in self.same_dir[self.folder_name]["tasks"]:
                            return multi_links, True
                        if (
                            self.same_dir[self.folder_name]["total"] <= 1
                            or len(self.same_dir[self.folder_name]["tasks"]) > 1
                        ):
                            if self.same_dir[self.folder_name]["total"] > 1:
                                self.same_dir[self.folder_name]["tasks"].remove(self.mid)
                                self.same_dir[self.folder_name]["total"] -= 1
                                spath = f"{self.dir}{self.folder_name}"
                                des_id = list(self.same_dir[self.folder_name]["tasks"])[0]
                                des_path = f"{DOWNLOAD_DIR}{des_id}{self.folder_name}"
                                LOGGER.info(f"Moving files from {self.mid} to {des_id}")
                                await move_and_merge(spath, des_path, self.mid)
                                multi_links = True
                            break
                    await sleep(1)
        return multi_links, False

    async def _resolve_download_meta(self):
        async with task_dict_lock:
            if self.is_cancelled:
                return None
            if self.mid not in task_dict:
                return None
            download = task_dict[self.mid]
            self.name = download.name()
            gid = download.gid()
        LOGGER.info(f"Download completed: {self.name}")
        return gid

    async def _recover_name_from_aria2(self, gid):
        try:
            a2status = await TorrentManager.aria2.tellStatus(gid)
            a2files = a2status.get("files", [])
            a2path = ""
            for file_info in a2files:
                if file_info.get("path"):
                    a2path = file_info["path"]
                    break
            if a2path and await aiopath.exists(a2path):
                self.dir = ospath.dirname(a2path)
                self.name = ospath.basename(a2path)
                return True
            await self.on_upload_error(
                f"No files found in download dir: {self.dir}"
            )
            return False
        except Exception:
            LOGGER.exception("Error fetching aria2 path")
            await self.on_upload_error(
                f"No files found in download dir: {self.dir}"
            )
            return False

    def _set_name_from_local_files(self, files):
        self.name = files[-1]
        if self.name == "yt-dlp-thumb":
            self.name = files[0]

    async def _ensure_task_dir_exists(self):
        if await aiopath.exists(self.dir):
            return
        LOGGER.warning(f"Task directory missing: {self.dir}, creating it now")
        await makedirs(self.dir, exist_ok=True)

    async def _recover_missing_name_from_dir(self, gid):
        if await aiopath.exists(f"{self.dir}/{self.name}"):
            return True
        try:
            await self._ensure_task_dir_exists()

            files = await listdir(self.dir)
            if not files:
                return await self._recover_name_from_aria2(gid)
            else:
                self._set_name_from_local_files(files)
            return True
        except Exception as e:
            LOGGER.exception("Error in file listing")
            await self.on_upload_error(str(e))
            return False

    async def _apply_include_exclude_filters(self):
        if not self.included_extensions:
            await remove_excluded_files(
                self.up_dir or self.dir, self.excluded_extensions
            )
        else:
            await remove_non_included_files(
                self.up_dir or self.dir, self.included_extensions
            )

    async def _update_path_state(self, up_path, up_dir, clear=False):
        self.is_file = await aiopath.isfile(up_path)
        self.name = up_path.replace(f"{up_dir}/", "").split("/", 1)[0]
        self.size = await get_path_size(up_dir)
        if clear:
            self.clear()

    async def _process_join_files(self, up_path):
        if self.join and not self.is_file:
            await join_files(up_path)
        return up_path

    async def _process_extract(self, up_path, up_dir, gid):
        if not self.extract or self.is_nzb:
            return up_path
        up_path = await self.proceed_extract(up_path, gid)
        if not self.is_cancelled:
            await self._update_path_state(up_path, up_dir, clear=True)
            await self._apply_include_exclude_filters()
        return up_path

    async def _process_ffmpeg(self, up_path, up_dir, gid):
        if not self.ffmpeg_cmds:
            return up_path
        up_path = await self.proceed_ffmpeg(up_path, gid)
        if not self.is_cancelled:
            await self._update_path_state(up_path, up_dir, clear=True)
        return up_path

    async def _process_name_substitution(self, up_path, up_dir):
        if not self.name_sub:
            return up_path
        LOGGER.info(f"Start Name Substitution {up_path}")
        up_path = await self.substitute(up_path)
        if not self.is_cancelled:
            self.is_file = await aiopath.isfile(up_path)
            self.name = up_path.replace(f"{up_dir}/", "").split("/", 1)[0]
        return up_path

    async def _process_screenshots(self, up_path, up_dir):
        if not self.screen_shots:
            return up_path
        up_path = await self.generate_screenshots(up_path)
        if not self.is_cancelled:
            await self._update_path_state(up_path, up_dir)
        return up_path

    async def _process_media_conversion(self, up_path, up_dir, gid):
        if not (self.convert_audio or self.convert_video):
            return up_path
        up_path = await self.convert_media(up_path, gid)
        if not self.is_cancelled:
            await self._update_path_state(up_path, up_dir, clear=True)
        return up_path

    async def _process_sample_video(self, up_path, up_dir, gid):
        if not self.sample_video:
            return up_path
        up_path = await self.generate_sample_video(up_path, gid)
        if not self.is_cancelled:
            await self._update_path_state(up_path, up_dir, clear=True)
        return up_path

    async def _process_compression(self, up_path, gid):
        if not self.compress:
            return up_path
        up_path = await self.proceed_compress(up_path, gid)
        self.is_file = await aiopath.isfile(up_path)
        if not self.is_cancelled:
            self.clear()
        return up_path

    async def _run_post_download_processing(self, up_path, up_dir, gid):
        up_path = await self._process_join_files(up_path)
        
        up_path = await self._process_extract(up_path, up_dir, gid)
        if self.is_cancelled:
            return None
        
        up_path = await self._process_ffmpeg(up_path, up_dir, gid)
        if self.is_cancelled:
            return None
        
        up_path = await self._process_name_substitution(up_path, up_dir)
        if self.is_cancelled:
            return None
        
        up_path = await self._process_screenshots(up_path, up_dir)
        if self.is_cancelled:
            return None
        
        up_path = await self._process_media_conversion(up_path, up_dir, gid)
        if self.is_cancelled:
            return None
        
        up_path = await self._process_sample_video(up_path, up_dir, gid)
        if self.is_cancelled:
            return None
        
        up_path = await self._process_compression(up_path, gid)
        if self.is_cancelled:
            return None
        
        return up_path

    async def _dispatch_upload(self, up_dir, up_path, gid):
        if self.is_leech:
            LOGGER.info(f"Leech Name: {self.name}")
            tg = TelegramUploader(self, up_dir)
            async with task_dict_lock:
                task_dict[self.mid] = TelegramStatus(self, tg, gid, "up")
            await gather(
                update_status_message(self.message.chat.id),
                tg.upload(),
            )
            del tg
        elif is_gdrive_id(self.up_dest):
            LOGGER.info(f"Gdrive Upload Name: {self.name}")
            drive = GoogleDriveUpload(self, up_path)
            async with task_dict_lock:
                task_dict[self.mid] = GoogleDriveStatus(self, drive, gid, "up")
            await gather(
                update_status_message(self.message.chat.id),
                sync_to_async(drive.upload),
            )
            del drive
        else:
            LOGGER.info(f"Rclone Upload Name: {self.name}")
            RCTransfer = RcloneTransferHelper(self)
            async with task_dict_lock:
                task_dict[self.mid] = RcloneStatus(self, RCTransfer, gid, "up")
            await gather(
                update_status_message(self.message.chat.id),
                RCTransfer.upload(up_path),
            )
            del RCTransfer

    @staticmethod
    def _build_base_complete_message(name, size):
        return (
            f"<b>Name: </b><code>{escape(name)}</code>\n\n"
            f"<b>Size: </b>{get_readable_file_size(size)}"
        )

    async def _send_leech_complete_messages(self, msg, files, total_files, corrupted):
        msg += f"\n<b>Total Files: </b>{total_files}"
        if corrupted != 0:
            msg += f"\n<b>Corrupted Files: </b>{corrupted}"
        msg += f"\n<b>cc: </b>{self.tag}\n\n"

        if not files:
            await send_message(self.message, msg)
            return

        files_msg = ""
        for index, (link, name) in enumerate(files.items(), start=1):
            files_msg += f"{index}. <a href='{link}'>{name}</a>\n"
            if len(files_msg.encode() + msg.encode()) > 4000:
                await send_message(self.message, msg + files_msg)
                await sleep(1)
                files_msg = ""
        if files_msg:
            await send_message(self.message, msg + files_msg)

    def _build_non_leech_message(self, msg, mime_type, files, folders):
        msg += f"\n\n<b>Type: </b>{mime_type}"
        if mime_type == "Folder":
            msg += f"\n<b>SubFolders: </b>{folders}"
            msg += f"\n<b>Files: </b>{files}"
        return msg

    def _add_cloud_button(self, buttons, link):
        if link:
            buttons.url_button("☁️ Cloud Link", link)
    
    def _add_rclone_button(self, buttons, rclone_path, mime_type):
        if not (rclone_path and Config.RCLONE_SERVE_URL and not self.private_link):
            return
        remote, rpath = rclone_path.split(":", 1)
        url_path = rutils.quote(f"{rpath}")
        share_url = f"{Config.RCLONE_SERVE_URL}/{remote}/{url_path}"
        if mime_type == "Folder":
            share_url += "/"
        buttons.url_button("🔗 Rclone Link", share_url)
    
    def _add_index_buttons(self, buttons, mime_type, dir_id):
        index_url = ""
        if self.private_link:
            index_url = self.user_dict.get("INDEX_URL", "") or ""
        elif Config.INDEX_URL:
            index_url = Config.INDEX_URL
        
        if not index_url:
            return
        
        share_url = f"{index_url}findpath?id={dir_id}"
        buttons.url_button("⚡ Index Link", share_url)
        if mime_type.startswith(("image", "video", "audio")):
            buttons.url_button("🌐 View Link", f"{index_url}findpath?id={dir_id}&view=true")
    
    def _build_non_leech_buttons(self, link, rclone_path, mime_type, dir_id):
        if not (link or (rclone_path and Config.RCLONE_SERVE_URL and not self.private_link)):
            return None

        buttons = ButtonMaker()
        self._add_cloud_button(buttons, link)
        self._add_rclone_button(buttons, rclone_path, mime_type)
        
        if not rclone_path and dir_id:
            self._add_index_buttons(buttons, mime_type, dir_id)
        
        return buttons.build_menu(2)

    async def _send_non_leech_complete_message(
        self,
        msg,
        link,
        files,
        folders,
        mime_type,
        rclone_path,
        dir_id,
    ):
        msg = self._build_non_leech_message(msg, mime_type, files, folders)
        button = self._build_non_leech_buttons(link, rclone_path, mime_type, dir_id)
        if not button and rclone_path:
            msg += f"\n\nPath: <code>{rclone_path}</code>"
        elif not link and rclone_path and button:
            msg += f"\n\nPath: <code>{rclone_path}</code>"
        msg += f"\n\n<b>cc: </b>{self.tag}"
        await send_message(self.message, msg, button)

    async def _post_upload_cleanup(self):
        if self.seed:
            await clean_target(self.up_dir)
            async with queue_dict_lock:
                if self.mid in non_queued_up:
                    non_queued_up.remove(self.mid)
            await start_from_queued()
            return

        await clean_download(self.dir)
        async with task_dict_lock:
            if self.mid in task_dict:
                del task_dict[self.mid]
            count = len(task_dict)
        if count == 0:
            await self.clean()
        else:
            await update_status_message(self.message.chat.id)

        async with queue_dict_lock:
            if self.mid in non_queued_up:
                non_queued_up.remove(self.mid)
        await start_from_queued()

    async def _prepare_download_paths(self, gid):
        if self.folder_name:
            self.name = self.folder_name.strip("/").split("/", 1)[0]

        if not await self._recover_missing_name_from_dir(gid):
            return None, None

        dl_path = f"{self.dir}/{self.name}"
        self.size = await get_path_size(dl_path)
        self.is_file = await aiopath.isfile(dl_path)

        if not self.seed:
            return self.dir, dl_path

        self.up_dir = f"{self.dir}10000"
        up_path = f"{self.up_dir}/{self.name}"
        await create_recursive_symlink(self.dir, self.up_dir)
        LOGGER.info(f"Shortcut created: {dl_path} -> {up_path}")
        return self.up_dir, up_path

    async def _resolve_multi_link_state(self, multi_links):
        if multi_links:
            self.seed = False
            await self.on_upload_error(
                f"{self.name} Downloaded!\n\nWaiting for other tasks to finish..."
            )
            return False
        if self.same_dir:
            self.seed = False
        return True

    async def _release_download_queue_slot(self):
        if Config.QUEUE_ALL:
            return
        async with queue_dict_lock:
            if self.mid in non_queued_dl:
                non_queued_dl.remove(self.mid)
        await start_from_queued()

    async def _wait_for_upload_queue_if_needed(self, gid):
        add_to_queue, event = await check_running_tasks(self, "up")
        await start_from_queued()
        if not add_to_queue:
            return True

        LOGGER.info(f"Added to Queue/Upload: {self.name}")
        async with task_dict_lock:
            task_dict[self.mid] = QueueStatus(self, gid, "Up")
        await event.wait()
        if self.is_cancelled:
            return False

        LOGGER.info(f"Start from Queued/Upload: {self.name}")
        return True

    async def _prepare_upload_target(self, up_path, up_dir, gid):
        up_path = await self._run_post_download_processing(up_path, up_dir, gid)
        if up_path is None:
            return None

        self.name = up_path.replace(f"{up_dir}/", "").split("/", 1)[0]
        self.size = await get_path_size(up_dir)

        if self.is_leech and not self.compress:
            await self.proceed_split(up_path, gid)
            if self.is_cancelled:
                return None
            self.clear()

        self.subproc = None
        return up_path

    async def _prepare_completion_upload_context(self):
        if self.is_cancelled:
            return None

        multi_links, should_return = await self._handle_same_dir_merge()
        if should_return:
            return None

        gid = await self._resolve_download_meta()
        if gid is None:
            return None

        if not (self.is_torrent or self.is_qbit):
            self.seed = False

        if not await self._resolve_multi_link_state(multi_links):
            return None

        up_dir, up_path = await self._prepare_download_paths(gid)
        if up_path is None:
            return None

        await self._apply_include_exclude_filters()
        await self._release_download_queue_slot()

        up_path = await self._prepare_upload_target(up_path, up_dir, gid)
        if up_path is None:
            return None

        return gid, up_dir, up_path

    async def on_download_complete(self):
        await sleep(2)
        context = await self._prepare_completion_upload_context()
        if context is None:
            return

        gid, up_dir, up_path = context

        if not await self._wait_for_upload_queue_if_needed(gid):
            return

        self.size = await get_path_size(up_dir)

        await self._dispatch_upload(up_dir, up_path, gid)
        return

    async def on_upload_complete(
        self, link, files, folders, mime_type, rclone_path="", dir_id=""
    ):
        if (
            self.is_super_chat
            and Config.INCOMPLETE_TASK_NOTIFIER
            and Config.DATABASE_URL
        ):
            await database.rm_complete_task(self.message.link)
        msg = self._build_base_complete_message(self.name, self.size)
        LOGGER.info(f"Task Done: {self.name}")
        if self.is_leech:
            await self._send_leech_complete_messages(msg, files, folders, mime_type)
        else:
            await self._send_non_leech_complete_message(
                msg,
                link,
                files,
                folders,
                mime_type,
                rclone_path,
                dir_id,
            )
        add_history(
            name=self.name,
            size=self.size,
            status="success",
            user_id=self.user_id,
            tag=self.tag,
            link=link or rclone_path or "",
            tool="leech" if self.is_leech else "upload",
        )
        await self._post_upload_cleanup()

    async def _remove_task_and_get_count(self) -> int:
        async with task_dict_lock:
            if self.mid in task_dict:
                del task_dict[self.mid]
            return len(task_dict)

    async def _update_failure_status(self, count: int) -> None:
        if count == 0:
            await self.clean()
            return
        await update_status_message(self.message.chat.id)

    async def _cleanup_incomplete_notifier(self) -> None:
        if (
            self.is_super_chat
            and Config.INCOMPLETE_TASK_NOTIFIER
            and Config.DATABASE_URL
        ):
            await database.rm_complete_task(self.message.link)

    async def _release_queue_entries(self) -> None:
        async with queue_dict_lock:
            if self.mid in queued_dl:
                queued_dl[self.mid].set()
                del queued_dl[self.mid]
            if self.mid in queued_up:
                queued_up[self.mid].set()
                del queued_up[self.mid]
            if self.mid in non_queued_dl:
                non_queued_dl.remove(self.mid)
            if self.mid in non_queued_up:
                non_queued_up.remove(self.mid)

    async def _cleanup_task_paths(self) -> None:
        await sleep(3)
        await clean_download(self.dir)
        if self.up_dir:
            await clean_download(self.up_dir)
        if self.thumb and await aiopath.exists(self.thumb):
            await remove(self.thumb)

    async def _handle_task_failure(self, message_text: str, history_tool: str, button=None):
        count = await self._remove_task_and_get_count()
        await self.remove_from_same_dir()
        await send_message(self.message, message_text, button)
        add_history(
            name=self.name,
            size=self.size,
            status="failed",
            user_id=self.user_id,
            tag=self.tag,
            link=self.link,
            tool=history_tool,
        )
        await self._update_failure_status(count)
        await self._cleanup_incomplete_notifier()
        await self._release_queue_entries()
        await start_from_queued()
        await self._cleanup_task_paths()

    async def on_download_error(self, error, button=None):
        msg = f"{self.tag} Download: {escape(str(error))}"
        await self._handle_task_failure(msg, "download", button)

    async def on_upload_error(self, error):
        msg = f"{self.tag} {escape(str(error))}"
        await self._handle_task_failure(msg, "upload")
