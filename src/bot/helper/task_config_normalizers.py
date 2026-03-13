"""
Task Configuration Normalizers
Handles normalization of links, tokens, and upload destinations
"""

from bot.helper.ext_utils.links_utils import is_gdrive_id, is_gdrive_link, is_rclone_path
from bot.helper.mirror_leech_utils.gdrive_utils.list import GoogleDriveList
from bot.helper.mirror_leech_utils.rclone_utils.list import RcloneList
from bot.helper.task_config_path_resolvers import TaskConfigPathResolvers


class TaskConfigNormalizers:
    """Handles normalization of links and tokens"""

    @staticmethod
    async def normalize_link_tokens(task_config):
        """Normalize link tokens for gdrive/rclone"""
        if task_config.link in ["rcl", "gdl"] or task_config.is_jd:
            return
        if is_rclone_path(task_config.link):
            if not task_config.link.startswith("mrcc:") and task_config.user_dict.get(
                "USER_TOKENS", False
            ):
                task_config.link = f"mrcc:{task_config.link}"
            await TaskConfigPathResolvers.is_token_exists(task_config, task_config.link, "dl")
            return
        if is_gdrive_link(task_config.link):
            if not task_config.link.startswith(
                ("mtp:", "tp:", "sa:")
            ) and task_config.user_dict.get("USER_TOKENS", False):
                task_config.link = f"mtp:{task_config.link}"
            await TaskConfigPathResolvers.is_token_exists(task_config, task_config.link, "dl")

    @staticmethod
    async def resolve_link_shortcuts(task_config):
        """Resolve 'rcl' and 'gdl' shortcuts to actual paths"""
        if task_config.link == "rcl":
            if not task_config.is_ytdlp and not task_config.is_jd:
                task_config.link = await RcloneList(task_config).get_rclone_path("rcd")
                if not is_rclone_path(task_config.link):
                    raise ValueError(task_config.link)
        elif task_config.link == "gdl":
            if not task_config.is_ytdlp and not task_config.is_jd:
                task_config.link = await GoogleDriveList(task_config).get_target_id("gdd")
                if not is_gdrive_id(task_config.link):
                    raise ValueError(task_config.link)

    @staticmethod
    async def normalize_up_dest_tokens(task_config):
        """Normalize upload destination tokens"""
        if task_config.up_dest in ["rcl", "gdl"]:
            return
        if is_gdrive_id(task_config.up_dest):
            if not task_config.up_dest.startswith(
                ("mtp:", "tp:", "sa:")
            ) and task_config.user_dict.get("USER_TOKENS", False):
                task_config.up_dest = f"mtp:{task_config.up_dest}"
        elif is_rclone_path(task_config.up_dest):
            if not task_config.up_dest.startswith(
                "mrcc:"
            ) and task_config.user_dict.get("USER_TOKENS", False):
                task_config.up_dest = f"mrcc:{task_config.up_dest}"
            task_config.up_dest = task_config.up_dest.strip("/")
        else:
            raise ValueError("Wrong Upload Destination!")
        await TaskConfigPathResolvers.is_token_exists(task_config, task_config.up_dest, "up")
