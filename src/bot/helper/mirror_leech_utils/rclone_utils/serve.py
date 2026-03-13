from asyncio import create_subprocess_exec
from configparser import RawConfigParser
from io import StringIO

from aiofiles import open as aiopen
from aiofiles.os import path as aiopath

from .... import LOGGER
from ....core.config_manager import Config

RcloneServe = []


def _is_rclone_serve_enabled():
    return bool(Config.RCLONE_SERVE_URL)


def _build_rclone_serve_command():
    cmd = [
        "rclone",
        "serve",
        "http",
        "--config",
        "rclone.conf",
        "--no-modtime",
        "combine:",
        "--addr",
        f":{Config.RCLONE_SERVE_PORT}",
        "--vfs-cache-mode",
        "full",
        "--vfs-cache-max-age",
        "1m0s",
        "--buffer-size",
        "64M",
        "-v",
        "--log-file",
        "rlog.txt",
    ]
    if (user := Config.RCLONE_SERVE_USER) and (pswd := Config.RCLONE_SERVE_PASS):
        cmd.extend(("--user", user, "--pass", pswd))
    return cmd


def _build_combine_upstreams(config):
    return " ".join(f"{remote}={remote}:" for remote in config.sections())


async def _stop_existing_rclone_serve():
    if not RcloneServe:
        return
    try:
        RcloneServe[0].kill()
        RcloneServe.clear()
    except (ProcessLookupError, IndexError) as e:
        LOGGER.warning(f"Failed to kill RcloneServe: {e}")


async def _load_rclone_config():
    config = RawConfigParser()
    async with aiopen("rclone.conf", "r") as f:
        contents = await f.read()
        config.read_string(contents)
    return config


async def _ensure_combine_section(config):
    if config.has_section("combine"):
        return
    upstreams = _build_combine_upstreams(config)
    config.add_section("combine")
    config.set("combine", "type", "combine")
    config.set("combine", "upstreams", upstreams)
    config_buffer = StringIO()
    config.write(config_buffer, space_around_delimiters=False)
    async with aiopen("rclone.conf", "w") as f:
        await f.write(config_buffer.getvalue())


async def rclone_serve_booter():
    if not _is_rclone_serve_enabled() or not await aiopath.exists("rclone.conf"):
        await _stop_existing_rclone_serve()
        return

    config = await _load_rclone_config()
    await _ensure_combine_section(config)
    await _stop_existing_rclone_serve()

    cmd = _build_rclone_serve_command()
    rcs = await create_subprocess_exec(*cmd)
    RcloneServe.append(rcs)
