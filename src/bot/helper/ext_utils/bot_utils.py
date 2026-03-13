from asyncio import create_subprocess_exec, create_subprocess_shell, run_coroutine_threadsafe, sleep
from asyncio.subprocess import PIPE
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps

from httpx import AsyncClient

from ... import bot_loop, user_data
from ...core.config_manager import Config
from ...core.telegram_manager import TgClient
from ..telegram_helper.button_build import ButtonMaker
from .help_messages import CLONE_HELP_DICT, MIRROR_HELP_DICT, YT_HELP_DICT
from .telegraph_helper import telegraph

COMMAND_USAGE = {}
BOOL_ARG_SET = {
    "-b",
    "-e",
    "-z",
    "-s",
    "-j",
    "-d",
    "-sv",
    "-ss",
    "-f",
    "-fd",
    "-fu",
    "-sync",
    "-hl",
    "-doc",
    "-med",
    "-ut",
    "-bt",
}
DIRECT_BOOL_ARGS = {
    "-s",
    "-j",
    "-f",
    "-fd",
    "-fu",
    "-sync",
    "-hl",
    "-doc",
    "-med",
    "-ut",
    "-bt",
}


async def is_premium_user(user_id):
    """
    Check if user is a premium telegram user

    Args:
        user_id: Telegram user ID

    Returns:
        bool: True if user is premium, False otherwise
    """
    try:
        return TgClient.IS_PREMIUM_USER if TgClient.user and TgClient.user.id == user_id else False
    except:
        return False

THREAD_POOL = ThreadPoolExecutor(max_workers=500)


class SetInterval:
    def __init__(self, interval, action, *args, **kwargs):
        self.interval = interval
        self.action = action
        self.task = bot_loop.create_task(self._set_interval(*args, **kwargs))

    async def _set_interval(self, *args, **kwargs):
        from asyncio import iscoroutinefunction
        while True:
            await sleep(self.interval)
            if iscoroutinefunction(self.action):
                await self.action(*args, **kwargs)
            else:
                # If not async, run in thread pool to avoid blocking
                result = self.action(*args, **kwargs)
                # Check if result is awaitable (e.g., coroutine)
                if hasattr(result, '__await__'):
                    await result

    def cancel(self):
        self.task.cancel()


def _build_command_usage(help_dict, command_key):
    buttons = ButtonMaker()
    for name in list(help_dict.keys())[1:]:
        buttons.data_button(name, f"help {command_key} {name}")
    buttons.data_button("Close", "help close")
    COMMAND_USAGE[command_key] = [help_dict["main"], buttons.build_menu(3)]
    buttons.reset()


def create_help_buttons():
    _build_command_usage(MIRROR_HELP_DICT, "mirror")
    _build_command_usage(YT_HELP_DICT, "yt")
    _build_command_usage(CLONE_HELP_DICT, "clone")


def bt_selection_buttons(id_):
    gid = id_[:12] if len(id_) > 25 else id_
    pin = "".join([n for n in id_ if n.isdigit()][:4])
    buttons = ButtonMaker()
    if Config.WEB_PINCODE:
        buttons.url_button("Select Files", f"{Config.BASE_URL}/app/files?gid={id_}")
        buttons.data_button("Pincode", f"sel pin {gid} {pin}")
    else:
        buttons.url_button(
            "Select Files", f"{Config.BASE_URL}/app/files?gid={id_}&pin={pin}"
        )
    buttons.data_button("Done Selecting", f"sel done {gid} {id_}")
    buttons.data_button("Cancel", f"sel cancel {gid}")
    return buttons.build_menu(2)


async def get_telegraph_list(telegraph_content):
    path = [
        (
            await telegraph.create_page(
                title="Mirror-Leech-Bot Drive Search", content=content
            )
        )["path"]
        for content in telegraph_content
    ]
    if len(path) > 1:
        await telegraph.edit_telegraph(path, telegraph_content)
    buttons = ButtonMaker()
    buttons.url_button("🔎 VIEW", f"https://telegra.ph/{path[0]}")
    return buttons.build_menu(1)


def arg_parser(items, arg_base):
    if not items:
        return

    arg_start = -1
    i = 0
    total = len(items)

    while i < total:
        part = items[i]

        if part not in arg_base:
            i += 1
            continue

        if arg_start == -1:
            arg_start = i

        if _is_true_flag_without_value(part, i, total):
            arg_base[part] = True
            i += 1
            continue

        consumed = _collect_and_assign_arg_values(items, i, part, arg_base)
        i += consumed + 1

    _assign_link_argument(items, arg_base, arg_start)


def _is_true_flag_without_value(part, index, total):
    return (index + 1 == total and part in BOOL_ARG_SET) or part in DIRECT_BOOL_ARGS


def _collect_and_assign_arg_values(items, index, part, arg_base):
    sub_list = []
    total = len(items)

    for j in range(index + 1, total):
        token = items[j]
        if token in arg_base and _should_stop_collecting(part, token, sub_list):
            if part in BOOL_ARG_SET and not sub_list:
                arg_base[part] = True
            break
        sub_list.append(token)

    if sub_list:
        _assign_parsed_value(arg_base, part, " ".join(sub_list))
    return len(sub_list)


def _should_stop_collecting(part, token, sub_list):
    if part == "-c" and token == "-c":
        return False
    if not sub_list:
        return True
    if part != "-ff":
        return True
    joined = " ".join(sub_list).strip()
    if joined.startswith("[") and joined.endswith("]"):
        return True
    if not joined.startswith("["):
        return True
    return False


def _assign_parsed_value(arg_base, part, value):
    if part != "-ff":
        arg_base[part] = value
        return
    if not value.strip().startswith("["):
        arg_base[part].add(value)
        return
    try:
        arg_base[part].add(tuple(eval(value)))
    except Exception:
        pass


def _assign_link_argument(items, arg_base, arg_start):
    if "link" not in arg_base:
        return
    link_items = items[:arg_start] if arg_start != -1 else items
    if link_items:
        arg_base["link"] = " ".join(link_items)


def get_size_bytes(size):
    size = size.lower()
    if "k" in size:
        size = int(float(size.split("k")[0]) * 1024)
    elif "m" in size:
        size = int(float(size.split("m")[0]) * 1048576)
    elif "g" in size:
        size = int(float(size.split("g")[0]) * 1073741824)
    elif "t" in size:
        size = int(float(size.split("t")[0]) * 1099511627776)
    else:
        size = 0
    return size


async def get_content_type(url):
    try:
        async with AsyncClient() as client:
            response = await client.get(url, allow_redirects=True, verify=False)
            return response.headers.get("Content-Type")
    except:
        return None


def update_user_ldata(id_, key, value):
    user_data.setdefault(id_, {})
    user_data[id_][key] = value


async def cmd_exec(cmd, shell=False):
    if shell:
        proc = await create_subprocess_shell(cmd, stdout=PIPE, stderr=PIPE)
    else:
        proc = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = await proc.communicate()
    try:
        stdout = stdout.decode().strip()
    except:
        stdout = "Unable to decode the response!"
    try:
        stderr = stderr.decode().strip()
    except:
        stderr = "Unable to decode the error!"
    return stdout, stderr, proc.returncode


def new_task(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        task = bot_loop.create_task(func(*args, **kwargs))
        return task

    return wrapper


async def sync_to_async(func, *args, wait=True, **kwargs):
    pfunc = partial(func, *args, **kwargs)
    future = bot_loop.run_in_executor(THREAD_POOL, pfunc)
    return await future if wait else future


def async_to_sync(func, *args, wait=True, **kwargs):
    future = run_coroutine_threadsafe(func(*args, **kwargs), bot_loop)
    return future.result() if wait else future


def loop_thread(func):
    @wraps(func)
    def wrapper(*args, wait=False, **kwargs):
        future = run_coroutine_threadsafe(func(*args, **kwargs), bot_loop)
        return future.result() if wait else future

    return wrapper
