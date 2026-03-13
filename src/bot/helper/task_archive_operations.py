"""
Archive Operations Processor
Handles extraction, compression, and file splitting operations
"""

from os import path as ospath
from os import walk
from shutil import move

from aiofiles.os import makedirs, remove

from bot import LOGGER
from bot.helper.ext_utils.bot_utils import sync_to_async
from bot.helper.ext_utils.files_utils import (
    SevenZ,
    get_base_name,
    get_path_size,
    is_archive,
    is_archive_split,
    is_first_archive_split,
    split_file,
)
from bot.helper.ext_utils.media_utils import FFMpeg, get_document_type
from bot.helper.mirror_leech_utils.status_utils.ffmpeg_status import FFmpegStatus
from bot.helper.mirror_leech_utils.status_utils.sevenz_status import SevenZStatus


class ArchiveOperationsProcessor:
    """Handles archive extraction, compression, and file splitting"""

    # ========== Extract Operations ==========

    @staticmethod
    def should_extract_file(file_):
        """Check if file should be extracted"""
        return is_first_archive_split(file_) or (
            is_archive(file_) and not file_.strip().lower().endswith(".rar")
        )

    @staticmethod
    async def collect_archives_to_extract(task_config, dl_path):
        """Collect all archive files that need extraction"""
        files_to_extract = []
        if task_config.is_file and is_archive(dl_path):
            files_to_extract.append(dl_path)
            return files_to_extract
        for dirpath, _, files in await sync_to_async(walk, dl_path, topdown=False):
            for file_ in files:
                if ArchiveOperationsProcessor.should_extract_file(file_):
                    files_to_extract.append(ospath.join(dirpath, file_))
        return files_to_extract

    @staticmethod
    async def cleanup_extracted_archives(task_config, dirpath, files):
        """Clean up archive files after extraction"""
        for file_ in files:
            if is_archive_split(file_) or is_archive(file_):
                del_path = ospath.join(dirpath, file_)
                try:
                    await remove(del_path)
                except:
                    task_config.is_cancelled = True

    @staticmethod
    async def _setup_extraction_status(task_config, sevenz, gid, task_dict, task_dict_lock):
        """Setup extraction status in task dictionary"""
        LOGGER.info(f"Extracting: {task_config.name}")
        async with task_dict_lock:
            task_dict[task_config.mid] = SevenZStatus(
                task_config, sevenz, gid, "Extract"
            )
    
    @staticmethod
    async def _extract_file_at_path(task_config, sevenz, f_path, dirpath, pswd):
        """Extract a single file and return extraction path and code"""
        task_config.proceed_count += 1
        t_path = get_base_name(f_path) if task_config.is_file else dirpath
        if not task_config.is_file:
            task_config.subname = ospath.basename(f_path)
        code = await sevenz.extract(f_path, t_path, pswd)
        return t_path, code
    
    @staticmethod
    async def _process_directory_files(task_config, sevenz, dirpath, files, pswd):
        """Process all extractable files in a directory"""
        code = 0
        t_path = dirpath
        for file_ in files:
            if task_config.is_cancelled:
                return t_path, code, True
            if ArchiveOperationsProcessor.should_extract_file(file_):
                f_path = ospath.join(dirpath, file_)
                t_path, code = await ArchiveOperationsProcessor._extract_file_at_path(
                    task_config, sevenz, f_path, dirpath, pswd
                )
        return t_path, code, False
    
    @staticmethod
    async def proceed_extract(task_config, dl_path, gid, task_dict, task_dict_lock):
        """Extract archive files"""
        pswd = task_config.extract if isinstance(task_config.extract, str) else ""
        task_config.files_to_proceed = (
            await ArchiveOperationsProcessor.collect_archives_to_extract(
                task_config, dl_path
            )
        )

        if not task_config.files_to_proceed:
            return dl_path

        t_path = dl_path
        sevenz = SevenZ(task_config)
        await ArchiveOperationsProcessor._setup_extraction_status(
            task_config, sevenz, gid, task_dict, task_dict_lock
        )

        for dirpath, _, files in await sync_to_async(
            walk, task_config.up_dir or task_config.dir, topdown=False
        ):
            t_path, code, cancelled = await ArchiveOperationsProcessor._process_directory_files(
                task_config, sevenz, dirpath, files, pswd
            )
            if cancelled:
                return False
            if code == 0:
                await ArchiveOperationsProcessor.cleanup_extracted_archives(
                    task_config, dirpath, files
                )

        if task_config.proceed_count == 0:
            LOGGER.info("No files able to extract!")
        return t_path if task_config.is_file and code == 0 else dl_path

    # ========== Compress Operations ==========

    @staticmethod
    async def proceed_compress(task_config, dl_path, gid, task_dict, task_dict_lock):
        """Compress files into archive"""
        pswd = task_config.compress if isinstance(task_config.compress, str) else ""
        if task_config.is_leech and task_config.is_file:
            new_folder = ospath.splitext(dl_path)[0]
            name = ospath.basename(dl_path)
            await makedirs(new_folder, exist_ok=True)
            new_dl_path = f"{new_folder}/{name}"
            await sync_to_async(move, dl_path, new_dl_path)
            dl_path = new_dl_path
            up_path = f"{new_dl_path}.zip"
            task_config.is_file = False
        else:
            up_path = f"{dl_path}.zip"

        sevenz = SevenZ(task_config)
        async with task_dict_lock:
            task_dict[task_config.mid] = SevenZStatus(task_config, sevenz, gid, "Zip")
        return await sevenz.zip(dl_path, up_path, pswd)

    # ========== Split Operations ==========

    @staticmethod
    async def collect_files_to_split(task_config, dl_path):
        """Collect files that need splitting"""
        files_to_split = {}
        if task_config.is_file:
            f_size = await get_path_size(dl_path)
            if f_size > task_config.split_size:
                files_to_split[dl_path] = [f_size, ospath.basename(dl_path)]
        else:
            for dirpath, _, files in await sync_to_async(walk, dl_path, topdown=False):
                for file_ in files:
                    f_path = ospath.join(dirpath, file_)
                    f_size = await get_path_size(f_path)
                    if f_size > task_config.split_size:
                        files_to_split[f_path] = [f_size, file_]
        return files_to_split

    @staticmethod
    def _calculate_split_size(task_config, f_size):
        parts = -(-f_size // task_config.split_size)
        if task_config.equal_splits:
            split_size = (f_size // parts) + (f_size % parts)
        else:
            split_size = task_config.split_size
        return parts, split_size

    @staticmethod
    async def _run_split_operation(task_config, ffmpeg, f_path, file_, parts, split_size):
        if not task_config.as_doc and (await get_document_type(f_path))[0]:
            task_config.progress = True
            return await ffmpeg.split(f_path, file_, parts, split_size)

        task_config.progress = False
        return await split_file(f_path, split_size, task_config)

    @staticmethod
    async def _cleanup_original_after_split(task_config, f_path, f_size, res):
        if not (res or f_size >= task_config.max_split_size):
            return
        try:
            await remove(f_path)
        except:
            task_config.is_cancelled = True

    @staticmethod
    async def proceed_split(task_config, dl_path, gid, task_dict, task_dict_lock):
        """Split large files"""
        task_config.files_to_proceed = (
            await ArchiveOperationsProcessor.collect_files_to_split(
                task_config, dl_path
            )
        )

        if not task_config.files_to_proceed:
            return dl_path

        ffmpeg = FFMpeg(task_config)
        async with task_dict_lock:
            task_dict[task_config.mid] = FFmpegStatus(task_config, ffmpeg, gid, "Split")
        LOGGER.info(f"Splitting: {task_config.name}")

        for f_path, (f_size, file_) in task_config.files_to_proceed.items():
            task_config.proceed_count += 1
            if task_config.is_file:
                task_config.subsize = task_config.size
            else:
                task_config.subsize = f_size
                task_config.subname = file_

            parts, split_size = ArchiveOperationsProcessor._calculate_split_size(
                task_config,
                f_size,
            )
            res = await ArchiveOperationsProcessor._run_split_operation(
                task_config,
                ffmpeg,
                f_path,
                file_,
                parts,
                split_size,
            )

            if task_config.is_cancelled:
                return False

            await ArchiveOperationsProcessor._cleanup_original_after_split(
                task_config,
                f_path,
                f_size,
                res,
            )

        return dl_path
