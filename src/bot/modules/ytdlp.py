from asyncio import Event, wait_for
from functools import partial
from time import time

from httpx import AsyncClient
from pyrogram.filters import regex, user
from pyrogram.handlers import CallbackQueryHandler
from yt_dlp import YoutubeDL

from .. import LOGGER, task_dict_lock, user_data
from ..core.config_manager import Config
from ..helper.ext_utils.bot_utils import COMMAND_USAGE, arg_parser, new_task, sync_to_async
from ..helper.ext_utils.links_utils import is_url
from ..helper.ext_utils.status_utils import get_readable_file_size, get_readable_time
from ..helper.listeners.task_listener import TaskListener
from ..helper.mirror_leech_utils.download_utils.yt_dlp_download import YoutubeDLHelper
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.message_utils import delete_message, edit_message, send_message


@new_task
async def select_format(_, query, obj):
    data = query.data.split()
    message = query.message
    await query.answer()

    if data[1] == "dict":
        b_name = data[2]
        await obj.qual_subbuttons(b_name)
    elif data[1] == "mp3":
        await obj.mp3_subbuttons()
    elif data[1] == "audio":
        await obj.audio_format()
    elif data[1] == "aq":
        if data[2] == "back":
            await obj.audio_format()
        else:
            await obj.audio_quality(data[2])
    elif data[1] == "back":
        await obj.back_to_main()
    elif data[1] == "cancel":
        await edit_message(message, "Task has been cancelled.")
        obj.qual = None
        obj.listener.is_cancelled = True
        obj.event.set()
    else:
        if data[1] == "sub":
            obj.qual = obj.formats[data[2]][data[3]][1]
        elif "|" in data[1]:
            obj.qual = obj.formats[data[1]]
        else:
            obj.qual = data[1]
        obj.event.set()


class YtSelection:
    def __init__(self, listener):
        self.listener = listener
        self._is_m4a = False
        self._reply_to = None
        self._time = time()
        self._timeout = 120
        self._is_playlist = False
        self._main_buttons = None
        self.event = Event()
        self.formats = {}
        self.qual = None

    async def _event_handler(self):
        pfunc = partial(select_format, obj=self)
        handler = self.listener.client.add_handler(
            CallbackQueryHandler(
                pfunc, filters=regex("^ytq") & user(self.listener.user_id)
            ),
            group=-1,
        )
        try:
            await wait_for(self.event.wait(), timeout=self._timeout)
        except TimeoutError:
            await edit_message(self._reply_to, "Timed Out. Task has been cancelled!")
            self.qual = None
            self.listener.is_cancelled = True
            self.event.set()
        except Exception as e:
            LOGGER.error(f"Quality selection error: {e}")
            self.listener.is_cancelled = True
            self.event.set()
        finally:
            self.listener.client.remove_handler(*handler)

    def _timeout_text(self):
        return get_readable_time(self._timeout - (time() - self._time))

    def _extract_item_size(self, item):
        if item.get("filesize"):
            return item["filesize"]
        if item.get("filesize_approx"):
            return item["filesize_approx"]
        return 0

    def _build_audio_format_entry(self, item, format_id):
        if item.get("video_ext") != "none":
            return None
        if item.get("resolution") != "audio only" and item.get("acodec") == "none":
            return None
        if item.get("audio_ext") == "m4a":
            self._is_m4a = True
        b_name = f"{item.get('acodec') or format_id}-{item['ext']}"
        return b_name, format_id

    def _build_video_format_entry(self, item, format_id):
        if not item.get("height"):
            return None
        height = item["height"]
        ext = item["ext"]
        fps = item["fps"] if item.get("fps") else ""
        b_name = f"{height}p{fps}-{ext}"
        ba_ext = "[ext=m4a]" if self._is_m4a and ext == "mp4" else ""
        v_format = f"{format_id}+ba{ba_ext}/b[height=?{height}]"
        return b_name, v_format

    def _register_single_format_item(self, item):
        if not item.get("tbr"):
            return
        format_id = item["format_id"]
        size = self._extract_item_size(item)

        format_entry = self._build_audio_format_entry(item, format_id)
        if format_entry is None:
            format_entry = self._build_video_format_entry(item, format_id)
        if format_entry is None:
            return

        b_name, v_format = format_entry
        self.formats.setdefault(b_name, {})[f"{item['tbr']}"] = [size, v_format]

    def _add_format_buttons(self, buttons):
        for b_name, tbr_dict in self.formats.items():
            if len(tbr_dict) == 1:
                tbr, v_list = next(iter(tbr_dict.items()))
                button_name = f"{b_name} ({get_readable_file_size(v_list[0])})"
                buttons.data_button(button_name, f"ytq sub {b_name} {tbr}")
            else:
                buttons.data_button(b_name, f"ytq dict {b_name}")

    async def _prepare_playlist_quality(self, buttons):
        self._is_playlist = True
        for i in ["144", "240", "360", "480", "720", "1080", "1440", "2160"]:
            video_format = f"bv*[height<=?{i}][ext=mp4]+ba[ext=m4a]/b[height<=?{i}]"
            b_data = f"{i}|mp4"
            self.formats[b_data] = video_format
            buttons.data_button(f"{i}-mp4", f"ytq {b_data}")
            video_format = f"bv*[height<=?{i}][ext=webm]+ba/b[height<=?{i}]"
            b_data = f"{i}|webm"
            self.formats[b_data] = video_format
            buttons.data_button(f"{i}-webm", f"ytq {b_data}")
        buttons.data_button("MP3", "ytq mp3")
        buttons.data_button("Audio Formats", "ytq audio")
        buttons.data_button("Best Videos", "ytq bv*+ba/b")
        buttons.data_button("Best Audios", "ytq ba/b")
        buttons.data_button("Cancel", "ytq cancel", "footer")
        self._main_buttons = buttons.build_menu(3)
        return f"Choose Playlist Videos Quality:\nTimeout: {self._timeout_text()}"

    async def _prepare_video_quality(self, result, buttons):
        format_dict = result.get("formats")
        if format_dict is not None:
            for item in format_dict:
                self._register_single_format_item(item)
            self._add_format_buttons(buttons)
        buttons.data_button("MP3", "ytq mp3")
        buttons.data_button("Audio Formats", "ytq audio")
        buttons.data_button("Best Video", "ytq bv*+ba/b")
        buttons.data_button("Best Audio", "ytq ba/b")
        buttons.data_button("Cancel", "ytq cancel", "footer")
        self._main_buttons = buttons.build_menu(2)
        return f"Choose Video Quality:\nTimeout: {self._timeout_text()}"

    async def get_quality(self, result):
        buttons = ButtonMaker()
        if "entries" in result:
            msg = await self._prepare_playlist_quality(buttons)
        else:
            msg = await self._prepare_video_quality(result, buttons)
        self._reply_to = await send_message(
            self.listener.message, msg, self._main_buttons
        )
        await self._event_handler()
        if not self.listener.is_cancelled:
            await delete_message(self._reply_to)
        return self.qual

    async def back_to_main(self):
        if self._is_playlist:
            msg = f"Choose Playlist Videos Quality:\nTimeout: {get_readable_time(self._timeout - (time() - self._time))}"
        else:
            msg = f"Choose Video Quality:\nTimeout: {get_readable_time(self._timeout - (time() - self._time))}"
        await edit_message(self._reply_to, msg, self._main_buttons)

    async def qual_subbuttons(self, b_name):
        buttons = ButtonMaker()
        tbr_dict = self.formats[b_name]
        for tbr, d_data in tbr_dict.items():
            button_name = f"{tbr}K ({get_readable_file_size(d_data[0])})"
            buttons.data_button(button_name, f"ytq sub {b_name} {tbr}")
        buttons.data_button("Back", "ytq back", "footer")
        buttons.data_button("Cancel", "ytq cancel", "footer")
        subbuttons = buttons.build_menu(2)
        msg = f"Choose Bit rate for <b>{b_name}</b>:\nTimeout: {get_readable_time(self._timeout - (time() - self._time))}"
        await edit_message(self._reply_to, msg, subbuttons)

    async def mp3_subbuttons(self):
        i = "s" if self._is_playlist else ""
        buttons = ButtonMaker()
        audio_qualities = [64, 128, 320]
        for q in audio_qualities:
            audio_format = f"ba/b-mp3-{q}"
            buttons.data_button(f"{q}K-mp3", f"ytq {audio_format}")
        buttons.data_button("Back", "ytq back")
        buttons.data_button("Cancel", "ytq cancel")
        subbuttons = buttons.build_menu(3)
        msg = f"Choose mp3 Audio{i} Bitrate:\nTimeout: {get_readable_time(self._timeout - (time() - self._time))}"
        await edit_message(self._reply_to, msg, subbuttons)

    async def audio_format(self):
        i = "s" if self._is_playlist else ""
        buttons = ButtonMaker()
        for frmt in ["aac", "alac", "flac", "m4a", "opus", "vorbis", "wav"]:
            audio_format = f"ba/b-{frmt}-"
            buttons.data_button(frmt, f"ytq aq {audio_format}")
        buttons.data_button("Back", "ytq back", "footer")
        buttons.data_button("Cancel", "ytq cancel", "footer")
        subbuttons = buttons.build_menu(3)
        msg = f"Choose Audio{i} Format:\nTimeout: {get_readable_time(self._timeout - (time() - self._time))}"
        await edit_message(self._reply_to, msg, subbuttons)

    async def audio_quality(self, format):
        i = "s" if self._is_playlist else ""
        buttons = ButtonMaker()
        for qual in range(11):
            audio_format = f"{format}{qual}"
            buttons.data_button(qual, f"ytq {audio_format}")
        buttons.data_button("Back", "ytq aq back")
        buttons.data_button("Cancel", "ytq aq cancel")
        subbuttons = buttons.build_menu(5)
        msg = f"Choose Audio{i} Quality:\n0 is best and 10 is worst\nTimeout: {get_readable_time(self._timeout - (time() - self._time))}"
        await edit_message(self._reply_to, msg, subbuttons)


def extract_info(link, options):
    with YoutubeDL(options) as ydl:
        result = ydl.extract_info(link, download=False)
        if result is None:
            raise ValueError("Info result is None")
        return result


async def _mdisk(link, name):
    key = link.split("/")[-1]
    async with AsyncClient(verify=False) as client:
        resp = await client.get(
            f"https://diskuploader.entertainvideo.com/v1/file/cdnurl?param={key}"
        )
    if resp.status_code == 200:
        resp_json = resp.json()
        link = resp_json["source"]
        if not name:
            name = resp_json["filename"]
    return name, link


class YtDlp(TaskListener):
    def __init__(
        self,
        client,
        message,
        _=None,
        is_leech=False,
        __=None,
        ___=None,
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
        self.is_ytdlp = True
        self.is_leech = is_leech

    @staticmethod
    def _default_args():
        return {
            "-doc": False,
            "-med": False,
            "-s": False,
            "-b": False,
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
            "-m": "",
            "-opt": {},
            "-n": "",
            "-up": "",
            "-rcf": "",
            "-t": "",
            "-ca": "",
            "-cv": "",
            "-ns": "",
            "-tl": "",
            "-ff": set(),
        }

    def _apply_parsed_args(self, args):
        self.ffmpeg_cmds = args["-ff"]
        self.select = args["-s"]
        self.name = args["-n"]
        self.up_dest = args["-up"]
        self.rc_flags = args["-rcf"]
        self.link = args["link"]
        self.compress = args["-z"]
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

    @staticmethod
    def _parse_bulk_range(is_bulk):
        bulk_start = 0
        bulk_end = 0
        if isinstance(is_bulk, bool):
            return is_bulk, bulk_start, bulk_end
        dargs = is_bulk.split(":")
        bulk_start = dargs[0] or None
        if len(dargs) == 2:
            bulk_end = dargs[1] or None
        return True, bulk_start, bulk_end

    async def _update_same_dir_counters(self):
        if self.multi <= 0:
            return
        if self.folder_name:
            await self._update_folder_counters()
        elif self.same_dir:
            await self._decrement_all_folder_totals()

    def _decrement_other_folders(self, skip_folder):
        for fd_name in self.same_dir:
            if fd_name != skip_folder:
                self.same_dir[fd_name]["total"] -= 1

    async def _update_folder_counters(self):
        async with task_dict_lock:
            if not self.same_dir:
                self.same_dir = {
                    self.folder_name: {
                        "total": self.multi,
                        "tasks": {self.mid},
                    }
                }
                return
            if self.folder_name in self.same_dir:
                self.same_dir[self.folder_name]["tasks"].add(self.mid)
            else:
                self.same_dir[self.folder_name] = {
                    "total": self.multi,
                    "tasks": {self.mid},
                }
            self._decrement_other_folders(self.folder_name)

    async def _decrement_all_folder_totals(self):
        async with task_dict_lock:
            for fd_name in self.same_dir:
                self.same_dir[fd_name]["total"] -= 1

    async def _resolve_link_from_reply(self):
        if not self.link and self.message.reply_to_message:
            self.link = self.message.reply_to_message.text.split("\n", 1)[0].strip()

    @staticmethod
    def _parse_custom_options(raw_options):
        try:
            return eval(raw_options) if raw_options else {}
        except Exception as e:
            LOGGER.error(e)
            return {}

    def _build_yt_options(self, opt):
        qual = ""
        options = {"usenetrc": True, "cookiefile": "cookies.txt"}
        if opt:
            for key, value in opt.items():
                if key in ["postprocessors", "download_ranges"]:
                    continue
                if key == "format" and not self.select:
                    qual = value
                options[key] = value
        options["playlist_items"] = "0"
        return options, qual

    async def _extract_yt_result(self, options, input_list):
        try:
            return await sync_to_async(extract_info, self.link, options)
        except Exception as e:
            msg = str(e).replace("<", " ").replace(">", " ")
            await send_message(self.message, f"{self.tag} {msg}")
            await self.remove_from_same_dir()
            return None
        finally:
            await self.run_multi(input_list, YtDlp)

    async def _initialize_event_context(self, text, input_list):
        """Initialize event context and parse arguments."""
        self.mid = self.message.id
        self.user = self.message.from_user or self.message.sender_chat
        self.user_id = self.user.id if self.user else None
        self.user_dict = user_data.get(self.user_id, {}) if self.user_id else {}
        
        args = self._default_args()
        arg_parser(input_list[1:], args)
        
        try:
            self.multi = int(args["-i"])
        except Exception:
            self.multi = 0
        
        self._apply_parsed_args(args)
        opt = self._parse_custom_options(args["-opt"])
        return args, opt

    async def _handle_bulk_setup(self, args, input_list):
        """Handle bulk download setup if needed."""
        is_bulk, bulk_start, bulk_end = self._parse_bulk_range(args["-b"])
        if is_bulk:
            await self.init_bulk(input_list, bulk_start, bulk_end, YtDlp)
            return True
        
        await self._update_same_dir_counters()
        if len(self.bulk) != 0:
            del self.bulk[0]
        return False

    async def _prepare_download_path_and_options(self, text, opt):
        """Prepare download path and resolve options."""
        path = f"{self.dir}{self.folder_name}"
        await self.get_tag(text)
        opt = opt or self.user_dict.get("YT_DLP_OPTIONS") or Config.YT_DLP_OPTIONS
        return path, opt

    async def _validate_and_prepare_link(self):
        """Validate URL and handle special cases like mdisk."""
        await self._resolve_link_from_reply()
        
        if not is_url(self.link):
            await send_message(
                self.message, COMMAND_USAGE["yt"][0], COMMAND_USAGE["yt"][1]
            )
            await self.remove_from_same_dir()
            return False
        
        if "mdisk.me" in self.link:
            self.name, self.link = await _mdisk(self.link, self.name)
        
        try:
            await self.before_start()
        except Exception as e:
            await send_message(self.message, e)
            await self.remove_from_same_dir()
            return False
        
        return True

    async def _get_quality_selection(self, result, qual):
        """Get quality selection from user if needed."""
        if not qual:
            qual = await YtSelection(self).get_quality(result)
            if qual is None:
                await self.remove_from_same_dir()
                return None
        return qual

    async def new_event(self):
        text = self.message.text.split("\n")
        input_list = text[0].split(" ")
        
        args, opt = await self._initialize_event_context(text, input_list)
        
        if await self._handle_bulk_setup(args, input_list):
            return
        
        path, opt = await self._prepare_download_path_and_options(text, opt)
        
        if not await self._validate_and_prepare_link():
            return
        
        options, qual = self._build_yt_options(opt)
        result = await self._extract_yt_result(options, input_list)
        if result is None:
            return
        
        qual = await self._get_quality_selection(result, qual)
        if qual is None:
            return
        
        LOGGER.info(f"Downloading with YT-DLP: {self.link}")
        playlist = "entries" in result
        ydl = YoutubeDLHelper(self)
        await ydl.add_download(path, qual, playlist, opt)


async def ytdl(client, message):
    try:
        LOGGER.info(f"▶️ /ytdl command received from {message.from_user.id if message.from_user else 'unknown'}")
        await YtDlp(client, message).new_event()
    except Exception as e:
        LOGGER.error(f"❌ /ytdl handler error: {e}", exc_info=True)


async def ytdl_leech(client, message):
    try:
        LOGGER.info(f"▶️ /ytdlleech command received from {message.from_user.id if message.from_user else 'unknown'}")
        await YtDlp(client, message, is_leech=True).new_event()
    except Exception as e:
        LOGGER.error(f"❌ /ytdlleech handler error: {e}", exc_info=True)
