"""
Name Substitution Processor
Handles file and directory name substitution with regex patterns
"""

from os import path as ospath, walk
from re import sub, I
from aiofiles.os import move

from bot import LOGGER
from bot.helper.ext_utils.bot_utils import sync_to_async


class NameSubstitutionProcessor:
    """Handles name substitution operations"""

    @staticmethod
    def perform_substitution(name, substitutions):
        """Apply regex substitutions to a filename"""
        for substitution in substitutions:
            sen = False
            pattern = substitution[0]
            if pattern.startswith('"') and pattern.endswith('"'):
                pattern = pattern.strip('"')

            if len(substitution) > 1:
                if len(substitution) > 2:
                    sen = substitution[2] == "s"
                    res = substitution[1]
                elif len(substitution[1]) == 0:
                    res = " "
                else:
                    res = substitution[1]
            else:
                res = ""

            try:
                name = sub(pattern, res, name, flags=I if sen else 0)
            except Exception as e:
                LOGGER.error(
                    f"Substitute Error: pattern: {pattern} res: {res}. Error: {e}"
                )
                return False

            if len(name.encode()) > 255:
                LOGGER.error(f"Substitute: {name} is too long")
                return False
        return name

    @staticmethod
    async def substitute_single_file(task_config, dl_path):
        """Apply substitution to a single file"""
        up_dir, name = dl_path.rsplit("/", 1)
        new_name = NameSubstitutionProcessor.perform_substitution(
            name, task_config.name_sub
        )
        if not new_name:
            return dl_path
        new_path = ospath.join(up_dir, new_name)
        await move(dl_path, new_path)
        return new_path

    @staticmethod
    async def substitute_directory(task_config, dl_path):
        """Apply substitution to all files in a directory"""
        for dirpath, _, files in await sync_to_async(walk, dl_path, topdown=False):
            for file_ in files:
                f_path = ospath.join(dirpath, file_)
                new_name = NameSubstitutionProcessor.perform_substitution(
                    file_, task_config.name_sub
                )
                if not new_name:
                    continue
                await move(f_path, ospath.join(dirpath, new_name))
        return dl_path

    @staticmethod
    async def substitute(task_config, dl_path):
        """
        Main substitution method
        Reduces cc=16 to simpler dispatch logic
        """
        if task_config.is_file:
            return await NameSubstitutionProcessor.substitute_single_file(
                task_config, dl_path
            )
        else:
            return await NameSubstitutionProcessor.substitute_directory(
                task_config, dl_path
            )
