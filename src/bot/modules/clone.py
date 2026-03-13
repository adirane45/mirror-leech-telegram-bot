from asyncio import gather
from json import loads
from secrets import token_urlsafe
from typing import Any

from aiofiles.os import remove  # type: ignore[import-untyped]

from .. import LOGGER, bot_loop, task_dict, task_dict_lock
from ..helper.ext_utils.bot_utils import COMMAND_USAGE, arg_parser, cmd_exec, sync_to_async
from ..helper.ext_utils.exceptions import DirectDownloadLinkException
from ..helper.ext_utils.links_utils import is_gdrive_id, is_gdrive_link, is_rclone_path, is_share_link
from ..helper.ext_utils.task_manager import stop_duplicate_check
from ..helper.listeners.task_listener import TaskListener
from ..helper.mirror_leech_utils.download_utils.direct_link_generator import direct_link_generator
from ..helper.mirror_leech_utils.gdrive_utils.clone import GoogleDriveClone
from ..helper.mirror_leech_utils.gdrive_utils.count import GoogleDriveCount
from ..helper.mirror_leech_utils.rclone_utils.transfer import RcloneTransferHelper
from ..helper.mirror_leech_utils.status_utils.gdrive_status import GoogleDriveStatus
from ..helper.mirror_leech_utils.status_utils.rclone_status import RcloneStatus
from ..helper.telegram_helper.bot_commands import BotCommands
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.message_utils import delete_message, send_message, send_status_message


class Clone(TaskListener):
    link: str
    name: str
    up_dest: str
    rc_flags: str
    multi: int
    same_dir: dict[str, Any]
    
    def __init__(
        self,
        client: Any,
        message: Any,
        _: Any = None,
        __: Any = None,
        ___: Any = None,
        ____: Any = None,
        _____: Any = None,
        bulk: list[Any] | None = None,
        multi_tag: Any = None,
        options: str = "",
    ) -> None:
        if bulk is None:
            bulk = []
        self.message = message
        self.client = client
        self.multi_tag = multi_tag
        self.options = options
        self.same_dir = {}
        self.bulk = bulk
        self.link = ""
        self.name = ""
        self.up_dest = ""
        self.rc_flags = ""
        self.multi = 0
        super().__init__()
        self.is_clone = True

    def _parse_clone_arguments(self, input_list: list[str]) -> tuple[bool | str, bool]:
        """Parse and validate clone command arguments."""
        args = {
            "link": "",
            "-i": 0,
            "-b": False,
            "-n": "",
            "-up": "",
            "-rcf": "",
            "-sync": False,
        }
        arg_parser(input_list[1:], args)
        
        try:
            self.multi = int(str(args["-i"]))
        except (KeyError, ValueError, TypeError):
            self.multi = 0
        
        self.up_dest = str(args["-up"])
        self.rc_flags = str(args["-rcf"])
        self.link = str(args["link"])
        self.name = str(args["-n"])
        
        return bool(args["-b"]) if isinstance(args["-b"], bool) else str(args["-b"]), bool(args["-sync"])

    def _parse_bulk_range(self, is_bulk: bool | str) -> tuple[bool, int, int]:
        """Parse bulk download range parameters."""
        bulk_start = 0
        bulk_end = 0
        
        if not isinstance(is_bulk, bool):
            dargs = is_bulk.split(":")
            bulk_start = int(dargs[0]) if dargs[0] else 0
            if len(dargs) == 2:
                bulk_end = int(dargs[1]) if dargs[1] else 0
            is_bulk = True
        
        return is_bulk, bulk_start, bulk_end

    async def _resolve_link_from_reply(self) -> None:
        """Resolve link from reply message if not provided."""
        if not self.link and (reply_to := self.message.reply_to_message):
            self.link = reply_to.text.split("\n", 1)[0].strip()

    async def _show_clone_help(self) -> None:
        """Show clone command help when no link is provided."""
        buttons = ButtonMaker()
        buttons.data_button("Help Menu", "help menu")
        buttons.data_button("Clone Options", "help clone main")
        buttons.data_button("Settings", "quick_settings")
        prompt = (
            "<b>📂 Clone</b>\n\n"
            "Send a drive link or rclone path, or reply to one.\n"
            f"Example: <code>/{BotCommands.CloneCommand} https://drive.google.com/...</code>"
        )
        await send_message(self.message, prompt, buttons.build_menu(2))

    async def new_event(self) -> None:
        text = self.message.text.split("\n")
        input_list = text[0].split(" ")
        
        is_bulk, sync = self._parse_clone_arguments(input_list)
        is_bulk, bulk_start, bulk_end = self._parse_bulk_range(is_bulk)
        
        if is_bulk:
            await self.init_bulk(input_list, bulk_start, bulk_end, Clone)
            return
        
        await self.get_tag(text)
        await self._resolve_link_from_reply()
        await self.run_multi(input_list, Clone)
        
        if len(self.link) == 0:
            await self._show_clone_help()
            return
        
        LOGGER.info(self.link)
        try:
            await self.before_start()
        except Exception as e:
            await send_message(self.message, e)
            return
        
        await self._proceed_to_clone(sync)

    async def _proceed_to_clone(self, sync: bool) -> None:
        if not await self._resolve_share_link_if_needed():
            return

        if is_gdrive_link(self.link) or is_gdrive_id(self.link):
            await self._clone_gdrive_path()
            return

        if is_rclone_path(self.link):
            await self._clone_rclone_path(sync)
            return

        await send_message(
            self.message, COMMAND_USAGE["clone"][0], COMMAND_USAGE["clone"][1]
        )

    async def _resolve_share_link_if_needed(self) -> bool:
        if is_share_link(self.link):
            try:
                self.link = await sync_to_async(direct_link_generator, self.link)
                LOGGER.info(f"Generated link: {self.link}")
            except DirectDownloadLinkException as e:
                LOGGER.error(str(e))
                if str(e).startswith("ERROR:"):
                    await send_message(self.message, str(e))
                    return False
        return True

    async def _clone_gdrive_path(self) -> None:
        self.name, mime_type, self.size, files, _ = await sync_to_async(
            GoogleDriveCount().count, self.link, self.user_id
        )
        if mime_type is None:
            await send_message(self.message, self.name)
            return
        msg, button = await stop_duplicate_check(self)
        if msg:
            await send_message(self.message, msg, button)
            return

        await self.on_download_start()
        LOGGER.info(f"Clone Started: Name: {self.name} - Source: {self.link}")
        drive = GoogleDriveClone(self)
        if files <= 10:
            status_msg = await send_message(self.message, f"Cloning: <code>{self.link}</code>")
        else:
            status_msg = ""
            gid = token_urlsafe(12)
            async with task_dict_lock:
                task_dict[self.mid] = GoogleDriveStatus(self, drive, gid, "cl")
            if self.multi <= 1:
                await send_status_message(self.message)

        flink, mime_type, files, folders, dir_id = await sync_to_async(drive.clone)
        if status_msg:
            await delete_message(status_msg)
        if not flink:
            return
        await self.on_upload_complete(flink, files, folders, mime_type, dir_id=dir_id)
        LOGGER.info(f"Cloning Done: {self.name}")

    def _resolve_rclone_config(self) -> str:
        if self.link.startswith("mrcc:"):
            self.link = self.link.replace("mrcc:", "", 1)
            self.up_dest = self.up_dest.replace("mrcc:", "", 1)
            return f"rclone/{self.user_id}.conf"
        return "rclone.conf"

    async def _resolve_rclone_source(self, config_path: str) -> tuple[str | None, str | None, str | None]:
        remote, src_path = self.link.split(":", 1)
        self.link = src_path.strip("/")

        if self.link.startswith("rclone_select"):
            if not self.name:
                self.name = self.link
            return remote, "", "Folder"

        src_path_str = self.link
        cmd = [
            "rclone",
            "lsjson",
            "--fast-list",
            "--stat",
            "--no-modtime",
            "--config",
            config_path,
            f"{remote}:{src_path_str}",
        ]
        res = await cmd_exec(cmd)
        if res[2] != 0:
            if res[2] != -9:
                msg = f"Error: While getting rclone stat. Path: {remote}:{src_path_str}. Stderr: {res[1][:4000]}"
                await send_message(self.message, msg)
            return None, None, None

        rstat = loads(res[0])
        if rstat["IsDir"]:
            if not self.name:
                self.name = src_path_str.rsplit("/", 1)[-1] if src_path_str else remote
            self.up_dest += self.name if self.up_dest.endswith(":") else f"/{self.name}"
            return remote, src_path_str, "Folder"

        if not self.name:
            self.name = src_path_str.rsplit("/", 1)[-1]
        return remote, src_path_str, str(rstat["MimeType"])

    async def _finalize_rclone_clone(self, config_path: str, destination: str, flink: str, mime_type: str) -> None:
        cmd1 = [
            "rclone",
            "lsf",
            "--fast-list",
            "-R",
            "--files-only",
            "--config",
            config_path,
            destination,
        ]
        cmd2 = [
            "rclone",
            "lsf",
            "--fast-list",
            "-R",
            "--dirs-only",
            "--config",
            config_path,
            destination,
        ]
        cmd3 = [
            "rclone",
            "size",
            "--fast-list",
            "--json",
            "--config",
            config_path,
            destination,
        ]
        res1, res2, res3 = await gather(cmd_exec(cmd1), cmd_exec(cmd2), cmd_exec(cmd3))
        if res1[2] != 0 or res2[2] != 0 or res3[2] != 0:
            if res1[2] == -9:
                return
            self.size = 0
            error = res1[1] or res2[1] or res3[1]
            msg = f"Error: While getting rclone stat. Path: {destination}. Stderr: {error[:4000]}"
            await self.on_upload_error(msg)
            return

        files = len(res1[0].split("\n"))
        folders = len(res2[0].strip().split("\n")) if res2[0] else 0
        self.size = loads(res3[0])["bytes"]
        await self.on_upload_complete(flink, files, folders, mime_type, destination)

    async def _clone_rclone_path(self, sync: bool) -> None:
        config_path = self._resolve_rclone_config()
        remote, src_path, mime_type = await self._resolve_rclone_source(config_path)
        if remote is None:
            return

        await self.on_download_start()
        transfer = RcloneTransferHelper(self)
        LOGGER.info(
            f"Clone Started: Name: {self.name} - Source: {self.link} - Destination: {self.up_dest}"
        )
        gid = token_urlsafe(12)
        async with task_dict_lock:
            task_dict[self.mid] = RcloneStatus(self, transfer, gid, "cl")
        if self.multi <= 1:
            await send_status_message(self.message)

        method = "sync" if sync else "copy"
        flink, destination = await transfer.clone(
            config_path,
            remote,
            src_path,
            mime_type,
            method,
        )
        if self.link.startswith("rclone_select"):
            await remove(self.link)
        if not destination:
            return

        LOGGER.info(f"Cloning Done: {self.name}")
        if mime_type:
            await self._finalize_rclone_clone(config_path, destination, flink, mime_type)


async def clone_node(client: Any, message: Any) -> None:
    bot_loop.create_task(Clone(client, message).new_event())
