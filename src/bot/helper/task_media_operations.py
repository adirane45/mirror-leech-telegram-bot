"""
Media Operations Processor
Handles media conversion, screenshot generation, and sample video creation
"""

from aiofiles.os import path as aiopath, makedirs, remove
from asyncio import gather
from os import path as ospath, walk
from shutil import move

from bot import LOGGER, cpu_eater_lock
from bot.helper.ext_utils.bot_utils import sync_to_async
from bot.helper.ext_utils.files_utils import get_path_size
from bot.helper.ext_utils.media_utils import FFMpeg, get_document_type, take_ss
from bot.helper.mirror_leech_utils.status_utils.ffmpeg_status import FFmpegStatus


class MediaOperationsProcessor:
    """Handles all media processing operations"""

    @staticmethod
    def parse_convert_setting(setting):
        """Parse conversion setting string"""
        if not setting:
            return "", "", []
        data = setting.split()
        ext = data[0].lower() if data else ""
        status = ""
        ext_list = []
        if len(data) > 2:
            if "+" in data[1]:
                status = "+"
            elif "-" in data[1]:
                status = "-"
            ext_list = [f".{ext_.lower()}" for ext_ in data[2:]]
        return ext, status, ext_list

    @staticmethod
    def should_convert_video(f_path, vext, vstatus, fvext):
        """Check if video file should be converted"""
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
    def should_convert_audio(f_path, aext, astatus, faext):
        """Check if audio file should be converted"""
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

    @staticmethod
    async def collect_media_files(task_config, dl_path):
        """Collect all media files from path"""
        if task_config.is_file:
            return [dl_path]
        all_files = []
        for dirpath, _, files in await sync_to_async(walk, dl_path, topdown=False):
            for file_ in files:
                all_files.append(ospath.join(dirpath, file_))
        return all_files

    @staticmethod
    async def generate_screenshots(task_config, dl_path):
        """Generate screenshots for video files"""
        ss_nb = (
            int(task_config.screen_shots)
            if isinstance(task_config.screen_shots, str)
            else 10
        )
        if task_config.is_file:
            if (await get_document_type(dl_path))[0]:
                LOGGER.info(f"Creating Screenshot for: {dl_path}")
                res = await take_ss(dl_path, ss_nb)
                if res:
                    new_folder = ospath.splitext(dl_path)[0]
                    name = ospath.basename(dl_path)
                    await makedirs(new_folder, exist_ok=True)
                    await gather(
                        sync_to_async(move, dl_path, f"{new_folder}/{name}"),
                        sync_to_async(move, res, new_folder),
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

    @staticmethod
    async def convert_media(task_config, dl_path, gid, task_dict, task_dict_lock):
        """Convert media files to specified formats"""
        vext, vstatus, fvext = MediaOperationsProcessor.parse_convert_setting(
            task_config.convert_video
        )
        aext, astatus, faext = MediaOperationsProcessor.parse_convert_setting(
            task_config.convert_audio
        )

        task_config.files_to_proceed = {}
        all_files = await MediaOperationsProcessor.collect_media_files(
            task_config, dl_path
        )

        for f_path in all_files:
            is_video, is_audio, _ = await get_document_type(f_path)
            if is_video and MediaOperationsProcessor.should_convert_video(
                f_path, vext, vstatus, fvext
            ):
                task_config.files_to_proceed[f_path] = "video"
            elif is_audio and not is_video and MediaOperationsProcessor.should_convert_audio(
                f_path, aext, astatus, faext
            ):
                task_config.files_to_proceed[f_path] = "audio"

        if task_config.files_to_proceed:
            ffmpeg = FFMpeg(task_config)
            async with task_dict_lock:
                task_dict[task_config.mid] = FFmpegStatus(
                    task_config, ffmpeg, gid, "Convert"
                )
            task_config.progress = False
            async with cpu_eater_lock:
                task_config.progress = True
                for f_path, f_type in task_config.files_to_proceed.items():
                    task_config.proceed_count += 1
                    LOGGER.info(f"Converting: {f_path}")
                    if task_config.is_file:
                        task_config.subsize = task_config.size
                    else:
                        task_config.subsize = await get_path_size(f_path)
                        task_config.subname = ospath.basename(f_path)

                    if f_type == "video":
                        res = await ffmpeg.convert_video(f_path, vext)
                    else:
                        res = await ffmpeg.convert_audio(f_path, aext)

                    if res:
                        try:
                            await remove(f_path)
                        except:
                            task_config.is_cancelled = True
                            return False
                    if task_config.is_file:
                        return res
        return dl_path

    @staticmethod
    def parse_sample_settings(sample_video):
        """Parse sample video settings"""
        data = sample_video.split(":") if isinstance(sample_video, str) else []
        if not data:
            return 60, 4
        sample_duration = int(data[0]) if data[0] else 60
        part_duration = int(data[1]) if len(data) > 1 else 4
        return sample_duration, part_duration

    @staticmethod
    async def collect_video_files_for_sample(task_config, dl_path):
        """Collect video files for sampling"""
        files_to_sample = {}
        if task_config.is_file and (await get_document_type(dl_path))[0]:
            files_to_sample[dl_path] = ospath.basename(dl_path)
            return files_to_sample
        for dirpath, _, files in await sync_to_async(walk, dl_path, topdown=False):
            for file_ in files:
                f_path = ospath.join(dirpath, file_)
                if (await get_document_type(f_path))[0]:
                    files_to_sample[f_path] = file_
        return files_to_sample

    @staticmethod
    async def generate_sample_video(task_config, dl_path, gid, task_dict, task_dict_lock):
        """Generate sample video clips"""
        sample_duration, part_duration = MediaOperationsProcessor.parse_sample_settings(
            task_config.sample_video
        )
        task_config.files_to_proceed = (
            await MediaOperationsProcessor.collect_video_files_for_sample(
                task_config, dl_path
            )
        )

        if task_config.files_to_proceed:
            ffmpeg = FFMpeg(task_config)
            async with task_dict_lock:
                task_dict[task_config.mid] = FFmpegStatus(
                    task_config, ffmpeg, gid, "Sample Video"
                )
            task_config.progress = False
            async with cpu_eater_lock:
                task_config.progress = True
                LOGGER.info(f"Creating Sample video: {task_config.name}")
                for f_path, file_ in task_config.files_to_proceed.items():
                    task_config.proceed_count += 1
                    if task_config.is_file:
                        task_config.subsize = task_config.size
                    else:
                        task_config.subsize = await get_path_size(f_path)
                        task_config.subname = file_
                    res = await ffmpeg.sample_video(
                        f_path, sample_duration, part_duration
                    )
                    if res and task_config.is_file:
                        new_folder = ospath.splitext(f_path)[0]
                        await makedirs(new_folder, exist_ok=True)
                        await gather(
                            sync_to_async(move, f_path, f"{new_folder}/{file_}"),
                            sync_to_async(move, res, f"{new_folder}/SAMPLE.{file_}"),
                        )
                        return new_folder
        return dl_path
