from base64 import b64encode
from os import path as ospath
from re import match as re_match

from aiofiles.os import path as aiopath

from .. import DOWNLOAD_DIR, LOGGER, task_dict_lock, user_data
from ..core.client_selector import ClientType, client_selector
from ..core.config_manager import Config
from ..core.link_bypassers import LinkBypassEngine
from ..helper.ext_utils.bot_utils import arg_parser, get_content_type, sync_to_async
from ..helper.ext_utils.exceptions import DirectDownloadLinkException
from ..helper.ext_utils.links_utils import (
    is_gdrive_id,
    is_gdrive_link,
    is_magnet,
    is_rclone_path,
    is_telegram_link,
    is_url,
)
from ..helper.listeners.task_listener import TaskListener
from ..helper.mirror_leech_utils.download_utils.aria2_download import add_aria2_download
from ..helper.mirror_leech_utils.download_utils.direct_downloader import add_direct_download
from ..helper.mirror_leech_utils.download_utils.direct_link_generator import direct_link_generator
from ..helper.mirror_leech_utils.download_utils.gd_download import add_gd_download
from ..helper.mirror_leech_utils.download_utils.jd_download import add_jd_download
from ..helper.mirror_leech_utils.download_utils.nzb_downloader import add_nzb
from ..helper.mirror_leech_utils.download_utils.qbit_download import add_qb_torrent
from ..helper.mirror_leech_utils.download_utils.rclone_download import add_rclone_download
from ..helper.mirror_leech_utils.download_utils.telegram_download import TelegramDownloadHelper
from ..helper.telegram_helper.bot_commands import BotCommands
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.message_utils import get_tg_link_message, send_message

LINK_BYPASS_ENGINE = LinkBypassEngine(
    enabled=getattr(Config, "ENABLE_LINK_BYPASS", True)
)


class Mirror(TaskListener):
    def __init__(
        self,
        client,
        message,
        is_qbit=False,
        is_leech=False,
        is_jd=False,
        is_nzb=False,
        same_dir=None,
        bulk=None,
        multi_tag=None,
        options="",
    ):
        if same_dir is None:
            same_dir = {}
        if bulk is None:
            bulk = []
        super().__init__()
        self.message = message
        self.client = client
        self.multi_tag = multi_tag
        self.options = options
        self.same_dir = same_dir
        self.bulk = bulk
        self.is_qbit = is_qbit
        self.is_leech = is_leech
        self.is_jd = is_jd
        self.is_nzb = is_nzb

    async def _bypass_url_if_needed(self):
        if not isinstance(self.link, str):
            return
        if not is_url(self.link) or is_telegram_link(self.link):
            return

        try:
            result = await LINK_BYPASS_ENGINE.normalize_link(self.link)
            if result.bypassed:
                LOGGER.info(
                    "Bypassed URL (%s): %s -> %s",
                    result.service,
                    result.original_url,
                    result.final_url,
                )
            self.link = result.final_url
        except Exception as e:
            LOGGER.debug(f"URL bypass failed for {self.link}: {e}")

    def _extract_message_context(self):
        try:
            if not self.message:
                LOGGER.error("❌ new_event: self.message is None!")
                return None, None

            if not self.message.text:
                LOGGER.error("❌ new_event: self.message.text is None!")
                return None, None

            self.mid = self.message.id
            self.user = self.message.from_user or self.message.sender_chat
            self.user_id = self.user.id if self.user else None
            self.user_dict = user_data.get(self.user_id, {}) if self.user_id else {}
            text = self.message.text.split("\n")
            input_list = text[0].split(" ")
            return text, input_list
        except AttributeError as e:
            LOGGER.error(f"❌ new_event AttributeError: {e} | message={self.message}")
            return None, None
        except Exception as e:
            LOGGER.error(f"❌ new_event Error: {e}")
            return None, None

    def _parse_and_apply_args(self, input_list):
        args = {
            "-doc": False,
            "-med": False,
            "-d": False,
            "-j": False,
            "-s": False,
            "-b": False,
            "-e": False,
            "-z": False,
            "-sv": False,
            "-ss": False,
            "-f": False,
            "-fd": False,
            "-fu": False,
            "-hl": False,
            "-bt": False,
            "-ut": False,
            "-i": 0,
            "-sp": 0,
            "link": "",
            "-n": "",
            "-m": "",
            "-up": "",
            "-rcf": "",
            "-au": "",
            "-ap": "",
            "-h": [],
            "-t": "",
            "-ca": "",
            "-cv": "",
            "-ns": "",
            "-tl": "",
            "-ff": set(),
        }

        arg_parser(input_list[1:], args)

        self.select = args["-s"]
        self.seed = args["-d"]
        self.name = args["-n"]
        self.up_dest = args["-up"]
        self.rc_flags = args["-rcf"]
        self.link = args["link"]
        self.compress = args["-z"]
        self.extract = args["-e"]
        self.join = args["-j"]
        self.thumb = args["-t"]
        self.split_size = args["-sp"]
        self.sample_video = args["-sv"]
        self.screen_shots = args["-ss"]
        self.force_run = args["-f"]
        self.force_download = args["-fd"]
        self.force_upload = args["-fu"]
        self.convert_audio = args["-ca"]
        self.convert_video = args["-cv"]
        self.name_sub = args["-ns"]
        self.hybrid_leech = args["-hl"]
        self.thumbnail_layout = args["-tl"]
        self.as_doc = args["-doc"]
        self.as_med = args["-med"]
        self.folder_name = f"/{args['-m']}".rstrip("/") if len(args["-m"]) > 0 else ""
        self.bot_trans = args["-bt"]
        self.user_trans = args["-ut"]
        self.ffmpeg_cmds = args["-ff"]

        headers = args["-h"]
        if headers:
            headers = headers.split("|")

        is_bulk, bulk_start, bulk_end = self._parse_bulk_args(args["-b"])
        ratio, seed_time = self._parse_seed_args()
        self._parse_multi_arg(args["-i"])

        return args, headers, is_bulk, bulk_start, bulk_end, ratio, seed_time

    def _parse_multi_arg(self, multi_arg):
        try:
            self.multi = int(multi_arg)
        except (KeyError, ValueError, TypeError):
            self.multi = 0

    def _parse_seed_args(self):
        if isinstance(self.seed, bool):
            return None, None
        dargs = self.seed.split(":")
        ratio = dargs[0] or None
        seed_time = dargs[1] if len(dargs) == 2 else None
        self.seed = True
        return ratio, seed_time

    def _parse_bulk_args(self, bulk_arg):
        if isinstance(bulk_arg, bool):
            return bulk_arg, 0, 0
        dargs = bulk_arg.split(":")
        bulk_start = dargs[0] or "0"
        bulk_end = dargs[1] if len(dargs) == 2 else "0"
        return True, bulk_start, bulk_end

    async def _handle_bulk_or_multi(self, input_list, is_bulk, bulk_start, bulk_end):
        if is_bulk:
            await self.init_bulk(input_list, bulk_start, bulk_end, Mirror)
            return True

        if self.multi > 0:
            await self._update_multi_same_dir_state()

        if len(self.bulk) != 0:
            del self.bulk[0]

        await self.run_multi(input_list, Mirror)
        return False

    def _decrement_same_dir_totals(self, skip_folder=None):
        for fd_name in self.same_dir:
            if skip_folder is not None and fd_name == skip_folder:
                continue
            self.same_dir[fd_name]["total"] -= 1

    def _ensure_folder_entry(self):
        if self.folder_name in self.same_dir:
            self.same_dir[self.folder_name]["tasks"].add(self.mid)
            return

        self.same_dir[self.folder_name] = {
            "total": self.multi,
            "tasks": {self.mid},
        }

    async def _update_multi_same_dir_state(self):
        if self.folder_name:
            async with task_dict_lock:
                if not self.same_dir:
                    self.same_dir = {
                        self.folder_name: {
                            "total": self.multi,
                            "tasks": {self.mid},
                        }
                    }
                    return
                self._ensure_folder_entry()
                self._decrement_same_dir_totals(skip_folder=self.folder_name)
            return

        if self.same_dir:
            async with task_dict_lock:
                self._decrement_same_dir_totals()

    async def _resolve_reply_and_link(self, input_list):
        reply_to = None
        file_ = None
        session = ""

        reply_to = self._resolve_initial_reply_link()

        await self._bypass_url_if_needed()

        if is_telegram_link(self.link):
            reply_to, session, should_return = await self._resolve_telegram_reply_target()
            if should_return:
                return None, None, None, True

        if isinstance(reply_to, list):
            await self._dispatch_bulk_mirror(reply_to, input_list)
            return None, None, None, True

        if reply_to:
            reply_to, file_ = await self._resolve_reply_file_or_link(reply_to)

        return reply_to, file_, session, False

    def _resolve_initial_reply_link(self):
        reply_to = self.message.reply_to_message
        if not self.link and reply_to and reply_to.text:
            self.link = reply_to.text.split("\n", 1)[0].strip()
        return reply_to

    async def _resolve_telegram_reply_target(self):
        try:
            reply_to, session = await get_tg_link_message(self.link)
            return reply_to, session, False
        except Exception as e:
            await send_message(self.message, f"ERROR: {e}")
            await self.remove_from_same_dir()
            return None, None, True

    async def _dispatch_bulk_mirror(self, reply_to, input_list):
        self.bulk = reply_to
        b_msg = input_list[:1]
        self.options = " ".join(input_list[1:])
        b_msg.append(f"{self.bulk[0]} -i {len(self.bulk)} {self.options}")
        nextmsg = await send_message(self.message, " ".join(b_msg))
        nextmsg = await self.client.get_messages(
            chat_id=self.message.chat.id, message_ids=nextmsg.id
        )
        if self.message.from_user:
            nextmsg.from_user = self.user
        else:
            nextmsg.sender_chat = self.user
        await Mirror(
            self.client,
            nextmsg,
            self.is_qbit,
            self.is_leech,
            self.is_jd,
            self.is_nzb,
            self.same_dir,
            self.bulk,
            self.multi_tag,
            self.options,
        ).new_event()

    def _extract_reply_media(self, reply_to):
        return (
            reply_to.document
            or reply_to.photo
            or reply_to.video
            or reply_to.audio
            or reply_to.voice
            or reply_to.video_note
            or reply_to.sticker
            or reply_to.animation
            or None
        )

    async def _resolve_reply_file_or_link(self, reply_to):
        file_ = self._extract_reply_media(reply_to)
        if file_ is None:
            if reply_text := reply_to.text:
                self.link = reply_text.split("\n", 1)[0].strip()
            else:
                reply_to = None
            return reply_to, file_

        if reply_to.document and (
            file_.mime_type == "application/x-bittorrent"
            or file_.file_name.endswith((".torrent", ".dlc", ".nzb"))
        ):
            file_name = file_.file_name or "telegram.file"
            download_path = ospath.join(DOWNLOAD_DIR, file_name)
            self.link = await reply_to.download(file_name=download_path)
            return reply_to, None

        return reply_to, file_

    async def _is_invalid_link_input(self, reply_to, file_):
        if not self.link and file_ is None:
            return True
        if is_telegram_link(self.link) and reply_to is None:
            return True
        if file_ is not None:
            return False
        return not await self._is_supported_link_source()

    async def _is_supported_link_source(self):
        return (
            is_url(self.link)
            or is_magnet(self.link)
            or await aiopath.exists(self.link)
            or is_rclone_path(self.link)
            or is_gdrive_id(self.link)
            or is_gdrive_link(self.link)
        )

    async def _send_invalid_link_prompt(self):
        buttons = ButtonMaker()

        if self.is_qbit:
            buttons.data_button("Magnet Link Info", "help qbit main")
            buttons.data_button("Torrent Search", "search main")
            prompt = (
                "<b>🧲 qBittorrent Mirror</b>\n\n"
                "<b>Send:</b>\n"
                "• Magnet link (magnet:?xt=urn:btih:...)\n"
                "• Torrent URL (https://...file.torrent)\n"
                "• .torrent file (reply with file)\n\n"
                "<b>NOT supported:</b> HTTP/HTTPS direct downloads\n"
                "(Use /mirror or /m for direct downloads)"
            )
        else:
            buttons.data_button("Help Menu", "help menu")
            buttons.data_button("Mirror Options", "help mirror main")
            buttons.data_button("YT-DLP Options", "help yt main")
            buttons.data_button("Settings", "quick_settings")
            prompt = (
                "<b>📥 Mirror/Leech</b>\n\n"
                "Send a link or reply to a file/message.\n"
                f"Example: <code>/{BotCommands.MirrorCommand[0]} https://example.com/file.zip</code>\n"
                f"Leech: <code>/{BotCommands.LeechCommand[0]} https://example.com/file.zip</code>"
            )

        await send_message(self.message, prompt, buttons.build_menu(2))
        await self.remove_from_same_dir()

    def _should_prepare_direct_link(self, file_):
        return (
            not self.is_jd
            and not self.is_nzb
            and not self.is_qbit
            and not is_magnet(self.link)
            and not is_rclone_path(self.link)
            and not is_gdrive_link(self.link)
            and not self.link.endswith(".torrent")
            and file_ is None
            and not is_gdrive_id(self.link)
        )

    async def _is_html_or_text_content(self):
        content_type = await get_content_type(self.link)
        return content_type is None or re_match(r"text/html|text/plain", content_type)

    async def _handle_direct_link_generation(self, headers):
        try:
            self.link = await sync_to_async(direct_link_generator, self.link)
            if isinstance(self.link, tuple):
                self.link, headers = self.link
            elif isinstance(self.link, str):
                LOGGER.info(f"Generated link: {self.link}")
            return headers, False
        except DirectDownloadLinkException as e:
            e = str(e)
            if "This link requires a password!" not in e:
                LOGGER.info(e)
            if e.startswith("ERROR:"):
                await send_message(self.message, e)
                await self.remove_from_same_dir()
                return headers, True
            return headers, False
        except Exception as e:
            LOGGER.exception("direct_link_generator failed")
            await send_message(self.message, e)
            await self.remove_from_same_dir()
            return headers, True

    async def _prepare_direct_link_if_needed(self, file_, headers):
        if not self._should_prepare_direct_link(file_):
            return headers, False
        if not await self._is_html_or_text_content():
            return headers, False
        return await self._handle_direct_link_generation(headers)

    async def _validate_qbit_input(self, file_):
        if self.is_qbit and not self.is_nzb:
            link_is_valid_for_qbit = (
                is_magnet(self.link)
                or self.link.endswith(".torrent")
                or (
                    isinstance(self.link, str)
                    and (
                        self.link.startswith(("http://", "https://"))
                        and self.link.endswith(".torrent")
                    )
                )
                or await aiopath.exists(self.link)
                or file_ is not None
            )
            if not link_is_valid_for_qbit:
                await send_message(
                    self.message,
                    "❌ <b>Invalid link for /qm (qBittorrent)</b>\n\n"
                    "✅ Supported formats:\n"
                    "• Magnet: <code>magnet:?xt=urn:btih:...</code>\n"
                    "• Torrent URL: <code>https://example.com/file.torrent</code>\n"
                    "• File: Reply with .torrent file\n\n"
                    "❌ NOT supported:\n"
                    "• Direct HTTP files\n"
                    "• Google Drive links\n"
                    "• Rclone paths\n\n"
                    "Use <b>/mirror</b> for direct downloads.",
                )
                await self.remove_from_same_dir()
                return False
        return True

    async def _select_auto_client(self, file_):
        auto_client = None
        if self._can_auto_select_client(file_):
            try:
                auto_client, _ = await client_selector.select_client(
                    self.link,
                    user_id=getattr(self, "user_id", None),
                )
            except Exception as e:
                LOGGER.debug(f"Client selection skipped: {e}")
        return auto_client

    def _can_auto_select_client(self, file_):
        return (
            getattr(Config, "ENABLE_CLIENT_SELECTION", True)
            and not self.is_jd
            and not self.is_nzb
            and not self.is_qbit
            and file_ is None
            and not isinstance(self.link, dict)
            and not is_rclone_path(self.link)
            and not is_gdrive_link(self.link)
            and not is_gdrive_id(self.link)
        )

    def _apply_auth_headers(self, headers, args):
        ussr = args["-au"]
        pssw = args["-ap"]
        if ussr or pssw:
            auth = f"{ussr}:{pssw}"
            headers.extend(
                [f"authorization: Basic {b64encode(auth.encode()).decode('ascii')}"]
            )

    async def _start_telegram_download(self, reply_to, path, session):
        await TelegramDownloadHelper(self).add_download(reply_to, f"{path}", session)

    async def _start_torrent_download(self, path, ratio, seed_time):
        await add_qb_torrent(self, path, ratio, seed_time)

    async def _start_aria_download(self, path, headers, ratio, seed_time, args):
        self._apply_auth_headers(headers, args)
        await add_aria2_download(self, path, headers, ratio, seed_time)

    async def _route_specialized_download(self, path, ratio, seed_time, headers, args, auto_client):
        if isinstance(self.link, dict):
            await add_direct_download(self, path)
            return True
        if self.is_jd:
            await add_jd_download(self, path)
            return True
        if self.is_nzb or auto_client == ClientType.SABNZBD:
            await add_nzb(self, path)
            return True
        if is_rclone_path(self.link):
            await add_rclone_download(self, f"{path}")
            return True
        if is_gdrive_link(self.link) or is_gdrive_id(self.link):
            await add_gd_download(self, path)
            return True
        return False

    async def _start_download(
        self, file_, reply_to, path, session, ratio, seed_time, headers, args, auto_client
    ):
        if file_ is not None:
            await self._start_telegram_download(reply_to, path, session)
        elif self.is_qbit or auto_client == ClientType.QBITTORRENT:
            await self._start_torrent_download(path, ratio, seed_time)
        elif await self._route_specialized_download(path, ratio, seed_time, headers, args, auto_client):
            return
        else:
            await self._start_aria_download(path, headers, ratio, seed_time, args)

    async def _prepare_event_context(self):
        text, input_list = self._extract_message_context()
        if text is None or input_list is None:
            return None

        args, headers, is_bulk, bulk_start, bulk_end, ratio, seed_time = (
            self._parse_and_apply_args(input_list)
        )

        should_return = await self._handle_bulk_or_multi(
            input_list, is_bulk, bulk_start, bulk_end
        )
        if should_return:
            return None

        await self.get_tag(text)
        path = f"{self.dir}{self.folder_name}/"

        reply_to, file_, session, should_return = await self._resolve_reply_and_link(
            input_list
        )
        if should_return:
            return None

        if await self._is_invalid_link_input(reply_to, file_):
            await self._send_invalid_link_prompt()
            return None

        if len(self.link) > 0:
            LOGGER.info(self.link)

        return {
            "args": args,
            "headers": headers,
            "ratio": ratio,
            "seed_time": seed_time,
            "path": path,
            "reply_to": reply_to,
            "file_": file_,
            "session": session,
        }

    async def _run_before_start(self):
        try:
            await self.before_start()
            return True
        except Exception as e:
            LOGGER.exception("before_start failed")
            await send_message(self.message, e)
            await self.remove_from_same_dir()
            return False

    async def _prepare_download_headers(self, file_, headers):
        headers, should_return = await self._prepare_direct_link_if_needed(file_, headers)
        if should_return:
            return None
        return headers

    async def new_event(self):
        context = await self._prepare_event_context()
        if context is None:
            return

        if not await self._run_before_start():
            return

        headers = await self._prepare_download_headers(
            context["file_"], context["headers"]
        )
        if headers is None:
            return

        if not await self._validate_qbit_input(context["file_"]):
            return

        auto_client = await self._select_auto_client(context["file_"])
        await self._start_download(
            context["file_"],
            context["reply_to"],
            context["path"],
            context["session"],
            context["ratio"],
            context["seed_time"],
            headers,
            context["args"],
            auto_client,
        )


async def mirror(client, message):
    try:
        user_id = message.from_user.id if message.from_user else (message.sender_chat.id if message.sender_chat else 'unknown')
        LOGGER.info(f"🔄 /mirror command received from {user_id}")

        if not message or not message.text:
            LOGGER.error("❌ /mirror: Invalid message object")
            return

        # Execute the mirror task directly - await instead of create_task
        await Mirror(client, message).new_event()
    except Exception as e:
        LOGGER.error(f"❌ /mirror handler error: {e}", exc_info=True)


async def qb_mirror(client, message):
    """Handle /qbmirror or /qm command for qBittorrent downloads
    Requires: magnet link, torrent URL, or .torrent file
    Examples:
        /qm magnet:?xt=urn:btih:...
        /qm https://example.com/file.torrent
    """
    try:
        await Mirror(client, message, is_qbit=True).new_event()
    except Exception as e:
        LOGGER.error(f"❌ /qbmirror handler error: {e}", exc_info=True)


async def jd_mirror(client, message):
    try:
        await Mirror(client, message, is_jd=True).new_event()
    except Exception as e:
        LOGGER.error(f"❌ /jdmirror handler error: {e}", exc_info=True)


async def nzb_mirror(client, message):
    try:
        await Mirror(client, message, is_nzb=True).new_event()
    except Exception as e:
        LOGGER.error(f"❌ /nzbmirror handler error: {e}", exc_info=True)


async def leech(client, message):
    try:
        user_id = message.from_user.id if message.from_user else (message.sender_chat.id if message.sender_chat else 'unknown')
        LOGGER.info(f"📥 /leech command received from {user_id}")

        if not message or not message.text:
            LOGGER.error("❌ /leech: Invalid message object")
            return

        # Execute the leech task directly - await instead of create_task
        await Mirror(client, message, is_leech=True).new_event()
    except Exception as e:
        LOGGER.error(f"❌ /leech handler error: {e}", exc_info=True)


async def qb_leech(client, message):
    try:
        await Mirror(client, message, is_qbit=True, is_leech=True).new_event()
    except Exception as e:
        LOGGER.error(f"❌ /qbleech handler error: {e}", exc_info=True)


async def jd_leech(client, message):
    try:
        await Mirror(client, message, is_leech=True, is_jd=True).new_event()
    except Exception as e:
        LOGGER.error(f"❌ /jdleech handler error: {e}", exc_info=True)


async def nzb_leech(client, message):
    try:
        await Mirror(client, message, is_leech=True, is_nzb=True).new_event()
    except Exception as e:
        LOGGER.error(f"❌ /nzbleech handler error: {e}", exc_info=True)
