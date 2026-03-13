"""
Settings UI formatters - Build consistent UI for different setting types
Each formatter handles one specific setting category
"""

from abc import ABC, abstractmethod
from html import escape
from typing import Tuple

from ..helper.telegram_helper.button_build import ButtonMaker
from .user_settings_core import SettingsRetriever


class BaseSettingsFormatter(ABC):
    """Base class for settings formatters"""

    def __init__(self, user_id: int, name: str):
        self.user_id = user_id
        self.name = name
        self.buttons = ButtonMaker()

    @abstractmethod
    async def get_text(self) -> str:
        """Get formatted text for settings display"""

    @abstractmethod
    async def build_buttons(self) -> None:
        """Build navigation buttons"""

    async def get_message_and_buttons(self) -> Tuple[str, list]:
        """Get complete message and buttons"""
        await self.build_buttons()
        text = await self.get_text()
        return text, self.buttons.build_menu(1)


class LeechSettingsFormatter(BaseSettingsFormatter):
    """Format leech-related settings"""

    async def build_buttons(self) -> None:
        """Add leech settings buttons"""
        self.buttons.data_button("Thumbnail", f"userset {self.user_id} menu THUMBNAIL")
        self.buttons.data_button(
            "Leech Split Size", f"userset {self.user_id} menu LEECH_SPLIT_SIZE"
        )
        self.buttons.data_button(
            "Leech Destination", f"userset {self.user_id} menu LEECH_DUMP_CHAT"
        )
        self.buttons.data_button(
            "Leech Prefix", f"userset {self.user_id} menu LEECH_FILENAME_PREFIX"
        )
        self.buttons.data_button(
            "Send As Media", f"userset {self.user_id} tog AS_DOCUMENT"
        )
        self.buttons.data_button(
            "Equal Splits", f"userset {self.user_id} tog EQUAL_SPLITS"
        )
        self.buttons.data_button(
            "Media Group", f"userset {self.user_id} tog MEDIA_GROUP"
        )
        self.buttons.data_button(
            "User Transmission", f"userset {self.user_id} tog USER_TRANSMISSION"
        )
        self.buttons.data_button(
            "Hybrid Leech", f"userset {self.user_id} tog HYBRID_LEECH"
        )
        self.buttons.data_button(
            "Thumbnail Layout", f"userset {self.user_id} menu THUMBNAIL_LAYOUT"
        )
        self.buttons.data_button("Back", f"userset {self.user_id} back")

    async def _get_leech_type(self) -> str:
        """Get leech type setting"""
        if SettingsRetriever.get_bool_setting(self.user_id, "AS_DOCUMENT"):
            return "DOCUMENT"
        return "MEDIA"

    async def _get_equal_splits_status(self) -> str:
        """Get equal splits status"""
        if SettingsRetriever.get_bool_setting(self.user_id, "EQUAL_SPLITS"):
            return "Enabled"
        return "Disabled"

    async def _get_media_group_status(self) -> str:
        """Get media group status"""
        if SettingsRetriever.get_bool_setting(self.user_id, "MEDIA_GROUP"):
            return "Enabled"
        return "Disabled"

    async def _get_user_transmission_method(self) -> str:
        """Get user transmission method"""
        if SettingsRetriever.get_bool_setting(
            self.user_id, "USER_TRANSMISSION", premium_only=True
        ):
            return "user"
        return "bot"

    async def _get_hybrid_leech_status(self) -> str:
        """Get hybrid leech status"""
        if SettingsRetriever.get_bool_setting(
            self.user_id, "HYBRID_LEECH", premium_only=True
        ):
            return "Enabled"
        return "Disabled"

    async def get_text(self) -> str:
        """Format leech settings text"""
        thumb_path = f"thumbnails/{self.user_id}.jpg"
        thumbmsg = SettingsRetriever.format_status(
            await SettingsRetriever.file_exists(thumb_path)
        )

        split_size = SettingsRetriever.get_setting(
            self.user_id, "LEECH_SPLIT_SIZE", "Default"
        )
        leech_dest = SettingsRetriever.get_setting(
            self.user_id, "LEECH_DUMP_CHAT", "None"
        )
        lprefix = SettingsRetriever.get_setting(
            self.user_id, "LEECH_FILENAME_PREFIX", "None"
        )

        return f"""<u>Leech Settings for {self.name}</u>
Leech Type: <b>{await self._get_leech_type()}</b>
Custom Thumbnail: <b>{thumbmsg}</b>
Leech Split Size: <b>{split_size}</b>
Equal Splits: <b>{await self._get_equal_splits_status()}</b>
Media Group: <b>{await self._get_media_group_status()}</b>
Leech Prefix: <code>{escape(str(lprefix))}</code>
Leech Destination: <code>{leech_dest}</code>
Leech By: <b>{await self._get_user_transmission_method()}</b> session
Hybrid Leech: <b>{await self._get_hybrid_leech_status()}</b>
Thumbnail Layout: <b>{SettingsRetriever.get_setting(self.user_id, "THUMBNAIL_LAYOUT", "None")}</b>
"""


class RcloneSettingsFormatter(BaseSettingsFormatter):
    """Format rclone-related settings"""

    async def build_buttons(self) -> None:
        """Add rclone settings buttons"""
        self.buttons.data_button("Rclone Config", f"userset {self.user_id} menu RCLONE_CONFIG")
        self.buttons.data_button(
            "Default Rclone Path", f"userset {self.user_id} menu RCLONE_PATH"
        )
        self.buttons.data_button("Rclone Flags", f"userset {self.user_id} menu RCLONE_FLAGS")
        self.buttons.data_button("Back", f"userset {self.user_id} back")

    async def get_text(self) -> str:
        """Format rclone settings text"""
        rclone_conf = f"rclone/{self.user_id}.conf"
        rccmsg = SettingsRetriever.format_status(
            await SettingsRetriever.file_exists(rclone_conf)
        )
        rccpath = SettingsRetriever.get_setting(self.user_id, "RCLONE_PATH", "None")
        rcflags = SettingsRetriever.get_setting(self.user_id, "RCLONE_FLAGS", "None")

        return f"""<u>Rclone Settings for {self.name}</u>
Rclone Config: <b>{rccmsg}</b>
Rclone Path: <code>{rccpath}</code>
Rclone Flags: <code>{rcflags}</code>"""


class GdriveSettingsFormatter(BaseSettingsFormatter):
    """Format Google Drive related settings"""

    async def build_buttons(self) -> None:
        """Add gdrive settings buttons"""
        self.buttons.data_button("token.pickle", f"userset {self.user_id} menu TOKEN_PICKLE")
        self.buttons.data_button(
            "Default Gdrive ID", f"userset {self.user_id} menu GDRIVE_ID"
        )
        self.buttons.data_button("Index URL", f"userset {self.user_id} menu INDEX_URL")
        self.buttons.data_button(
            "Stop Duplicate", f"userset {self.user_id} tog STOP_DUPLICATE"
        )
        self.buttons.data_button("Back", f"userset {self.user_id} back")

    async def _get_stop_duplicate_status(self) -> str:
        """Get stop duplicate status"""
        if SettingsRetriever.get_bool_setting(self.user_id, "STOP_DUPLICATE"):
            return "Enabled"
        return "Disabled"

    async def get_text(self) -> str:
        """Format gdrive settings text"""
        token_pickle = f"tokens/{self.user_id}.pickle"
        tokenmsg = SettingsRetriever.format_status(
            await SettingsRetriever.file_exists(token_pickle)
        )
        gdrive_id = SettingsRetriever.get_setting(self.user_id, "GDRIVE_ID", "None")
        index_url = SettingsRetriever.get_setting(self.user_id, "INDEX_URL", "None")

        return f"""<u>Google Drive Settings for {self.name}</u>
Gdrive Token: <b>{tokenmsg}</b>
Gdrive ID: <code>{gdrive_id}</code>
Index URL: <code>{index_url}</code>
Stop Duplicate: <b>{await self._get_stop_duplicate_status()}</b>"""


class UploadSettingsFormatter(BaseSettingsFormatter):
    """Format upload/general settings"""

    async def build_buttons(self) -> None:
        """Add upload settings buttons"""
        self.buttons.data_button("Leech", f"userset {self.user_id} leech")
        self.buttons.data_button("Rclone", f"userset {self.user_id} rclone")
        self.buttons.data_button("Gdrive API", f"userset {self.user_id} gdrive")
        self.buttons.data_button("Upload Paths", f"userset {self.user_id} menu UPLOAD_PATHS")
        self.buttons.data_button(
            "Default Upload", f"userset {self.user_id} menu DEFAULT_UPLOAD"
        )
        self.buttons.data_button(
            "User Tokens", f"userset {self.user_id} tog USER_TOKENS"
        )
        self.buttons.data_button(
            "Excluded Extensions", f"userset {self.user_id} menu EXCLUDED_EXTENSIONS"
        )
        self.buttons.data_button(
            "Included Extensions", f"userset {self.user_id} menu INCLUDED_EXTENSIONS"
        )
        self.buttons.data_button(
            "Name Substitute", f"userset {self.user_id} menu NAME_SUBSTITUTE"
        )
        self.buttons.data_button("YT-DLP Options", f"userset {self.user_id} menu YT_DLP_OPTIONS")
        self.buttons.data_button("FFmpeg Cmds", f"userset {self.user_id} menu FFMPEG_CMDS")

    async def _get_upload_method(self) -> str:
        """Get default upload method"""
        default = SettingsRetriever.get_setting(self.user_id, "DEFAULT_UPLOAD", "gd")
        return "Gdrive API" if default == "gd" else "Rclone"

    async def _get_token_usage(self) -> str:
        """Get token usage setting"""
        if SettingsRetriever.get_setting(self.user_id, "USER_TOKENS", False):
            return "MY"
        return "OWNER"

    async def get_text(self) -> str:
        """Format upload settings text"""
        upload_paths = SettingsRetriever.get_setting(self.user_id, "UPLOAD_PATHS", "None")
        name_sub = (
            "Added"
            if SettingsRetriever.get_setting(self.user_id, "NAME_SUBSTITUTE", False)
            else "None"
        )
        excluded_ext = SettingsRetriever.get_setting(
            self.user_id, "EXCLUDED_EXTENSIONS", "None"
        )
        included_ext = SettingsRetriever.get_setting(
            self.user_id, "INCLUDED_EXTENSIONS", "None"
        )
        yt_opts = SettingsRetriever.get_setting(self.user_id, "YT_DLP_OPTIONS", "None")
        ffmpeg = (
            "Exists"
            if SettingsRetriever.get_setting(self.user_id, "FFMPEG_CMDS", False)
            else "None"
        )

        return f"""<u>Settings for {self.name}</u>
Default Upload: <b>{await self._get_upload_method()}</b>
Using: <b>{await self._get_token_usage()}</b> token/config
Upload Paths: <code>{upload_paths}</code>
Name Substitution: <code>{name_sub}</code>
Excluded Extensions: <code>{excluded_ext}</code>
Included Extensions: <code>{included_ext}</code>
YT-DLP Options: <code>{yt_opts}</code>
FFmpeg Commands: <b>{ffmpeg}</b>"""
