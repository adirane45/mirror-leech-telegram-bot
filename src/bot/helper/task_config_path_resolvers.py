"""
Task Configuration Path Resolvers
Handles token paths, config paths, and file system operations
"""

from aiofiles.os import path as aiopath, makedirs
from os import chmod

from bot import Config
from bot.helper.ext_utils.links_utils import is_rclone_path, is_gdrive_link


class TaskConfigPathResolvers:
    """Handles path resolution and token/config path utilities"""

    @staticmethod
    def get_token_path(task_config, dest):
        """Get the token path based on destination prefix"""
        if dest.startswith("mtp:"):
            return f"tokens/{task_config.user_id}.pickle"
        elif (
            dest.startswith("sa:")
            or Config.USE_SERVICE_ACCOUNTS
            and not dest.startswith("tp:")
        ):
            return "accounts"
        else:
            return "token.pickle"

    @staticmethod
    def get_config_path(task_config, dest):
        """Get the RClone config path based on destination"""
        return (
            f"rclone/{task_config.user_id}.conf"
            if dest.startswith("mrcc:")
            else "rclone.conf"
        )

    @staticmethod
    async def is_token_exists(task_config, path, status):
        """Validate that required tokens/configs exist"""
        if is_rclone_path(path):
            config_path = TaskConfigPathResolvers.get_config_path(task_config, path)
            if config_path != "rclone.conf" and status == "up":
                task_config.private_link = True
            if not await aiopath.exists(config_path):
                raise ValueError(f"Rclone Config: {config_path} not Exists!")
        elif (
            status == "dl"
            and is_gdrive_link(path)
            or status == "up"
            and is_gdrive_id(path)
        ):
            token_path = TaskConfigPathResolvers.get_token_path(task_config, path)
            if token_path.startswith("tokens/") and status == "up":
                task_config.private_link = True
            if not await aiopath.exists(token_path):
                raise ValueError(f"NO TOKEN! {token_path} not Exists!")

    @staticmethod
    async def ensure_workdir(task_config):
        """Ensure download directory exists with proper permissions"""
        await makedirs(task_config.dir, exist_ok=True)
        # Set permissions to 777 so qBittorrent (UID 1000) can write
        chmod(task_config.dir, 0o777)


def is_gdrive_id(path):
    """Check if path is a Google Drive ID"""
    from bot.helper.ext_utils.links_utils import GDRIVE_ID_REGEX
    import re

    return bool(re.match(GDRIVE_ID_REGEX, path))
