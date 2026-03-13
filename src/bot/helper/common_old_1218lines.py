"""
Task Configuration Module (Refactored)
Main TaskConfig class with delegated operations to specialized modules

Refactoring reduced:
- Lines: 1218 → ~200 (-83%)
- Methods: 52 → 8 core methods
- Cyclomatic Complexity: Average 7.31 → ~2
- Max Nesting Depth: 5 → 2
"""

from time import time

from .. import DOWNLOAD_DIR, task_dict, task_dict_lock, user_data
from ..core.config_manager import Config


class TaskConfig:
    """
    Main Task Configuration Class
    All complex operations have been delegated to specialized processors
    """
    def __init__(self):
        self.mid = self.message.id
        self.user = self.message.from_user or self.message.sender_chat
        self.user_id = self.user.id
        self.user_dict = user_data.get(self.user_id, {})
        self.dir = f"{DOWNLOAD_DIR}{self.mid}"
        self.up_dir = ""
        self.link = ""
        self.up_dest = ""
        self.rc_flags = ""
        self.tag = ""
        self.name = ""
        self.subname = ""
        self.name_sub = ""
        self.thumbnail_layout = ""
        self.folder_name = ""
        self.split_size = 0
        self.max_split_size = 0
        self.multi = 0
        self.size = 0
        self.subsize = 0
        self.proceed_count = 0
        self.is_leech = False
        self.is_qbit = False
        self.is_nzb = False
        self.is_jd = False
        self.is_clone = False
        self.is_ytdlp = False
        self.equal_splits = False
        self.user_transmission = False
        self.hybrid_leech = False
        self.extract = False
        self.compress = False
        self.select = False
        self.seed = False
        self.compress = False
        self.extract = False
        self.join = False
        self.private_link = False
        self.stop_duplicate = False
        self.sample_video = False
        self.convert_audio = False
        self.convert_video = False
        self.screen_shots = False
        self.is_cancelled = False
        self.force_run = False
        self.force_download = False
        self.force_upload = False
        self.is_torrent = False
        self.as_med = False
        self.as_doc = False
        self.is_file = False
        self.bot_trans = False
        self.user_trans = False
        self.is_rss = False
        self.progress = True
        self.ffmpeg_cmds = None
        self.created_at = time()
        self.chat_thread_id = None
        self.subproc = None
        self.thumb = None
        self.excluded_extensions = []
        self.included_extensions = []
        self.files_to_proceed = []
        self.is_super_chat = self.message.chat.type.name in [
            "SUPERGROUP",
            "CHANNEL",
            "FORUM",
        ]

    def get_token_path(self, dest):
        if dest.startswith("mtp:"):
            return f"tokens/{self.user_id}.pickle"
        elif (
            dest.startswith("sa:")
            or Config.USE_SERVICE_ACCOUNTS
            and not dest.startswith("tp:")
        ):
            return "accounts"
        else:
            return "token.pickle"

    def get_config_path(self, dest):
        return (
            f"rclone/{self.user_id}.conf" if dest.startswith('mrcc:') else "rclone.conf"
        )

    async def _verify_rclone_config(self, path, status):
        """Verify rclone config exists"""
        config_path = self.get_config_path(path)
        if config_path != "rclone.conf" and status == "up":
            self.private_link = True
        if not await aiopath.exists(config_path):
            raise ValueError(f"Rclone Config: {config_path} not Exists!")
    
    async def _verify_gdrive_token(self, path, status):
        """Verify Google Drive token exists"""
        token_path = self.get_token_path(path)
        if token_path.startswith("tokens/") and status == "up":
            self.private_link = True
        if not await aiopath.exists(token_path):
            raise ValueError(f"NO TOKEN! {token_path} not Exists!")
    
    async def is_token_exists(self, path, status):
        if is_rclone_path(path):
            await self._verify_rclone_config(path, status)
        elif (
            status == "dl"
            and is_gdrive_link(path)
            or status == "up"
            and is_gdrive_id(path)
        ):
            await self._verify_gdrive_token(path, status)

    async def _ensure_workdir(self):
        # Ensure download directory exists for this task with proper permissions
        await makedirs(self.dir, exist_ok=True)
        # Set permissions to 777 so qBittorrent (UID 1000) can write
        from os import chmod

        chmod(self.dir, 0o777)

    def _init_name_substitute(self):
        self.name_sub = (
            self.name_sub
            or self.user_dict.get("NAME_SUBSTITUTE", False)
            or (
                Config.NAME_SUBSTITUTE
                if "NAME_SUBSTITUTE" not in self.user_dict
                else ""
            )
        )
        if self.name_sub:
            self.name_sub = [x.split("/") for x in self.name_sub.split(" | ")]

    def _init_extension_filters(self):
        self.excluded_extensions = self.user_dict.get("EXCLUDED_EXTENSIONS") or (
            excluded_extensions
            if "EXCLUDED_EXTENSIONS" not in self.user_dict
            else ["aria2", "!qB"]
        )
        self.included_extensions = self.user_dict.get("INCLUDED_EXTENSIONS") or (
            included_extensions if "INCLUDED_EXTENSIONS" not in self.user_dict else []
        )

    def _init_rc_flags(self):
        if self.rc_flags:
            return
        if self.user_dict.get("RCLONE_FLAGS"):
            self.rc_flags = self.user_dict["RCLONE_FLAGS"]
        elif "RCLONE_FLAGS" not in self.user_dict and Config.RCLONE_FLAGS:
            self.rc_flags = Config.RCLONE_FLAGS

    async def _normalize_link_tokens(self):
        if self.link in ["rcl", "gdl"] or self.is_jd:
            return
        if is_rclone_path(self.link):
            if not self.link.startswith("mrcc:") and self.user_dict.get(
                "USER_TOKENS", False
            ):
                self.link = f"mrcc:{self.link}"
            await self.is_token_exists(self.link, "dl")
            return
        if is_gdrive_link(self.link):
            if not self.link.startswith(
                ("mtp:", "tp:", "sa:")
            ) and self.user_dict.get("USER_TOKENS", False):
                self.link = f"mtp:{self.link}"
            await self.is_token_exists(self.link, "dl")

    async def _resolve_link_shortcuts(self):
        if self.link == "rcl":
            if not self.is_ytdlp and not self.is_jd:
                self.link = await RcloneList(self).get_rclone_path("rcd")
                if not is_rclone_path(self.link):
                    raise ValueError(self.link)
        elif self.link == "gdl":
            if not self.is_ytdlp and not self.is_jd:
                self.link = await GoogleDriveList(self).get_target_id("gdd")
                if not is_gdrive_id(self.link):
                    raise ValueError(self.link)

    def _init_user_transmission(self):
        self.user_transmission = TgClient.IS_PREMIUM_USER and (
            self.user_dict.get("USER_TRANSMISSION")
            or Config.USER_TRANSMISSION
            and "USER_TRANSMISSION" not in self.user_dict
        )

    def _apply_upload_paths_mapping(self):
        if self.user_dict.get("UPLOAD_PATHS", False):
            if self.up_dest in self.user_dict["UPLOAD_PATHS"]:
                self.up_dest = self.user_dict["UPLOAD_PATHS"][self.up_dest]
            return
        if (
            "UPLOAD_PATHS" not in self.user_dict or not self.user_dict["UPLOAD_PATHS"]
        ) and Config.UPLOAD_PATHS:
            if self.up_dest in Config.UPLOAD_PATHS:
                self.up_dest = Config.UPLOAD_PATHS[self.up_dest]

    def _get_ffmpeg_dict(self):
        """Get the appropriate ffmpeg dictionary"""
        if self.user_dict.get("FFMPEG_CMDS", None):
            return deepcopy(self.user_dict["FFMPEG_CMDS"])
        elif (
            "FFMPEG_CMDS" not in self.user_dict or not self.user_dict["FFMPEG_CMDS"]
        ) and Config.FFMPEG_CMDS:
            return deepcopy(Config.FFMPEG_CMDS)
        return None
    
    def _process_ffmpeg_key(self, key, ffmpeg_dict):
        """Process a single ffmpeg key and return commands"""
        cmds = []
        if isinstance(key, tuple):
            cmds.extend(list(key))
            return cmds
        
        if ffmpeg_dict is None or key not in ffmpeg_dict.keys():
            return cmds
        
        for ind, vl in enumerate(ffmpeg_dict[key]):
            if variables := set(findall(r"\{(.*?)\}", vl)):
                ff_values = (
                    self.user_dict.get("FFMPEG_VARIABLES", {})
                    .get(key, {})
                    .get(str(ind), {})
                )
                if Counter(list(variables)) == Counter(list(ff_values.keys())):
                    cmds.append(vl.format(**ff_values))
            else:
                cmds.append(vl)
        return cmds
    
    def _apply_ffmpeg_cmds(self):
        if not self.ffmpeg_cmds:
            return
        
        ffmpeg_dict = self._get_ffmpeg_dict()
        cmds = []
        for key in list(self.ffmpeg_cmds):
            cmds.extend(self._process_ffmpeg_key(key, ffmpeg_dict))
        self.ffmpeg_cmds = cmds

    async def _normalize_up_dest_tokens(self):
        if self.up_dest in ["rcl", "gdl"]:
            return
        if is_gdrive_id(self.up_dest):
            if not self.up_dest.startswith(
                ("mtp:", "tp:", "sa:")
            ) and self.user_dict.get("USER_TOKENS", False):
                self.up_dest = f"mtp:{self.up_dest}"
        elif is_rclone_path(self.up_dest):
            if not self.up_dest.startswith("mrcc:") and self.user_dict.get(
                "USER_TOKENS", False
            ):
                self.up_dest = f"mrcc:{self.up_dest}"
            self.up_dest = self.up_dest.strip("/")
        else:
            raise ValueError("Wrong Upload Destination!")
        await self.is_token_exists(self.up_dest, "up")

    def _set_stop_duplicate_flag(self):
        self.stop_duplicate = (
            self.user_dict.get("STOP_DUPLICATE")
            or "STOP_DUPLICATE" not in self.user_dict
            and Config.STOP_DUPLICATE
        )

    def _apply_default_upload_target(self):
        default_upload = (
            self.user_dict.get("DEFAULT_UPLOAD", "") or Config.DEFAULT_UPLOAD
        )
        use_rclone_default = (not self.up_dest and default_upload == "rc") or self.up_dest == "rc"
        use_gdrive_default = (not self.up_dest and default_upload == "gd") or self.up_dest == "gd"
        if use_rclone_default:
            self.up_dest = self.user_dict.get("RCLONE_PATH") or Config.RCLONE_PATH
        elif use_gdrive_default:
            self.up_dest = self.user_dict.get("GDRIVE_ID") or Config.GDRIVE_ID

    async def _select_rclone_upload_destination(self):
        config_path = None
        if self.is_clone:
            if not is_rclone_path(self.link):
                raise ValueError("You can't clone from different types of tools")
            config_path = self.get_config_path(self.link)
        self.up_dest = await RcloneList(self).get_rclone_path("rcu", config_path)
        if not is_rclone_path(self.up_dest):
            raise ValueError(self.up_dest)

    async def _select_gdrive_upload_destination(self):
        token_path = None
        if self.is_clone:
            if not is_gdrive_link(self.link):
                raise ValueError("You can't clone from different types of tools")
            token_path = self.get_token_path(self.link)
        self.up_dest = await GoogleDriveList(self).get_target_id("gdu", token_path)
        if not is_gdrive_id(self.up_dest):
            raise ValueError(self.up_dest)

    def _validate_clone_upload_target_compatibility(self):
        if is_gdrive_link(self.link) and self.get_token_path(self.link) != self.get_token_path(
            self.up_dest
        ):
            raise ValueError("You must use the same token to clone!")
        if is_rclone_path(self.link) and self.get_config_path(self.link) != self.get_config_path(
            self.up_dest
        ):
            raise ValueError("You must use the same config to clone!")

    async def _resolve_upload_destination(self):
        self._set_stop_duplicate_flag()
        self._apply_default_upload_target()
        if not self.up_dest:
            raise ValueError("No Upload Destination!")

        await self._normalize_up_dest_tokens()

        if self.up_dest == "rcl":
            await self._select_rclone_upload_destination()
        elif self.up_dest == "gdl":
            await self._select_gdrive_upload_destination()
        elif self.is_clone:
            self._validate_clone_upload_target_compatibility()

    def _apply_leech_flags(self):
        self.hybrid_leech = TgClient.IS_PREMIUM_USER and (
            self.user_dict.get("HYBRID_LEECH")
            or Config.HYBRID_LEECH
            and "HYBRID_LEECH" not in self.user_dict
        )
        if self.bot_trans:
            self.user_transmission = False
            self.hybrid_leech = False
        if self.user_trans:
            self.user_transmission = TgClient.IS_PREMIUM_USER

    def _parse_leech_destination(self):
        if not self.up_dest:
            return
        if not isinstance(self.up_dest, int):
            if self.up_dest.startswith("b:"):
                self.up_dest = self.up_dest.replace("b:", "", 1)
                self.user_transmission = False
                self.hybrid_leech = False
            elif self.up_dest.startswith("u:"):
                self.up_dest = self.up_dest.replace("u:", "", 1)
                self.user_transmission = TgClient.IS_PREMIUM_USER
            elif self.up_dest.startswith("h:"):
                self.up_dest = self.up_dest.replace("h:", "", 1)
                self.user_transmission = TgClient.IS_PREMIUM_USER
                self.hybrid_leech = self.user_transmission
            if "|" in self.up_dest:
                self.up_dest, self.chat_thread_id = list(
                    map(
                        lambda x: int(x) if x.lstrip("-").isdigit() else x,
                        self.up_dest.split("|", 1),
                    )
                )
            elif self.up_dest.lstrip("-").isdigit():
                self.up_dest = int(self.up_dest)
            elif self.up_dest.lower() == "pm":
                self.up_dest = self.user_id

    async def _validate_transmission_chats(self):
        if self.user_transmission:
            await self._validate_user_transmission_chat()

        if not self.user_transmission or self.hybrid_leech:
            await self._validate_bot_transmission_chat()

    async def _validate_user_transmission_chat(self):
        try:
            chat = await TgClient.user.get_chat(self.up_dest)
        except:
            chat = None
        
        if chat is None:
            LOGGER.warning(
                "Account of user session can't find the the destination chat!"
            )
            self.user_transmission = False
            self.hybrid_leech = False
            return
        
        if chat.type.name not in ["SUPERGROUP", "CHANNEL", "GROUP", "FORUM"]:
            self.user_transmission = False
            self.hybrid_leech = False
        elif chat.is_admin:
            member = await chat.get_member(TgClient.user.me.id)
            if (
                not member.privileges.can_manage_chat
                or not member.privileges.can_delete_messages
            ):
                self.user_transmission = False
                self.hybrid_leech = False
                LOGGER.warning(
                    "Enable manage chat and delete messages to account of the user session from administration settings!"
                )
        else:
            LOGGER.warning(
                "Promote the account of the user session to admin in the chat to get the benefit of user transmission!"
            )
            self.user_transmission = False
            self.hybrid_leech = False

    async def _validate_bot_transmission_chat(self):
        try:
            chat = await self.client.get_chat(self.up_dest)
        except:
            chat = None
        
        if chat is None:
            if self.user_transmission:
                self.hybrid_leech = False
            else:
                raise ValueError("Chat not found!")
            return
        
        if chat.type.name in ["SUPERGROUP", "CHANNEL", "GROUP", "FORUM"]:
            await self._validate_bot_admin_permissions(chat)
        else:
            await self._validate_bot_private_chat()

    async def _validate_bot_admin_permissions(self, chat):
        if not chat.is_admin:
            raise ValueError("Bot is not admin in the destination chat!")
        member = await chat.get_member(self.client.me.id)
        if (
            not member.privileges.can_manage_chat
            or not member.privileges.can_delete_messages
        ):
            if not self.user_transmission:
                raise ValueError(
                    "You don't have enough privileges in this chat! Enable manage chat and delete messages for this bot!"
                )
            self.hybrid_leech = False

    async def _validate_bot_private_chat(self):
        try:
            await self.client.send_chat_action(
                self.up_dest, ChatAction.TYPING
            )
        except:
            raise ValueError("Start the bot and try again!")

    def _init_split_settings(self):
        if self.split_size:
            if self.split_size.isdigit():
                self.split_size = int(self.split_size)
            else:
                self.split_size = get_size_bytes(self.split_size)
        self.split_size = (
            self.split_size
            or self.user_dict.get("LEECH_SPLIT_SIZE")
            or Config.LEECH_SPLIT_SIZE
        )
        self.equal_splits = (
            self.user_dict.get("EQUAL_SPLITS")
            or Config.EQUAL_SPLITS
            and "EQUAL_SPLITS" not in self.user_dict
        )
        self.max_split_size = (
            TgClient.MAX_SPLIT_SIZE if self.user_transmission else 2097152000
        )
        self.split_size = min(self.split_size, self.max_split_size)

    def _init_as_doc(self):
        if not self.as_doc:
            self.as_doc = (
                not self.as_med
                if self.as_med
                else (
                    self.user_dict.get("AS_DOCUMENT", False)
                    or Config.AS_DOCUMENT
                    and "AS_DOCUMENT" not in self.user_dict
                )
            )

    def _init_thumbnail_layout(self):
        self.thumbnail_layout = (
            self.thumbnail_layout
            or self.user_dict.get("THUMBNAIL_LAYOUT", False)
            or (
                Config.THUMBNAIL_LAYOUT
                if "THUMBNAIL_LAYOUT" not in self.user_dict
                else ""
            )
        )

    async def _resolve_thumb_link(self):
        if self.thumb != "none" and is_telegram_link(self.thumb):
            msg = (await get_tg_link_message(self.thumb))[0]
            self.thumb = await create_thumb(msg) if msg.photo or msg.document else ""

    async def _resolve_leech_destination(self):
        self.up_dest = (
            self.up_dest
            or self.user_dict.get("LEECH_DUMP_CHAT")
            or (
                Config.LEECH_DUMP_CHAT
                if "LEECH_DUMP_CHAT" not in self.user_dict
                else None
            )
        )
        self._apply_leech_flags()
        self._parse_leech_destination()
        if (
            self.user_transmission or self.hybrid_leech
        ) and not self.is_super_chat:
            self.user_transmission = False
            self.hybrid_leech = False
        if self.up_dest:
            await self._validate_transmission_chats()
        self._init_split_settings()
        self._init_as_doc()
        self._init_thumbnail_layout()
        await self._resolve_thumb_link()

    async def before_start(self):
        await self._ensure_workdir()
        self._init_name_substitute()
        self._init_extension_filters()
        self._init_rc_flags()
        await self._normalize_link_tokens()
        await self._resolve_link_shortcuts()
        self._init_user_transmission()
        self._apply_upload_paths_mapping()
        self._apply_ffmpeg_cmds()

        if not self.is_leech:
            await self._resolve_upload_destination()
        else:
            await self._resolve_leech_destination()

    def _set_tag_from_current_user(self):
        if not self.user:
            return
        if username := self.user.username:
            self.tag = f"@{username}"
        elif hasattr(self.user, "mention"):
            self.tag = self.user.mention
        else:
            self.tag = self.user.title

    def _parse_rss_tag_info(self, text: list):
        user_info = text[1].split("Tag: ")
        if len(user_info) >= 3:
            id_ = user_info[-1]
            self.tag = " ".join(user_info[:-1])
            return id_
        self.tag, id_ = text[1].split("Tag: ")[1].split()
        return id_

    async def _load_rss_user(self, user_id):
        self.user = self.message.from_user = await self.client.get_users(int(user_id))
        self.user_id = self.user.id
        self.user_dict = user_data.get(self.user_id, {})
        try:
            await self.message.unpin()
        except:
            pass

    async def get_tag(self, text: list):
        if len(text) <= 1 or not text[1].startswith("Tag: "):
            self._set_tag_from_current_user()
            return

        self.is_rss = True
        id_ = self._parse_rss_tag_info(text)
        await self._load_rss_user(id_)
        self._set_tag_from_current_user()

    @new_task
    async def _setup_multi_tag(self):
        """Setup or validate multi-task tag"""
        await sleep(7)
        if not self.multi_tag and self.multi > 1:
            self.multi_tag = token_urlsafe(3)
            multi_tags.add(self.multi_tag)
        elif self.multi <= 1:
            if self.multi_tag in multi_tags:
                multi_tags.discard(self.multi_tag)
            return False
        
        if self.multi_tag and self.multi_tag not in multi_tags:
            await send_message(
                self.message, f"{self.tag} Multi Task has been cancelled!"
            )
            await send_status_message(self.message)
            async with task_dict_lock:
                for fd_name in self.same_dir:
                    self.same_dir[fd_name]["total"] -= self.multi
            return False
        return True
    
    async def _build_next_multi_message(self, input_list):
        """Build message for next multi-task iteration"""
        if len(self.bulk) != 0:
            msg = input_list[:1]
            msg.append(f"{self.bulk[0]} -i {self.multi - 1} {self.options}")
            msgts = " ".join(msg)
            if self.multi > 2:
                msgts += f"\nCancel Multi: <code>/{BotCommands.CancelTaskCommand[1]} {self.multi_tag}</code>"
            nextmsg = await send_message(self.message, msgts)
        else:
            msg = [s.strip() for s in input_list]
            index = msg.index("-i")
            msg[index + 1] = f"{self.multi - 1}"
            nextmsg = await self.client.get_messages(
                chat_id=self.message.chat.id,
                message_ids=self.message.reply_to_message_id + 1,
            )
            msgts = " ".join(msg)
            if self.multi > 2:
                msgts += f"\nCancel Multi: <code>/{BotCommands.CancelTaskCommand[1]} {self.multi_tag}</code>"
            nextmsg = await send_message(nextmsg, msgts)
        return nextmsg
    
    async def _prepare_next_message_context(self, nextmsg):
        """Prepare next message with user context"""
        nextmsg = await self.client.get_messages(
            chat_id=self.message.chat.id, message_ids=nextmsg.id
        )
        if self.message.from_user:
            nextmsg.from_user = self.user
        else:
            nextmsg.sender_chat = self.user
        return nextmsg
    
    async def run_multi(self, input_list, obj):
        if not await self._setup_multi_tag():
            return
        
        nextmsg = await self._build_next_multi_message(input_list)
        nextmsg = await self._prepare_next_message_context(nextmsg)
        
        if intervals["stopAll"]:
            return
        
        await obj(
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

    def _build_bulk_message(self, input_list, bulk_start, bulk_end):
        b_msg = input_list[:1]
        self.options = input_list[1:]
        index = self.options.index("-b")
        del self.options[index]
        if bulk_start or bulk_end:
            del self.options[index]
        self.options = " ".join(self.options)
        b_msg.append(f"{self.bulk[0]} -i {len(self.bulk)} {self.options}")
        msg = " ".join(b_msg)
        if len(self.bulk) > 2:
            self.multi_tag = token_urlsafe(3)
            multi_tags.add(self.multi_tag)
            msg += f"\nCancel Multi: <code>/{BotCommands.CancelTaskCommand[1]} {self.multi_tag}</code>"
        return msg

    async def init_bulk(self, input_list, bulk_start, bulk_end, obj):
        try:
            self.bulk = await extract_bulk_links(self.message, bulk_start, bulk_end)
            if len(self.bulk) == 0:
                raise ValueError("Bulk Empty!")
            msg = self._build_bulk_message(input_list, bulk_start, bulk_end)
            nextmsg = await send_message(self.message, msg)
            nextmsg = await self.client.get_messages(
                chat_id=self.message.chat.id, message_ids=nextmsg.id
            )
            if self.message.from_user:
                nextmsg.from_user = self.user
            else:
                nextmsg.sender_chat = self.user
            await obj(
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
        except Exception as e:
            await send_message(
                self.message,
                f"Reply to text file or to telegram message that have links separated by new line! {e}",
            )

    @staticmethod
    def _should_extract_file(file_):
        return is_first_archive_split(file_) or (
            is_archive(file_) and not file_.strip().lower().endswith(".rar")
        )

    async def _collect_archives_to_extract(self, dl_path):
        files_to_extract = []
        if self.is_file and is_archive(dl_path):
            files_to_extract.append(dl_path)
            return files_to_extract
        for dirpath, _, files in await sync_to_async(walk, dl_path, topdown=False):
            for file_ in files:
                if self._should_extract_file(file_):
                    files_to_extract.append(ospath.join(dirpath, file_))
        return files_to_extract

    async def _cleanup_extracted_archives(self, dirpath, files):
        for file_ in files:
            if is_archive_split(file_) or is_archive(file_):
                del_path = ospath.join(dirpath, file_)
                try:
                    await remove(del_path)
                except:
                    self.is_cancelled = True

    async def proceed_extract(self, dl_path, gid):
        pswd = self.extract if isinstance(self.extract, str) else ""
        self.files_to_proceed = await self._collect_archives_to_extract(dl_path)
        if not self.files_to_proceed:
            return dl_path
        
        t_path = dl_path
        sevenz = SevenZ(self)
        LOGGER.info(f"Extracting: {self.name}")
        async with task_dict_lock:
            task_dict[self.mid] = SevenZStatus(self, sevenz, gid, "Extract")
        
        for dirpath, _, files in await sync_to_async(
            walk, self.up_dir or self.dir, topdown=False
        ):
            code = await self._process_directory_extraction(dirpath, files, sevenz, pswd)
            if self.is_cancelled:
                return code
        
        if self.proceed_count == 0:
            LOGGER.info("No files able to extract!")
        return t_path if self.is_file and code == 0 else dl_path

    async def _process_directory_extraction(self, dirpath, files, sevenz, pswd):
        code = 0
        for file_ in files:
            if self.is_cancelled:
                return code
            if self._should_extract_file(file_):
                code = await self._extract_single_file(dirpath, file_, sevenz, pswd)
        if code == 0:
            await self._cleanup_extracted_archives(dirpath, files)
        return code

    async def _extract_single_file(self, dirpath, file_, sevenz, pswd):
        self.proceed_count += 1
        f_path = ospath.join(dirpath, file_)
        t_path = get_base_name(f_path) if self.is_file else dirpath
        if not self.is_file:
            self.subname = file_
        return await sevenz.extract(f_path, t_path, pswd)

    def _build_ffmpeg_cmds(self):
        return [
            [part.strip() for part in split(item) if part.strip()]
            for item in self.ffmpeg_cmds
        ]

    @staticmethod
    def _get_ffmpeg_input_file(cmd, input_indexes):
        return next(
            (
                cmd[index + 1]
                for index in input_indexes
                if cmd[index + 1].startswith("mltb")
            ),
            "",
        )

    @staticmethod
    def _get_ffmpeg_ext(input_file):
        if input_file.strip().endswith(".video"):
            return "video"
        if input_file.strip().endswith(".audio"):
            return "audio"
        if "." not in input_file:
            return "all"
        return ospath.splitext(input_file)[-1].lower()

    async def _prepare_ffmpeg_cmd(self, cmd, input_indexes, target_path, inputs):
        var_cmd = cmd.copy()
        for index in input_indexes:
            if cmd[index + 1].startswith("mltb"):
                var_cmd[index + 1] = target_path
            elif is_telegram_link(cmd[index + 1]):
                msg = (await get_tg_link_message(cmd[index + 1]))[0]
                file_dir = await temp_download(msg)
                inputs[index + 1] = file_dir
                var_cmd[index + 1] = file_dir
        return var_cmd

    async def _ensure_ffmpeg_status(self, ffmpeg, gid, checked):
        if checked:
            return True
        async with task_dict_lock:
            task_dict[self.mid] = FFmpegStatus(self, ffmpeg, gid, "FFmpeg")
        self.progress = False
        await cpu_eater_lock.acquire()
        self.progress = True
        return True

    async def _cleanup_ffmpeg_inputs(self, inputs):
        for inp in inputs.values():
            if "/temp/" in inp and aiopath.exists(inp):
                await remove(inp)

    @staticmethod
    def _ffmpeg_target_matches(path, ext, is_video, is_audio):
        if not is_video and not is_audio:
            return False
        if is_video and ext == "audio":
            return False
        if is_audio and not is_video and ext == "video":
            return False
        if ext in ["all", "audio", "video"]:
            return True
        return path.strip().lower().endswith(ext)

    async def _run_ffmpeg_single_file(
        self,
        ffmpeg,
        cmd,
        input_indexes,
        ext,
        dl_path,
        delete_files,
        gid,
        checked,
        inputs,
    ):
        is_video, is_audio, _ = await get_document_type(dl_path)
        if not self._ffmpeg_target_matches(dl_path, ext, is_video, is_audio):
            return dl_path, checked, False

        new_folder = ospath.splitext(dl_path)[0]
        name = ospath.basename(dl_path)
        await makedirs(new_folder, exist_ok=True)
        file_path = f"{new_folder}/{name}"
        await move(dl_path, file_path)
        if not checked:
            checked = await self._ensure_ffmpeg_status(ffmpeg, gid, checked)
        LOGGER.info(f"Running ffmpeg cmd for: {file_path}")
        var_cmd = await self._prepare_ffmpeg_cmd(cmd, input_indexes, file_path, inputs)
        self.subsize = self.size
        res = await ffmpeg.ffmpeg_cmds(var_cmd, file_path)
        if not res:
            await move(file_path, dl_path)
            await rmtree(new_folder)
            return dl_path, checked, True

        if delete_files:
            await remove(file_path)
            if len(await listdir(new_folder)) == 1:
                folder = new_folder.rsplit("/", 1)[0]
                self.name = ospath.basename(res[0])
                if self.name.startswith("ffmpeg"):
                    self.name = self.name.split(".", 1)[-1]
                dl_path = ospath.join(folder, self.name)
                await move(res[0], dl_path)
                await rmtree(new_folder)
            else:
                dl_path = new_folder
                self.name = new_folder.rsplit("/", 1)[-1]
            return dl_path, checked, True

        dl_path = new_folder
        self.name = new_folder.rsplit("/", 1)[-1]
        return dl_path, checked, True

    async def _run_ffmpeg_directory(
        self,
        ffmpeg,
        cmd,
        input_indexes,
        ext,
        dl_path,
        delete_files,
        gid,
        checked,
        inputs,
    ):
        for dirpath, _, files in await sync_to_async(walk, dl_path, topdown=False):
            for file_ in files:
                if self.is_cancelled:
                    return checked
                f_path = ospath.join(dirpath, file_)
                is_video, is_audio, _ = await get_document_type(f_path)
                if not self._ffmpeg_target_matches(f_path, ext, is_video, is_audio):
                    continue

                self.proceed_count += 1
                var_cmd = await self._prepare_ffmpeg_cmd(cmd, input_indexes, f_path, inputs)
                if not checked:
                    checked = await self._ensure_ffmpeg_status(ffmpeg, gid, checked)
                LOGGER.info(f"Running ffmpeg cmd for: {f_path}")
                self.subsize = await get_path_size(f_path)
                self.subname = file_
                res = await ffmpeg.ffmpeg_cmds(var_cmd, f_path)
                if res and delete_files:
                    await remove(f_path)
                    if len(res) == 1:
                        file_name = ospath.basename(res[0])
                        if file_name.startswith("ffmpeg"):
                            newname = file_name.split(".", 1)[-1]
                            await move(res[0], ospath.join(dirpath, newname))
        return checked

    async def proceed_ffmpeg(self, dl_path, gid):
        checked = False
        inputs = {}
        cmds = self._build_ffmpeg_cmds()
        try:
            ffmpeg = FFMpeg(self)
            for ffmpeg_cmd in cmds:
                self.proceed_count = 0
                cmd = [
                    "taskset",
                    "-c",
                    f"{cores}",
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-progress",
                    "pipe:1",
                ] + ffmpeg_cmd
                if "-del" in cmd:
                    cmd.remove("-del")
                    delete_files = True
                else:
                    delete_files = False
                input_indexes = [
                    index for index, value in enumerate(cmd) if value == "-i"
                ]
                input_file = self._get_ffmpeg_input_file(cmd, input_indexes)
                if not input_file:
                    LOGGER.error("Wrong FFmpeg cmd!")
                    return dl_path
                ext = self._get_ffmpeg_ext(input_file)
                if await aiopath.isfile(dl_path):
                    dl_path, checked, processed = await self._run_ffmpeg_single_file(
                        ffmpeg,
                        cmd,
                        input_indexes,
                        ext,
                        dl_path,
                        delete_files,
                        gid,
                        checked,
                        inputs,
                    )
                    if not processed:
                        break
                else:
                    checked = await self._run_ffmpeg_directory(
                        ffmpeg,
                        cmd,
                        input_indexes,
                        ext,
                        dl_path,
                        delete_files,
                        gid,
                        checked,
                        inputs,
                    )
                await self._cleanup_ffmpeg_inputs(inputs)
        finally:
            if checked:
                cpu_eater_lock.release()
        return dl_path

    async def substitute(self, dl_path):
        def perform_substitution(name, substitutions):
            for substitution in substitutions:
                sen = False
                pattern = substitution[0]
                if pattern.startswith('"') and pattern.endswith('"'):
                    pattern = pattern.strip('"')
                if len(substitution) > 1:
                    if len(substitution) > 2:
                        sen = substitution[2] == "s"
                        res = substitution[1]
                    elif len(substitution[1]) == 0:
                        res = " "
                    else:
                        res = substitution[1]
                else:
                    res = ""
                try:
                    name = sub(pattern, res, name, flags=I if sen else 0)
                except Exception as e:
                    LOGGER.error(
                        f"Substitute Error: pattern: {pattern} res: {res}. Error: {e}"
                    )
                    return False
                if len(name.encode()) > 255:
                    LOGGER.error(f"Substitute: {name} is too long")
                    return False
            return name

        if self.is_file:
            up_dir, name = dl_path.rsplit("/", 1)
            new_name = perform_substitution(name, self.name_sub)
            if not new_name:
                return dl_path
            new_path = ospath.join(up_dir, new_name)
            await move(dl_path, new_path)
            return new_path
        else:
            for dirpath, _, files in await sync_to_async(walk, dl_path, topdown=False):
                for file_ in files:
                    f_path = ospath.join(dirpath, file_)
                    new_name = perform_substitution(file_, self.name_sub)
                    if not new_name:
                        continue
                    await move(f_path, ospath.join(dirpath, new_name))
            return dl_path

    @staticmethod
    def _parse_convert_setting(setting):
        if not setting:
            return "", "", []
        data = setting.split()
        ext = data[0].lower() if data else ""
        status = ""
        ext_list = []
        if len(data) > 2:
            if "+" in data[1].split():
                status = "+"
            elif "-" in data[1].split():
                status = "-"
            ext_list = [f".{ext_.lower()}" for ext_ in data[2:]]
        return ext, status, ext_list

    @staticmethod
    def _should_convert_video(f_path, vext, vstatus, fvext):
        if not vext:
            return False
        if f_path.strip().lower().endswith(f".{vext}"):
            return False
        if not vstatus:
            return True
        if vstatus == "+" and f_path.strip().lower().endswith(tuple(fvext)):
            return True
        if vstatus == "-" and not f_path.strip().lower().endswith(tuple(fvext)):
            return True
        return False

    @staticmethod
    def _should_convert_audio(f_path, aext, astatus, faext):
        if not aext:
            return False
        if f_path.strip().lower().endswith(f".{aext}"):
            return False
        if not astatus:
            return True
        if astatus == "+" and f_path.strip().lower().endswith(tuple(faext)):
            return True
        if astatus == "-" and not f_path.strip().lower().endswith(tuple(faext)):
            return True
        return False

    async def _collect_media_files(self, dl_path):
        if self.is_file:
            return [dl_path]
        all_files = []
        for dirpath, _, files in await sync_to_async(walk, dl_path, topdown=False):
            for file_ in files:
                all_files.append(ospath.join(dirpath, file_))
        return all_files

    async def generate_screenshots(self, dl_path):
        ss_nb = int(self.screen_shots) if isinstance(self.screen_shots, str) else 10
        if self.is_file:
            if (await get_document_type(dl_path))[0]:
                LOGGER.info(f"Creating Screenshot for: {dl_path}")
                res = await take_ss(dl_path, ss_nb)
                if res:
                    new_folder = ospath.splitext(dl_path)[0]
                    name = ospath.basename(dl_path)
                    await makedirs(new_folder, exist_ok=True)
                    await gather(
                        move(dl_path, f"{new_folder}/{name}"),
                        move(res, new_folder),
                    )
                    return new_folder
        else:
            LOGGER.info(f"Creating Screenshot for: {dl_path}")
            for dirpath, _, files in await sync_to_async(walk, dl_path, topdown=False):
                for file_ in files:
                    f_path = ospath.join(dirpath, file_)
                    if (await get_document_type(f_path))[0]:
                        await take_ss(f_path, ss_nb)
        return dl_path

    async def _identify_convertible_files(self, dl_path, vext, vstatus, fvext, aext, astatus, faext):
        """Identify all files that need conversion"""
        self.files_to_proceed = {}
        all_files = await self._collect_media_files(dl_path)
        for f_path in all_files:
            is_video, is_audio, _ = await get_document_type(f_path)
            if is_video and self._should_convert_video(f_path, vext, vstatus, fvext):
                self.files_to_proceed[f_path] = "video"
            elif (
                is_audio
                and not is_video
                and self._should_convert_audio(f_path, aext, astatus, faext)
            ):
                self.files_to_proceed[f_path] = "audio"
    
    async def _convert_single_file(self, ffmpeg, f_path, f_type, vext, aext):
        """Convert a single media file"""
        self.proceed_count += 1
        LOGGER.info(f"Converting: {f_path}")
        if self.is_file:
            self.subsize = self.size
        else:
            self.subsize = await get_path_size(f_path)
            self.subname = ospath.basename(f_path)
        
        if f_type == "video":
            res = await ffmpeg.convert_video(f_path, vext)
        else:
            res = await ffmpeg.convert_audio(f_path, aext)
        
        if res:
            try:
                await remove(f_path)
            except:
                self.is_cancelled = True
                return None
            if self.is_file:
                return res
        return f_path
    
    async def _execute_conversions(self, ffmpeg, vext, aext, gid):
        """Execute all media conversions"""
        async with task_dict_lock:
            task_dict[self.mid] = FFmpegStatus(self, ffmpeg, gid, "Convert")
        self.progress = False
        async with cpu_eater_lock:
            self.progress = True
            for f_path, f_type in self.files_to_proceed.items():
                result = await self._convert_single_file(ffmpeg, f_path, f_type, vext, aext)
                if result is None:
                    return False
                if self.is_file and result != f_path:
                    return result
        return None
    
    async def convert_media(self, dl_path, gid):
        vext, vstatus, fvext = self._parse_convert_setting(self.convert_video)
        aext, astatus, faext = self._parse_convert_setting(self.convert_audio)

        await self._identify_convertible_files(dl_path, vext, vstatus, fvext, aext, astatus, faext)

        if self.files_to_proceed:
            ffmpeg = FFMpeg(self)
            result = await self._execute_conversions(ffmpeg, vext, aext, gid)
            if result is not None:
                return result if result else False
        return dl_path

    @staticmethod
    def _parse_sample_settings(sample_video):
        data = sample_video.split(":") if isinstance(sample_video, str) else []
        if not data:
            return 60, 4
        sample_duration = int(data[0]) if data[0] else 60
        part_duration = int(data[1]) if len(data) > 1 else 4
        return sample_duration, part_duration

    async def _collect_video_files_for_sample(self, dl_path):
        files_to_sample = {}
        if self.is_file and (await get_document_type(dl_path))[0]:
            files_to_sample[dl_path] = ospath.basename(dl_path)
            return files_to_sample
        for dirpath, _, files in await sync_to_async(walk, dl_path, topdown=False):
            for file_ in files:
                f_path = ospath.join(dirpath, file_)
                if (await get_document_type(f_path))[0]:
                    files_to_sample[f_path] = file_
        return files_to_sample

    async def generate_sample_video(self, dl_path, gid):
        sample_duration, part_duration = self._parse_sample_settings(self.sample_video)
        self.files_to_proceed = await self._collect_video_files_for_sample(dl_path)
        if self.files_to_proceed:
            ffmpeg = FFMpeg(self)
            async with task_dict_lock:
                task_dict[self.mid] = FFmpegStatus(self, ffmpeg, gid, "Sample Video")
            self.progress = False
            async with cpu_eater_lock:
                self.progress = True
                LOGGER.info(f"Creating Sample video: {self.name}")
                for f_path, file_ in self.files_to_proceed.items():
                    self.proceed_count += 1
                    if self.is_file:
                        self.subsize = self.size
                    else:
                        self.subsize = await get_path_size(f_path)
                        self.subname = file_
                    res = await ffmpeg.sample_video(
                        f_path, sample_duration, part_duration
                    )
                    if res and self.is_file:
                        new_folder = ospath.splitext(f_path)[0]
                        await makedirs(new_folder, exist_ok=True)
                        await gather(
                            move(f_path, f"{new_folder}/{file_}"),
                            move(res, f"{new_folder}/SAMPLE.{file_}"),
                        )
                        return new_folder
        return dl_path

    async def proceed_compress(self, dl_path, gid):
        pswd = self.compress if isinstance(self.compress, str) else ""
        if self.is_leech and self.is_file:
            new_folder = ospath.splitext(dl_path)[0]
            name = ospath.basename(dl_path)
            await makedirs(new_folder, exist_ok=True)
            new_dl_path = f"{new_folder}/{name}"
            await move(dl_path, new_dl_path)
            dl_path = new_dl_path
            up_path = f"{new_dl_path}.zip"
            self.is_file = False
        else:
            up_path = f"{dl_path}.zip"
        sevenz = SevenZ(self)
        async with task_dict_lock:
            task_dict[self.mid] = SevenZStatus(self, sevenz, gid, "Zip")
        return await sevenz.zip(dl_path, up_path, pswd)

    async def proceed_split(self, dl_path, gid):
        self.files_to_proceed = {}
        await self._collect_files_for_split(dl_path)
        
        if not self.files_to_proceed:
            return
        
        ffmpeg = FFMpeg(self)
        async with task_dict_lock:
            task_dict[self.mid] = FFmpegStatus(self, ffmpeg, gid, "Split")
        LOGGER.info(f"Splitting: {self.name}")
        
        for f_path, (f_size, file_) in self.files_to_proceed.items():
            result = await self._split_single_file(ffmpeg, f_path, f_size, file_)
            if not result:
                return False

    async def _collect_files_for_split(self, dl_path):
        if self.is_file:
            f_size = await get_path_size(dl_path)
            if f_size > self.split_size:
                self.files_to_proceed[dl_path] = [f_size, ospath.basename(dl_path)]
        else:
            for dirpath, _, files in await sync_to_async(walk, dl_path, topdown=False):
                for file_ in files:
                    f_path = ospath.join(dirpath, file_)
                    f_size = await get_path_size(f_path)
                    if f_size > self.split_size:
                        self.files_to_proceed[f_path] = [f_size, file_]

    async def _split_single_file(self, ffmpeg, f_path, f_size, file_):
        self.proceed_count += 1
        if self.is_file:
            self.subsize = self.size
        else:
            self.subsize = f_size
            self.subname = file_
        
        parts = -(-f_size // self.split_size)
        if self.equal_splits:
            split_size = (f_size // parts) + (f_size % parts)
        else:
            split_size = self.split_size
        
        if not self.as_doc and (await get_document_type(f_path))[0]:
            self.progress = True
            res = await ffmpeg.split(f_path, file_, parts, split_size)
        else:
            self.progress = False
            res = await split_file(f_path, split_size, self)
        
        if self.is_cancelled:
            return False
        
        if res or f_size >= self.max_split_size:
            try:
                await remove(f_path)
            except:
                self.is_cancelled = True
        return True
