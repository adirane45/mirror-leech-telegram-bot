"""
Task Configuration Mapping
Handles upload path mapping and FFmpeg command configuration
"""

from collections import Counter
from copy import deepcopy
from re import findall

from bot import Config


class TaskConfigMapping:
    """Handles complex configuration mappings"""

    @staticmethod
    def apply_upload_paths_mapping(task_config):
        """Apply upload path shortcut mappings"""
        if task_config.user_dict.get("UPLOAD_PATHS", False):
            if task_config.up_dest in task_config.user_dict["UPLOAD_PATHS"]:
                task_config.up_dest = task_config.user_dict["UPLOAD_PATHS"][
                    task_config.up_dest
                ]
            return
        if (
            "UPLOAD_PATHS" not in task_config.user_dict
            or not task_config.user_dict["UPLOAD_PATHS"]
        ) and Config.UPLOAD_PATHS:
            if task_config.up_dest in Config.UPLOAD_PATHS:
                task_config.up_dest = Config.UPLOAD_PATHS[task_config.up_dest]

    @staticmethod
    def apply_ffmpeg_cmds(task_config):
        """
        Apply FFmpeg command templates with variable substitution
        Reduces nested conditional complexity
        """
        if not task_config.ffmpeg_cmds:
            return

        # Get FFmpeg command dictionary
        if task_config.user_dict.get("FFMPEG_CMDS", None):
            ffmpeg_dict = deepcopy(task_config.user_dict["FFMPEG_CMDS"])
        elif (
            "FFMPEG_CMDS" not in task_config.user_dict
            or not task_config.user_dict["FFMPEG_CMDS"]
        ) and Config.FFMPEG_CMDS:
            ffmpeg_dict = deepcopy(Config.FFMPEG_CMDS)
        else:
            ffmpeg_dict = None

        cmds = []
        for key in list(task_config.ffmpeg_cmds):
            # Handle tuple keys
            if isinstance(key, tuple):
                cmds.extend(list(key))
                continue

            # Skip if key not in dictionary
            if ffmpeg_dict is None or key not in ffmpeg_dict.keys():
                continue

            # Process each command template
            for ind, vl in enumerate(ffmpeg_dict[key]):
                # Check for variables to substitute
                if variables := set(findall(r"\{(.*?)\}", vl)):
                    ff_values = (
                        task_config.user_dict.get("FFMPEG_VARIABLES", {})
                        .get(key, {})
                        .get(str(ind), {})
                    )
                    # Only substitute if all variables are provided
                    if Counter(list(variables)) == Counter(list(ff_values.keys())):
                        cmds.append(vl.format(**ff_values))
                else:
                    # No variables, use as-is
                    cmds.append(vl)

        task_config.ffmpeg_cmds = cmds
