"""
Task Configuration Initializers
Handles all initialization logic for TaskConfig settings
"""

from bot.core.config_manager import Config
from bot.core.telegram_manager import TgClient
from bot.helper.ext_utils.bot_utils import get_size_bytes


class TaskConfigInitializers:
    """Handles initialization of various TaskConfig settings"""

    @staticmethod
    def init_name_substitute(task_config):
        """Initialize name substitution patterns"""
        task_config.name_sub = (
            task_config.name_sub
            or task_config.user_dict.get("NAME_SUBSTITUTE", False)
            or (
                Config.NAME_SUBSTITUTE
                if "NAME_SUBSTITUTE" not in task_config.user_dict
                else ""
            )
        )
        if task_config.name_sub:
            task_config.name_sub = [
                x.split("/") for x in task_config.name_sub.split(" | ")
            ]

    @staticmethod
    def init_extension_filters(task_config):
        """Initialize file extension filters"""
        from bot import excluded_extensions, included_extensions

        task_config.excluded_extensions = task_config.user_dict.get(
            "EXCLUDED_EXTENSIONS"
        ) or (
            excluded_extensions
            if "EXCLUDED_EXTENSIONS" not in task_config.user_dict
            else ["aria2", "!qB"]
        )
        task_config.included_extensions = task_config.user_dict.get(
            "INCLUDED_EXTENSIONS"
        ) or (
            included_extensions
            if "INCLUDED_EXTENSIONS" not in task_config.user_dict
            else []
        )

    @staticmethod
    def init_rc_flags(task_config):
        """Initialize RClone flags"""
        if task_config.rc_flags:
            return
        if task_config.user_dict.get("RCLONE_FLAGS"):
            task_config.rc_flags = task_config.user_dict["RCLONE_FLAGS"]
        elif "RCLONE_FLAGS" not in task_config.user_dict and Config.RCLONE_FLAGS:
            task_config.rc_flags = Config.RCLONE_FLAGS

    @staticmethod
    def init_user_transmission(task_config):
        """Initialize user transmission settings"""
        is_premium = TgClient and hasattr(TgClient, 'IS_PREMIUM_USER') and TgClient.IS_PREMIUM_USER
        task_config.user_transmission = is_premium and (
            task_config.user_dict.get("USER_TRANSMISSION")
            or Config.USER_TRANSMISSION
            and "USER_TRANSMISSION" not in task_config.user_dict
        )

    @staticmethod
    def init_split_settings(task_config):
        """Initialize file split size settings"""
        if task_config.split_size:
            if task_config.split_size.isdigit():
                task_config.split_size = int(task_config.split_size)
            else:
                task_config.split_size = get_size_bytes(task_config.split_size)
        task_config.split_size = (
            task_config.split_size
            or task_config.user_dict.get("LEECH_SPLIT_SIZE")
            or Config.LEECH_SPLIT_SIZE
        )
        task_config.equal_splits = (
            task_config.user_dict.get("EQUAL_SPLITS")
            or Config.EQUAL_SPLITS
            and "EQUAL_SPLITS" not in task_config.user_dict
        )
        task_config.max_split_size = (
            TgClient.MAX_SPLIT_SIZE if task_config.user_transmission else 2097152000
        )
        task_config.split_size = min(task_config.split_size, task_config.max_split_size)

    @staticmethod
    def init_as_doc(task_config):
        """Initialize 'as document' mode"""
        if not task_config.as_doc:
            task_config.as_doc = (
                not task_config.as_med
                if task_config.as_med
                else (
                    task_config.user_dict.get("AS_DOCUMENT", False)
                    or Config.AS_DOCUMENT
                    and "AS_DOCUMENT" not in task_config.user_dict
                )
            )

    @staticmethod
    def init_thumbnail_layout(task_config):
        """Initialize thumbnail layout settings"""
        task_config.thumbnail_layout = (
            task_config.thumbnail_layout
            or task_config.user_dict.get("THUMBNAIL_LAYOUT", False)
            or (
                Config.THUMBNAIL_LAYOUT
                if "THUMBNAIL_LAYOUT" not in task_config.user_dict
                else ""
            )
        )
