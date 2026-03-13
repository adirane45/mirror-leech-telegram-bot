from asyncio import sleep
from logging import getLogger
from os import path as ospath
from os import walk
from re import match as re_match
from re import sub as re_sub
from time import time

from aiofiles.os import path as aiopath
from aiofiles.os import remove, rename
from aioshutil import rmtree
from natsort import natsorted
from PIL import Image
from pyrogram.errors import BadRequest, FloodWait, RPCError
from pyrogram.types import InputMediaDocument, InputMediaPhoto, InputMediaVideo
from tenacity import RetryError, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ... import intervals
from ...core.config_manager import Config
from ...core.file_cache_manager import file_cache_manager
from ...core.telegram_manager import TgClient
from ..ext_utils.bot_utils import sync_to_async
from ..ext_utils.files_utils import get_base_name, get_mime_type, is_archive
from ..ext_utils.media_utils import (
    get_audio_thumbnail,
    get_document_type,
    get_media_info,
    get_multiple_frames_thumbnail,
    get_video_thumbnail,
)
from ..telegram_helper.message_utils import delete_message

LOGGER = getLogger(__name__)


class TelegramUploader:
    def __init__(self, listener, path):
        self._last_uploaded = 0
        self._processed_bytes = 0
        self._listener = listener
        self._path = path
        self._start_time = time()
        self._total_files = 0
        self._thumb = self._listener.thumb or f"thumbnails/{listener.user_id}.jpg"
        self._msgs_dict = {}
        self._corrupted = 0
        self._is_corrupted = False
        self._media_dict = {"videos": {}, "documents": {}}
        self._last_msg_in_group = False
        self._up_path = ""
        self._lprefix = ""
        self._media_group = False
        self._is_private = False
        self._sent_msg = None
        self._user_session = self._listener.user_transmission
        self._error = ""

    async def _upload_progress(self, current, _):
        if self._listener.is_cancelled:
            if self._user_session:
                TgClient.user.stop_transmission()
            else:
                self._listener.client.stop_transmission()
        chunk_size = current - self._last_uploaded
        self._last_uploaded = current
        self._processed_bytes += chunk_size

    async def _user_settings(self):
        self._media_group = self._listener.user_dict.get("MEDIA_GROUP") or (
            Config.MEDIA_GROUP
            if "MEDIA_GROUP" not in self._listener.user_dict
            else False
        )
        self._lprefix = self._listener.user_dict.get("LEECH_FILENAME_PREFIX") or (
            Config.LEECH_FILENAME_PREFIX
            if "LEECH_FILENAME_PREFIX" not in self._listener.user_dict
            else ""
        )
        if self._thumb != "none" and not await aiopath.exists(self._thumb):
            self._thumb = None

    async def _msg_to_reply(self):
        if self._listener.up_dest:
            msg = (
                self._listener.message.link
                if self._listener.is_super_chat
                else self._listener.message.text.lstrip("/")
            )
            try:
                if self._user_session:
                    self._sent_msg = await TgClient.user.send_message(
                        chat_id=self._listener.up_dest,
                        text=msg,
                        message_thread_id=self._listener.chat_thread_id,
                        disable_notification=True,
                    )
                else:
                    self._sent_msg = await self._listener.client.send_message(
                        chat_id=self._listener.up_dest,
                        text=msg,
                        message_thread_id=self._listener.chat_thread_id,
                        disable_notification=True,
                    )
                    self._is_private = self._sent_msg.chat.type.name == "PRIVATE"
            except Exception as e:
                await self._listener.on_upload_error(str(e))
                return False
        elif self._user_session:
            self._sent_msg = await TgClient.user.get_messages(
                chat_id=self._listener.message.chat.id, message_ids=self._listener.mid
            )
            if self._sent_msg is None:
                self._sent_msg = await TgClient.user.send_message(
                    chat_id=self._listener.message.chat.id,
                    text="Deleted Cmd Message! Don't delete the cmd message again!",
                    disable_notification=True,
                )
        else:
            self._sent_msg = self._listener.message
        return True

    async def _prepare_file(self, file_, dirpath):
        if self._lprefix:
            cap_mono = f"{self._lprefix} <code>{file_}</code>"
            self._lprefix = re_sub("<.*?>", "", self._lprefix)
            new_path = ospath.join(dirpath, f"{self._lprefix} {file_}")
            await rename(self._up_path, new_path)
            self._up_path = new_path
        else:
            cap_mono = f"<code>{file_}</code>"
        if len(file_) > 60:
            if is_archive(file_):
                name = get_base_name(file_)
                ext = file_.split(name, 1)[1]
            elif match := re_match(r".+(?=\..+\.0*\d+$)|.+(?=\.part\d+\..+$)", file_):
                name = match.group(0)
                ext = file_.split(name, 1)[1]
            elif len(fsplit := ospath.splitext(file_)) > 1:
                name = fsplit[0]
                ext = fsplit[1]
            else:
                name = file_
                ext = ""
            extn = len(ext)
            remain = 60 - extn
            name = name[:remain]
            new_path = ospath.join(dirpath, f"{name}{ext}")
            await rename(self._up_path, new_path)
            self._up_path = new_path
        return cap_mono

    def _get_input_media(self, subkey, key):
        rlist = []
        for msg in self._media_dict[key][subkey]:
            if key == "videos":
                input_media = InputMediaVideo(
                    media=msg.video.file_id, caption=msg.caption
                )
            else:
                input_media = InputMediaDocument(
                    media=msg.document.file_id, caption=msg.caption
                )
            rlist.append(input_media)
        return rlist

    async def _send_screenshots(self, dirpath, outputs):
        inputs = [
            InputMediaPhoto(ospath.join(dirpath, p), p.rsplit("/", 1)[-1])
            for p in outputs
        ]
        for i in range(0, len(inputs), 10):
            batch = inputs[i : i + 10]
            self._sent_msg = (
                await self._sent_msg.reply_media_group(
                    media=batch,
                    disable_notification=True,
                )
            )[-1]

    def _extract_message_file_info(self, message):
        if message is None:
            return None, None, None
        if message.document:
            return message.document.file_id, message.document.file_unique_id, "document"
        if message.video:
            return message.video.file_id, message.video.file_unique_id, "video"
        if message.audio:
            return message.audio.file_id, message.audio.file_unique_id, "audio"
        if message.photo:
            return message.photo.file_id, message.photo.file_unique_id, "photo"
        if message.animation:
            return message.animation.file_id, message.animation.file_unique_id, "animation"
        return None, None, None

    async def _send_cached_media(self, cached_entry, cap_mono):
        file_id = cached_entry.get("file_id")
        if not file_id:
            return False
        file_type = cached_entry.get("file_type")
        try:
            if file_type == "video":
                self._sent_msg = await self._sent_msg.reply_video(
                    video=file_id,
                    caption=cap_mono,
                    disable_notification=True,
                )
            elif file_type == "audio":
                self._sent_msg = await self._sent_msg.reply_audio(
                    audio=file_id,
                    caption=cap_mono,
                    disable_notification=True,
                )
            elif file_type == "photo":
                self._sent_msg = await self._sent_msg.reply_photo(
                    photo=file_id,
                    caption=cap_mono,
                    disable_notification=True,
                )
            elif file_type == "animation":
                self._sent_msg = await self._sent_msg.reply_animation(
                    animation=file_id,
                    caption=cap_mono,
                    disable_notification=True,
                )
            else:
                self._sent_msg = await self._sent_msg.reply_document(
                    document=file_id,
                    caption=cap_mono,
                    disable_notification=True,
                )
            return True
        except Exception as exc:
            LOGGER.debug(f"Cached send failed: {exc}")
            return False

    async def _store_cache_entry(self, hashes, size, file_name):
        file_id, file_unique_id, file_type = self._extract_message_file_info(
            self._sent_msg
        )
        if not file_id or not file_unique_id or not file_type:
            return
        mime_type = get_mime_type(self._up_path)
        await file_cache_manager.store_entry(
            hashes=hashes,
            size=size,
            file_id=file_id,
            file_unique_id=file_unique_id,
            file_type=file_type,
            mime_type=mime_type,
            file_name=file_name,
        )

    async def _send_media_group(self, subkey, key, msgs):
        for index, msg in enumerate(msgs):
            if self._listener.hybrid_leech or not self._user_session:
                msgs[index] = await self._listener.client.get_messages(
                    chat_id=msg[0], message_ids=msg[1]
                )
            else:
                msgs[index] = await TgClient.user.get_messages(
                    chat_id=msg[0], message_ids=msg[1]
                )
        msgs_list = await msgs[0].reply_to_message.reply_media_group(
            media=self._get_input_media(subkey, key),
            disable_notification=True,
        )
        for msg in msgs:
            if msg.link in self._msgs_dict:
                del self._msgs_dict[msg.link]
            await delete_message(msg)
        del self._media_dict[key][subkey]
        if self._listener.is_super_chat or self._listener.up_dest:
            for m in msgs_list:
                self._msgs_dict[m.link] = m.caption
        self._sent_msg = msgs_list[-1]

    def _should_track_sent_link(self):
        return (
            not self._is_corrupted
            and (self._listener.is_super_chat or self._listener.up_dest)
            and not self._is_private
        )

    async def _flush_pending_groups_for_path(self, f_path):
        if not self._last_msg_in_group:
            return
        group_lists = [x for v in self._media_dict.values() for x in v.keys()]
        match = re_match(r".+(?=\.0*\d+$)|.+(?=\.part\d+\..+$)", f_path)
        if match and match.group(0) in group_lists:
            return
        for key, value in list(self._media_dict.items()):
            for subkey, msgs in list(value.items()):
                if len(msgs) > 1:
                    await self._send_media_group(subkey, key, msgs)

    async def _flush_all_pending_groups(self):
        for key, value in list(self._media_dict.items()):
            for subkey, msgs in list(value.items()):
                if len(msgs) > 1:
                    try:
                        await self._send_media_group(subkey, key, msgs)
                    except Exception as e:
                        LOGGER.info(
                            f"While sending media group at the end of task. Error: {e}"
                        )

    async def _refresh_session_message(self, f_size):
        if not (self._listener.hybrid_leech and self._listener.user_transmission):
            return
        self._user_session = f_size > 2097152000
        if self._user_session:
            self._sent_msg = await TgClient.user.get_messages(
                chat_id=self._sent_msg.chat.id,
                message_ids=self._sent_msg.id,
            )
            return
        self._sent_msg = await self._listener.client.get_messages(
            chat_id=self._sent_msg.chat.id,
            message_ids=self._sent_msg.id,
        )

    async def _try_cached_upload(self, cap_mono):
        cache_payload = await file_cache_manager.prepare_hashes(self._up_path)
        if not cache_payload:
            return None, False
        hashes, size = cache_payload
        cached_entry = await file_cache_manager.get_cached_entry(hashes, size)
        if not cached_entry:
            return cache_payload, False
        if await self._send_cached_media(cached_entry, cap_mono):
            if self._should_track_sent_link():
                self._msgs_dict[self._sent_msg.link] = ospath.basename(self._up_path)
            await remove(self._up_path)
            await sleep(1)
            return cache_payload, True
        return cache_payload, False

    async def _validate_file_path(self, f_path):
        """Validate file existence and size."""
        if not await aiopath.exists(f_path):
            if intervals["stopAll"]:
                return "stop", None
            LOGGER.error(f"{f_path} not exists! Continue uploading!")
            return "continue", None
        
        f_size = await aiopath.getsize(f_path)
        self._total_files += 1
        
        if f_size == 0:
            LOGGER.error(
                f"{f_path} size is zero, telegram don't upload zero size files"
            )
            self._corrupted += 1
            return "continue", None
        
        return None, f_size

    async def _handle_cache_upload(self, cap_mono, file_):
        """Try to upload from cache if available."""
        cache_payload, uploaded_from_cache = await self._try_cached_upload(cap_mono)
        if uploaded_from_cache:
            return True, None
        return False, cache_payload

    async def _perform_actual_upload(self, cap_mono, file_, f_path, f_size):
        """Perform the actual file upload."""
        await self._flush_pending_groups_for_path(f_path)
        await self._refresh_session_message(f_size)
        
        self._last_msg_in_group = False
        self._last_uploaded = 0
        await self._upload_file(cap_mono, file_, f_path)

    async def _post_upload_processing(self, cache_payload, file_):
        """Handle post-upload tasks like caching and link tracking."""
        if cache_payload and not self._is_corrupted:
            hashes, size = cache_payload
            await self._store_cache_entry(hashes, size, file_)
        
        if self._should_track_sent_link():
            self._msgs_dict[self._sent_msg.link] = file_
        
        await sleep(1)

    async def _cleanup_uploaded_file(self):
        """Clean up the uploaded file if it still exists."""
        if (
            not self._listener.is_cancelled
            and self._up_path
            and await aiopath.exists(self._up_path)
        ):
            await remove(self._up_path)

    async def _upload_single_file(self, file_, dirpath):
        self._error = ""
        self._up_path = f_path = ospath.join(dirpath, file_)
        
        status, f_size = await self._validate_file_path(f_path)
        if status:
            return status
        
        try:
            if self._listener.is_cancelled:
                return "stop"
            
            cap_mono = await self._prepare_file(file_, dirpath)
            cached, cache_payload = await self._handle_cache_upload(cap_mono, file_)
            if cached:
                return "continue"
            
            await self._perform_actual_upload(cap_mono, file_, f_path, f_size)
            
            if self._listener.is_cancelled:
                return "stop"
            
            await self._post_upload_processing(cache_payload, file_)
            return "continue"
        except Exception as err:
            if isinstance(err, RetryError):
                LOGGER.info(f"Total Attempts: {err.last_attempt.attempt_number}")
                err = err.last_attempt.exception()
            LOGGER.error(f"{err}. Path: {self._up_path}")
            self._error = str(err)
            self._corrupted += 1
            if self._listener.is_cancelled:
                return "stop"
            return "continue"
        finally:
            await self._cleanup_uploaded_file()

    async def upload(self):
        await self._user_settings()
        res = await self._msg_to_reply()
        if not res:
            return
        
        for dirpath, _, files in natsorted(await sync_to_async(walk, self._path)):
            outcome = await self._process_directory(dirpath, files)
            if outcome == "stop":
                return
        
        await self._finalize_upload()

    async def _process_directory(self, dirpath, files):
        if dirpath.strip().endswith("/yt-dlp-thumb"):
            return None
        if dirpath.strip().endswith("_mltbss"):
            await self._send_screenshots(dirpath, files)
            await rmtree(dirpath, ignore_errors=True)
            return None
        
        for file_ in natsorted(files):
            outcome = await self._upload_single_file(file_, dirpath)
            if outcome == "stop":
                return "stop"
        return None

    async def _finalize_upload(self):
        await self._flush_all_pending_groups()
        if self._listener.is_cancelled:
            return
        if self._total_files == 0:
            await self._listener.on_upload_error(
                "No files to upload. In case you have filled EXCLUDED/INCLUDED EXTENSIONS, then check if all files have those extensions or not."
            )
            return
        if self._total_files <= self._corrupted:
            await self._listener.on_upload_error(
                f"Files Corrupted or unable to upload. {self._error or 'Check logs!'}"
            )
            return
        LOGGER.info(f"Leech Completed: {self._listener.name}")
        await self._listener.on_upload_complete(
            None, self._msgs_dict, self._total_files, self._corrupted
        )

    async def _resolve_thumb(self, file, is_video, is_audio, is_image):
        thumb = self._thumb
        if not is_image and thumb is None:
            file_name = ospath.splitext(file)[0]
            thumb_path = f"{self._path}/yt-dlp-thumb/{file_name}.jpg"
            if await aiopath.isfile(thumb_path):
                return thumb_path
            alt_thumb = thumb_path.replace("/yt-dlp-thumb", "")
            if await aiopath.isfile(alt_thumb):
                return alt_thumb
            if is_audio and not is_video:
                return await get_audio_thumbnail(self._up_path)
        return thumb

    async def _reply_document(self, cap_mono, thumb):
        if self._listener.is_cancelled:
            return
        if thumb == "none":
            thumb = None
        self._sent_msg = await self._sent_msg.reply_document(
            document=self._up_path,
            thumb=thumb,
            caption=cap_mono,
            force_document=True,
            disable_notification=True,
            progress=self._upload_progress,
        )

    async def _reply_video(self, cap_mono, thumb):
        duration = (await get_media_info(self._up_path))[0]
        if thumb is None and self._listener.thumbnail_layout:
            thumb = await get_multiple_frames_thumbnail(
                self._up_path,
                self._listener.thumbnail_layout,
                self._listener.screen_shots,
            )
        if thumb is None:
            thumb = await get_video_thumbnail(self._up_path, duration)
        if thumb is not None and thumb != "none":
            with Image.open(thumb) as img:
                width, height = img.size
        else:
            width, height = 480, 320
        if self._listener.is_cancelled:
            return
        if thumb == "none":
            thumb = None
        self._sent_msg = await self._sent_msg.reply_video(
            video=self._up_path,
            caption=cap_mono,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb,
            supports_streaming=True,
            disable_notification=True,
            progress=self._upload_progress,
        )

    async def _reply_audio(self, cap_mono, thumb):
        duration, artist, title = await get_media_info(self._up_path)
        if self._listener.is_cancelled:
            return
        if thumb == "none":
            thumb = None
        self._sent_msg = await self._sent_msg.reply_audio(
            audio=self._up_path,
            caption=cap_mono,
            duration=duration,
            performer=artist,
            title=title,
            thumb=thumb,
            disable_notification=True,
            progress=self._upload_progress,
        )

    async def _reply_photo(self, cap_mono):
        if self._listener.is_cancelled:
            return
        self._sent_msg = await self._sent_msg.reply_photo(
            photo=self._up_path,
            caption=cap_mono,
            disable_notification=True,
            progress=self._upload_progress,
        )

    async def _send_with_detected_type(
        self, cap_mono, file, o_path, force_document=False
    ):
        is_video, is_audio, is_image = await get_document_type(self._up_path)
        thumb = await self._resolve_thumb(file, is_video, is_audio, is_image)

        upload_as_document = (
            self._listener.as_doc
            or force_document
            or (not is_video and not is_audio and not is_image)
        )

        if upload_as_document:
            if is_video and thumb is None:
                thumb = await get_video_thumbnail(self._up_path, None)
            await self._reply_document(cap_mono, thumb)
            return "documents", thumb
        if is_video:
            await self._reply_video(cap_mono, thumb)
            return "videos", thumb
        if is_audio:
            await self._reply_audio(cap_mono, thumb)
            return "audios", thumb
        await self._reply_photo(cap_mono)
        return "photos", thumb

    async def _track_media_group(self, o_path):
        if (
            self._listener.is_cancelled
            or not self._media_group
            or not (self._sent_msg.video or self._sent_msg.document)
        ):
            return
        key = "documents" if self._sent_msg.document else "videos"
        match = re_match(r".+(?=\.0*\d+$)|.+(?=\.part\d+\..+$)", o_path)
        if not match:
            return
        pname = match.group(0)
        if pname in self._media_dict[key].keys():
            self._media_dict[key][pname].append([self._sent_msg.chat.id, self._sent_msg.id])
        else:
            self._media_dict[key][pname] = [[self._sent_msg.chat.id, self._sent_msg.id]]
        msgs = self._media_dict[key][pname]
        if len(msgs) == 10:
            await self._send_media_group(pname, key, msgs)
            return
        self._last_msg_in_group = True

    async def _cleanup_generated_thumb(self, thumb):
        if self._thumb is None and thumb is not None and await aiopath.exists(thumb):
            await remove(thumb)

    async def _ensure_thumb_available(self):
        if (
            self._thumb is not None
            and not await aiopath.exists(self._thumb)
            and self._thumb != "none"
        ):
            self._thumb = None

    async def _send_upload_and_track(self, cap_mono, file, o_path, force_document):
        key, thumb = await self._send_with_detected_type(
            cap_mono,
            file,
            o_path,
            force_document,
        )
        await self._track_media_group(o_path)
        await self._cleanup_generated_thumb(thumb)
        return key, thumb

    async def _retry_after_floodwait(self, flood_wait, cap_mono, file, o_path):
        LOGGER.warning(str(flood_wait))
        await sleep(flood_wait.value * 1.3)
        return await self._upload_file(cap_mono, file, o_path)

    async def _handle_upload_exception(self, err, key, cap_mono, file, o_path):
        err_type = "RPCError: " if isinstance(err, RPCError) else ""
        LOGGER.error(f"{err_type}{err}. Path: {self._up_path}")
        if isinstance(err, BadRequest) and key != "documents":
            LOGGER.error(f"Retrying As Document. Path: {self._up_path}")
            return await self._upload_file(cap_mono, file, o_path, True)
        raise err

    @retry(
        wait=wait_exponential(multiplier=2, min=4, max=8),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
    )
    async def _upload_file(self, cap_mono, file, o_path, force_document=False):
        await self._ensure_thumb_available()
        self._is_corrupted = False
        key = "documents"
        thumb = self._thumb
        try:
            key, thumb = await self._send_upload_and_track(
                cap_mono,
                file,
                o_path,
                force_document,
            )
        except FloodWait as f:
            await self._cleanup_generated_thumb(thumb)
            return await self._retry_after_floodwait(f, cap_mono, file, o_path)
        except Exception as err:
            await self._cleanup_generated_thumb(thumb)
            return await self._handle_upload_exception(err, key, cap_mono, file, o_path)

    @property
    def speed(self):
        try:
            return self._processed_bytes / (time() - self._start_time)
        except:
            return 0

    @property
    def processed_bytes(self):
        return self._processed_bytes

    async def cancel_task(self):
        self._listener.is_cancelled = True
        LOGGER.info(f"Cancelling Upload: {self._listener.name}")
        await self._listener.on_upload_error("your upload has been stopped!")
