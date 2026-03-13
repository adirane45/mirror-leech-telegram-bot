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
    @staticmethod
    def _get_ffmpeg_dict(task_config):
        """Get the appropriate ffmpeg dictionary"""
        if task_config.user_dict.get("FFMPEG_CMDS", None):
            return deepcopy(task_config.user_dict["FFMPEG_CMDS"])
        elif (
            "FFMPEG_CMDS" not in task_config.user_dict
            or not task_config.user_dict["FFMPEG_CMDS"]
        ) and Config.FFMPEG_CMDS:
            return deepcopy(Config.FFMPEG_CMDS)
        return None
    
    @staticmethod
    def _process_ffmpeg_key(task_config, key, ffmpeg_dict):
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
                    task_config.user_dict.get("FFMPEG_VARIABLES", {})
                    .get(key, {})
                    .get(str(ind), {})
                )
                if Counter(list(variables)) == Counter(list(ff_values.keys())):
                    cmds.append(vl.format(**ff_values))
            else:
                cmds.append(vl)
        return cmds
    
    @staticmethod
    def apply_ffmpeg_cmds(task_config):
        """
        Apply FFmpeg command templates with variable substitution
        Reduces nested conditional complexity
        """
        if not task_config.ffmpeg_cmds:
            return

        ffmpeg_dict = TaskConfigMapping._get_ffmpeg_dict(task_config)
        cmds = []
        for key in list(task_config.ffmpeg_cmds):
            cmds.extend(TaskConfigMapping._process_ffmpeg_key(task_config, key, ffmpeg_dict))
        task_config.ffmpeg_cmds = cmds
