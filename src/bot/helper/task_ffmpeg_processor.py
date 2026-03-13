"""
FFmpeg Task Processor
Handles all FFmpeg processing operations
Extracts complex cc=23, 80-line proceed_ffmpeg method
"""

from os import path as ospath
from os import walk
from shlex import split
from shutil import move

from aiofiles.os import listdir, makedirs
from aiofiles.os import path as aiopath
from aiofiles.os import remove
from aioshutil import rmtree

from bot import LOGGER, cores, cpu_eater_lock
from bot.helper.ext_utils.bot_utils import sync_to_async
from bot.helper.ext_utils.files_utils import get_path_size
from bot.helper.ext_utils.links_utils import is_telegram_link
from bot.helper.ext_utils.media_utils import FFMpeg, get_document_type
from bot.helper.mirror_leech_utils.status_utils.ffmpeg_status import FFmpegStatus


async def get_tg_link_message(link):
    """Get telegram message from link"""
    from bot.helper.telegram_helper.message_utils import get_tg_link_message as _get_msg

    return await _get_msg(link)


async def temp_download(msg):
    """Download temp file from telegram message"""
    from bot.helper.telegram_helper.message_utils import temp_download as _temp_download

    return await _temp_download(msg)


class FFmpegTaskProcessor:
    """Handles FFmpeg processing operations"""

    @staticmethod
    def build_ffmpeg_cmds(ffmpeg_cmds):
        """Parse and build FFmpeg command list"""
        return [
            [part.strip() for part in split(item) if part.strip()]
            for item in ffmpeg_cmds
        ]

    @staticmethod
    def get_ffmpeg_input_file(cmd, input_indexes):
        """Extract the main input file from FFmpeg command"""
        return next(
            (
                cmd[index + 1]
                for index in input_indexes
                if cmd[index + 1].startswith("mltb")
            ),
            "",
        )

    @staticmethod
    def get_ffmpeg_ext(input_file):
        """Get file extension type from input file"""
        if input_file.strip().endswith(".video"):
            return "video"
        if input_file.strip().endswith(".audio"):
            return "audio"
        if "." not in input_file:
            return "all"
        return ospath.splitext(input_file)[-1].lower()

    @staticmethod
    async def prepare_ffmpeg_cmd(cmd, input_indexes, target_path, inputs):
        """Prepare FFmpeg command with variable substitution"""
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

    @staticmethod
    async def ensure_ffmpeg_status(task_config, ffmpeg, gid, checked, task_dict, task_dict_lock):
        """Ensure FFmpeg status is set up and locks acquired"""
        if checked:
            return True
        async with task_dict_lock:
            task_dict[task_config.mid] = FFmpegStatus(task_config, ffmpeg, gid, "FFmpeg")
        task_config.progress = False
        await cpu_eater_lock.acquire()
        task_config.progress = True
        return True

    @staticmethod
    async def cleanup_ffmpeg_inputs(inputs):
        """Clean up temporary input files"""
        for inp in inputs.values():
            if "/temp/" in inp and await aiopath.exists(inp):
                await remove(inp)

    @staticmethod
    def should_process_file(f_path, ext, is_video, is_audio):
        """Check if file should be processed based on type and extension"""
        if not is_video and not is_audio:
            return False
        if is_video and ext == "audio":
            return False
        if is_audio and not is_video and ext == "video":
            return False
        if ext not in ["all", "audio", "video"] and not f_path.strip().lower().endswith(ext):
            return False
        return True

    @staticmethod
    @staticmethod
    async def _prepare_file_structure(dl_path):
        """Prepare file structure for FFmpeg processing"""
        new_folder = ospath.splitext(dl_path)[0]
        name = ospath.basename(dl_path)
        await makedirs(new_folder, exist_ok=True)
        file_path = f"{new_folder}/{name}"
        await move(dl_path, file_path)
        return new_folder, file_path
    
    @staticmethod
    async def _cleanup_after_ffmpeg(dl_path, new_folder, file_path, res, delete_files, task_config):
        """Cleanup files after FFmpeg processing"""
        if res:
            if delete_files:
                await remove(file_path)
                if len(await listdir(new_folder)) == 1:
                    folder = new_folder.rsplit("/", 1)[0]
                    task_config.name = ospath.basename(res[0])
                    if task_config.name.startswith("ffmpeg"):
                        task_config.name = task_config.name.split(".", 1)[-1]
                    dl_path = ospath.join(folder, task_config.name)
                    await move(res[0], dl_path)
                    await rmtree(new_folder)
                else:
                    dl_path = new_folder
                    task_config.name = new_folder.rsplit("/", 1)[-1]
            else:
                dl_path = new_folder
                task_config.name = new_folder.rsplit("/", 1)[-1]
        else:
            await move(file_path, dl_path)
            await rmtree(new_folder)
        return dl_path
    
    @staticmethod
    async def _process_ffmpeg_command(task_config, ffmpeg, cmd, dl_path, file_path, input_indexes, inputs, checked, gid, task_dict, task_dict_lock):
        """Process a single FFmpeg command"""
        delete_files = "-del" in cmd
        if delete_files:
            cmd.remove("-del")

        input_file = FFmpegTaskProcessor.get_ffmpeg_input_file(cmd, input_indexes)
        if not input_file:
            LOGGER.error("Wrong FFmpeg cmd!")
            return dl_path, checked

        ext = FFmpegTaskProcessor.get_ffmpeg_ext(input_file)
        is_video, is_audio, _ = await get_document_type(dl_path)
        if not FFmpegTaskProcessor.should_process_file(dl_path, ext, is_video, is_audio):
            return None, checked

        new_folder, file_path = await FFmpegTaskProcessor._prepare_file_structure(dl_path)
        
        if not checked:
            checked = await FFmpegTaskProcessor.ensure_ffmpeg_status(
                task_config, ffmpeg, gid, checked, task_dict, task_dict_lock
            )

        LOGGER.info(f"Running ffmpeg cmd for: {file_path}")
        var_cmd = await FFmpegTaskProcessor.prepare_ffmpeg_cmd(
            cmd, input_indexes, file_path, inputs
        )
        task_config.subsize = task_config.size
        res = await ffmpeg.ffmpeg_cmds(var_cmd, file_path)
        
        dl_path = await FFmpegTaskProcessor._cleanup_after_ffmpeg(
            dl_path, new_folder, file_path, res, delete_files, task_config
        )
        return dl_path, checked
    
    @staticmethod
    async def process_single_file(task_config, ffmpeg, cmds, dl_path, inputs, gid, checked, task_dict, task_dict_lock):
        """Process a single file with FFmpeg"""
        file_path = dl_path
        for ffmpeg_cmd in cmds:
            task_config.proceed_count = 0
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

            input_indexes = [
                index for index, value in enumerate(cmd) if value == "-i"
            ]
            
            result = await FFmpegTaskProcessor._process_ffmpeg_command(
                task_config, ffmpeg, cmd, dl_path, file_path, input_indexes, inputs, checked, gid, task_dict, task_dict_lock
            )
            if result[0] is None:
                break
            dl_path, checked = result

        return dl_path, checked

    @staticmethod
    async def process_directory(task_config, ffmpeg, cmds, dl_path, inputs, gid, checked, task_dict, task_dict_lock):
        """Process all eligible files in a directory with FFmpeg"""
        for ffmpeg_cmd in cmds:
            result = await FFmpegTaskProcessor._process_single_ffmpeg_cmd(
                task_config, ffmpeg, ffmpeg_cmd, dl_path, inputs, gid, checked, task_dict, task_dict_lock
            )
            if result is False:
                return False, checked
            elif result is not None:
                checked = result
        return dl_path, checked

    @staticmethod
    async def _process_single_ffmpeg_cmd(task_config, ffmpeg, ffmpeg_cmd, dl_path, inputs, gid, checked, task_dict, task_dict_lock):
        task_config.proceed_count = 0
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

        delete_files = "-del" in cmd
        if delete_files:
            cmd.remove("-del")

        input_indexes = [
            index for index, value in enumerate(cmd) if value == "-i"
        ]
        input_file = FFmpegTaskProcessor.get_ffmpeg_input_file(cmd, input_indexes)
        if not input_file:
            LOGGER.error("Wrong FFmpeg cmd!")
            return None

        ext = FFmpegTaskProcessor.get_ffmpeg_ext(input_file)

        for dirpath, _, files in await sync_to_async(walk, dl_path, topdown=False):
            for file_ in files:
                if task_config.is_cancelled:
                    return False

                f_path = ospath.join(dirpath, file_)
                is_video, is_audio, _ = await get_document_type(f_path)

                if not FFmpegTaskProcessor.should_process_file(f_path, ext, is_video, is_audio):
                    continue

                checked = await FFmpegTaskProcessor._process_single_file_with_ffmpeg(
                    task_config, ffmpeg, f_path, file_, dirpath, cmd, input_indexes, inputs, 
                    gid, checked, delete_files, task_dict, task_dict_lock
                )
        return checked

    @staticmethod
    async def _process_single_file_with_ffmpeg(task_config, ffmpeg, f_path, file_, dirpath, 
                                                cmd, input_indexes, inputs, gid, checked, 
                                                delete_files, task_dict, task_dict_lock):
        task_config.proceed_count += 1
        var_cmd = await FFmpegTaskProcessor.prepare_ffmpeg_cmd(
            cmd, input_indexes, f_path, inputs
        )

        if not checked:
            checked = await FFmpegTaskProcessor.ensure_ffmpeg_status(
                task_config, ffmpeg, gid, checked, task_dict, task_dict_lock
            )

        LOGGER.info(f"Running ffmpeg cmd for: {f_path}")
        task_config.subsize = await get_path_size(f_path)
        task_config.subname = file_
        res = await ffmpeg.ffmpeg_cmds(var_cmd, f_path)

        if res and delete_files:
            await remove(f_path)
            if len(res) == 1:
                file_name = ospath.basename(res[0])
                if file_name.startswith("ffmpeg"):
                    newname = file_name.split(".", 1)[-1]
                    newres = ospath.join(dirpath, newname)
                    await sync_to_async(move, res[0], newres)
        return checked

    @staticmethod
    async def proceed_ffmpeg(task_config, dl_path, gid, task_dict, task_dict_lock):
        """
        Main FFmpeg processing method
        Reduced from 80 lines with cc=23 to modular approach
        """
        checked = False
        inputs = {}
        cmds = FFmpegTaskProcessor.build_ffmpeg_cmds(task_config.ffmpeg_cmds)

        try:
            ffmpeg = FFMpeg(task_config)

            if await aiopath.isfile(dl_path):
                dl_path, checked = await FFmpegTaskProcessor.process_single_file(
                    task_config, ffmpeg, cmds, dl_path, inputs, gid, checked, task_dict, task_dict_lock
                )
            else:
                dl_path, checked = await FFmpegTaskProcessor.process_directory(
                    task_config, ffmpeg, cmds, dl_path, inputs, gid, checked, task_dict, task_dict_lock
                )

            await FFmpegTaskProcessor.cleanup_ffmpeg_inputs(inputs)
        finally:
            if checked:
                cpu_eater_lock.release()

        return dl_path
