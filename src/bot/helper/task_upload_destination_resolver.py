"""
Upload Destination Resolver
Handles resolution of upload destinations for Google Drive and RClone
Extracts complex cc=33 upload resolution logic from common.py
"""

from bot import Config
from bot.helper.ext_utils.links_utils import is_gdrive_id, is_gdrive_link, is_rclone_path
from bot.helper.mirror_leech_utils.gdrive_utils.list import GoogleDriveList
from bot.helper.mirror_leech_utils.rclone_utils.list import RcloneList
from bot.helper.task_config_normalizers import TaskConfigNormalizers
from bot.helper.task_config_path_resolvers import TaskConfigPathResolvers


class UploadDestinationResolver:
    """Resolves upload destination paths for various cloud storage services"""

    @staticmethod
    def _get_default_upload_config(task_config):
        """Get default upload destination from config"""
        stop_duplicate = (
            task_config.user_dict.get("STOP_DUPLICATE")
            or "STOP_DUPLICATE" not in task_config.user_dict
            and Config.STOP_DUPLICATE
        )
        default_upload = (
            task_config.user_dict.get("DEFAULT_UPLOAD", "") or Config.DEFAULT_UPLOAD
        )
        return stop_duplicate, default_upload

    @staticmethod
    def _resolve_default_destination(task_config, default_upload):
        """Resolve default destination based on DEFAULT_UPLOAD setting"""
        if (not task_config.up_dest and default_upload == "rc") or task_config.up_dest == "rc":
            task_config.up_dest = (
                task_config.user_dict.get("RCLONE_PATH") or Config.RCLONE_PATH
            )
        elif (not task_config.up_dest and default_upload == "gd") or task_config.up_dest == "gd":
            task_config.up_dest = (
                task_config.user_dict.get("GDRIVE_ID") or Config.GDRIVE_ID
            )

    @staticmethod
    async def _resolve_rclone_shortcut(task_config):
        """Resolve 'rcl' shortcut to actual rclone path"""
        config_path = None
        if task_config.is_clone:
            if not is_rclone_path(task_config.link):
                raise ValueError("You can't clone from different types of tools")
            config_path = TaskConfigPathResolvers.get_config_path(task_config, task_config.link)
        task_config.up_dest = await RcloneList(task_config).get_rclone_path(
            "rcu", config_path
        )
        if not is_rclone_path(task_config.up_dest):
            raise ValueError(task_config.up_dest)

    @staticmethod
    async def _resolve_gdrive_shortcut(task_config):
        """Resolve 'gdl' shortcut to actual Google Drive ID"""
        token_path = None
        if task_config.is_clone:
            if not is_gdrive_link(task_config.link):
                raise ValueError("You can't clone from different types of tools")
            token_path = TaskConfigPathResolvers.get_token_path(task_config, task_config.link)
        task_config.up_dest = await GoogleDriveList(task_config).get_target_id(
            "gdu", token_path
        )
        if not is_gdrive_id(task_config.up_dest):
            raise ValueError(task_config.up_dest)

    @staticmethod
    def _validate_clone_tokens(task_config):
        """Validate that source and destination use the same token/config"""
        if is_gdrive_link(task_config.link):
            link_token = TaskConfigPathResolvers.get_token_path(task_config, task_config.link)
            dest_token = TaskConfigPathResolvers.get_token_path(task_config, task_config.up_dest)
            if link_token != dest_token:
                raise ValueError("You must use the same token to clone!")
        if is_rclone_path(task_config.link):
            link_config = TaskConfigPathResolvers.get_config_path(task_config, task_config.link)
            dest_config = TaskConfigPathResolvers.get_config_path(task_config, task_config.up_dest)
            if link_config != dest_config:
                raise ValueError("You must use the same config to clone!")

    @staticmethod
    async def resolve_upload_destination(task_config):
        """
        Main method to resolve upload destination
        Reduces cyclomatic complexity from 33 to manageable levels
        """
        # Set stop_duplicate flag
        stop_duplicate, default_upload = UploadDestinationResolver._get_default_upload_config(
            task_config
        )
        task_config.stop_duplicate = stop_duplicate

        # Resolve default destination
        UploadDestinationResolver._resolve_default_destination(task_config, default_upload)

        # Validate destination exists
        if not task_config.up_dest:
            raise ValueError("No Upload Destination!")

        # Normalize tokens
        await TaskConfigNormalizers.normalize_up_dest_tokens(task_config)

        # Handle shortcuts
        if task_config.up_dest == "rcl":
            await UploadDestinationResolver._resolve_rclone_shortcut(task_config)
        elif task_config.up_dest == "gdl":
            await UploadDestinationResolver._resolve_gdrive_shortcut(task_config)

        # Validate clone operation uses matching tokens/configs
        if task_config.is_clone:
            UploadDestinationResolver._validate_clone_tokens(task_config)
