from asyncio import Event, gather, wait_for
from configparser import RawConfigParser
from functools import partial
from json import loads
from time import time

from aiofiles import open as aiopen
from aiofiles.os import path as aiopath
from pyrogram.filters import regex, user
from pyrogram.handlers import CallbackQueryHandler

from .... import LOGGER
from ....core.config_manager import Config
from ...ext_utils.bot_utils import cmd_exec, new_task, update_user_ldata
from ...ext_utils.db_handler import database
from ...ext_utils.status_utils import get_readable_file_size, get_readable_time
from ...telegram_helper.button_build import ButtonMaker
from ...telegram_helper.message_utils import delete_message, edit_message, send_message

LIST_LIMIT = 6


def _build_target_path(obj, index):
    return obj.path + (
        f"/{obj.path_list[index]['Path']}" if obj.path else obj.path_list[index]["Path"]
    )


async def _handle_selected_paths_done(obj, message):
    obj.path = f"rclone_select_{time()}.txt"
    async with aiopen(obj.path, "w") as txt_file:
        for selected_path in obj.selected_pathes:
            await txt_file.write(f"{selected_path}\n")
    await delete_message(message)
    obj.event.set()


async def _handle_path_action(obj, data, message):
    index = int(data[3])
    if obj.select:
        path = _build_target_path(obj, index)
        if path in obj.selected_pathes:
            obj.selected_pathes.remove(path)
        else:
            obj.selected_pathes.add(path)
        await obj.get_path_buttons()
        return
    obj.path = _build_target_path(obj, index)
    if data[2] == "fo":
        await obj.get_path()
    else:
        await delete_message(message)
        obj.event.set()


async def _handle_set_default_path(obj):
    path = (
        f"{obj.remote}{obj.path}"
        if obj.config_path == "rclone.conf"
        else f"mrcc:{obj.remote}{obj.path}"
    )
    if path == obj.listener.user_dict.get("RCLONE_PATH"):
        return
    update_user_ldata(obj.listener.user_id, "RCLONE_PATH", path)
    await obj.get_path_buttons()
    if Config.DATABASE_URL:
        await database.update_user_data(obj.listener.user_id)


async def _handle_config_scope_change(obj, config_path):
    obj.config_path = config_path
    obj.path = ""
    obj.remote = ""
    await obj.list_remotes()


async def _handle_back_action(obj, data):
    if data[2] == "re":
        await obj.list_config()
    else:
        await obj.back_from_path()


async def _handle_simple_action(action, obj, data, message, query):
    action_handlers = {
        "pre": lambda: _handle_previous_page(obj),
        "nex": lambda: _handle_next_page(obj),
        "select": lambda: _toggle_select_mode(obj),
        "back": lambda: _handle_back_action(obj, data),
        "re": lambda: _handle_remote_selection(obj, query),
        "clear": lambda: _clear_selections(obj),
        "ds": lambda: _handle_selected_paths_done(obj, message),
        "pa": lambda: _handle_path_action(obj, data, message),
        "ps": lambda: _handle_page_step(obj, data),
        "root": lambda: _handle_root_navigation(obj),
        "itype": lambda: _handle_item_type(obj, data),
        "cur": lambda: _handle_current_selection(obj, message),
        "def": lambda: _handle_set_default_path(obj),
        "owner": lambda: _handle_config_scope_change(obj, "rclone.conf"),
        "user": lambda: _handle_config_scope_change(obj, obj.user_rcc_path),
    }
    
    handler = action_handlers.get(action)
    if handler:
        await handler()


async def _handle_previous_page(obj):
    obj.iter_start -= LIST_LIMIT * obj.page_step
    await obj.get_path_buttons()


async def _handle_next_page(obj):
    obj.iter_start += LIST_LIMIT * obj.page_step
    await obj.get_path_buttons()


async def _toggle_select_mode(obj):
    obj.select = not obj.select
    await obj.get_path_buttons()


async def _handle_remote_selection(obj, query):
    remotes_data = query.data.split(maxsplit=2)
    obj.remote = remotes_data[2]
    await obj.get_path()


async def _clear_selections(obj):
    obj.selected_pathes = set()
    await obj.get_path_buttons()


async def _handle_page_step(obj, data):
    page_step = int(data[2])
    if obj.page_step != page_step:
        obj.page_step = page_step
        await obj.get_path_buttons()


async def _handle_root_navigation(obj):
    obj.path = ""
    await obj.get_path()


async def _handle_item_type(obj, data):
    obj.item_type = data[2]
    await obj.get_path()


async def _handle_current_selection(obj, message):
    await delete_message(message)
    obj.event.set()


@new_task
async def path_updates(_, query, obj):
    await query.answer()
    message = query.message
    data = query.data.split()
    action = data[1]
    if action == "cancel":
        obj.remote = "Task has been cancelled!"
        obj.path = ""
        obj.listener.is_cancelled = True
        obj.event.set()
        await delete_message(message)
        return
    if obj.query_proc:
        return
    obj.query_proc = True
    try:
        await _handle_simple_action(action, obj, data, message, query)
    finally:
        obj.query_proc = False


class RcloneList:
    def __init__(self, listener):
        self._rc_user = False
        self._rc_owner = False
        self._sections = []
        self._reply_to = None
        self._time = time()
        self._timeout = 240
        self.listener = listener
        self.remote = ""
        self.query_proc = False
        self.item_type = "--dirs-only"
        self.event = Event()
        self.user_rcc_path = f"rclone/{self.listener.user_id}.conf"
        self.config_path = ""
        self.path = ""
        self.list_status = ""
        self.path_list = []
        self.iter_start = 0
        self.page_step = 1
        self.select = False
        self.selected_pathes = set()

    async def _event_handler(self):
        pfunc = partial(path_updates, obj=self)
        handler = self.listener.client.add_handler(
            CallbackQueryHandler(
                pfunc, filters=regex("^rcq") & user(self.listener.user_id)
            ),
            group=-1,
        )
        try:
            await wait_for(self.event.wait(), timeout=self._timeout)
        except:
            self.path = ""
            self.remote = "Timed Out. Task has been cancelled!"
            self.listener.is_cancelled = True
            self.event.set()
        finally:
            self.listener.client.remove_handler(*handler)

    async def _send_list_message(self, msg, button):
        if not self.listener.is_cancelled:
            if self._reply_to is None:
                self._reply_to = await send_message(self.listener.message, msg, button)
            else:
                await edit_message(self._reply_to, msg, button)

    def _normalize_iteration_start(self, items_no, pages):
        if items_no <= self.iter_start:
            self.iter_start = 0
        elif self.iter_start < 0 or self.iter_start > items_no:
            self.iter_start = LIST_LIMIT * (pages - 1)

    def _is_path_selected(self, name):
        return name in self.selected_pathes or any(
            selected_path.strip().endswith(f"/{name}")
            for selected_path in self.selected_pathes
        )

    def _build_item_button(self, item, index):
        orig_index = index + self.iter_start
        name = item["Path"]
        if self._is_path_selected(name):
            name = f"✅ {name}"
        if item["IsDir"]:
            ptype = "fo"
        else:
            ptype = "fi"
            name = f"[{get_readable_file_size(item['Size'])}] {name}"
        return name, f"rcq pa {ptype} {orig_index}"

    def _add_item_buttons(self, buttons):
        visible_items = self.path_list[self.iter_start : LIST_LIMIT + self.iter_start]
        for index, item in enumerate(visible_items):
            name, callback_data = self._build_item_button(item, index)
            buttons.data_button(name, callback_data)

    def _add_pagination_buttons(self, buttons, items_no):
        if items_no <= LIST_LIMIT:
            return
        for page_step in [1, 2, 4, 6, 10, 30, 50, 100]:
            buttons.data_button(page_step, f"rcq ps {page_step}", position="header")
        buttons.data_button("Previous", "rcq pre", position="footer")
        buttons.data_button("Next", "rcq nex", position="footer")

    def _add_item_type_toggle(self, buttons):
        if self.list_status != "rcd":
            return
        if self.item_type == "--dirs-only":
            buttons.data_button("Files", "rcq itype --files-only", position="footer")
        else:
            buttons.data_button("Folders", "rcq itype --dirs-only", position="footer")

    def _should_show_choose_current_path(self, items_no):
        return self.list_status == "rcu" or items_no > 0

    def _should_show_done_selection(self):
        return len(self.selected_pathes) > 1

    def _should_show_back(self):
        return self.path or len(self._sections) > 1 or (self._rc_user and self._rc_owner)

    def _add_selection_action_buttons(self, buttons):
        if not self._should_show_done_selection():
            return
        buttons.data_button("Done With Selection", "rcq ds", position="footer")
        buttons.data_button("Clear Selection", "rcq clear", position="footer")

    def _add_back_buttons(self, buttons):
        if self._should_show_back():
            buttons.data_button("Back", "rcq back pa", position="footer")
        if self.path:
            buttons.data_button("Back To Root", "rcq root", position="footer")

    def _add_footer_action_buttons(self, buttons, items_no):
        if self._should_show_choose_current_path(items_no):
            buttons.data_button("Choose Current Path", "rcq cur", position="footer")

        if self.list_status == "rcd":
            buttons.data_button(
                f"Select: {'Enabled' if self.select else 'Disabled'}",
                "rcq select",
                position="footer",
            )

        self._add_selection_action_buttons(buttons)

        if self.list_status == "rcu":
            buttons.data_button("Set as Default Path", "rcq def", position="footer")

        self._add_back_buttons(buttons)
        buttons.data_button("Cancel", "rcq cancel", position="footer")

    def _build_path_message(self, items_no, page, pages):
        msg = "Choose Path:" + (
            "\nTransfer Type: <i>Download</i>"
            if self.list_status == "rcd"
            else "\nTransfer Type: <i>Upload</i>"
        )
        if self.list_status == "rcu":
            default_path = Config.RCLONE_PATH
            msg += f"\nDefault Rclone Path: {default_path}" if default_path else ""
        msg += f"\n\nItems: {items_no}"
        if items_no > LIST_LIMIT:
            msg += f" | Page: {int(page)}/{pages} | Page Step: {self.page_step}"
        msg += f"\n\nItem Type: {self.item_type}\nConfig Path: {self.config_path}"
        msg += f"\nCurrent Path: <code>{self.remote}{self.path}</code>"
        msg += f"\nTimeout: {get_readable_time(self._timeout - (time() - self._time))}"
        return msg

    async def get_path_buttons(self):
        items_no = len(self.path_list)
        pages = (items_no + LIST_LIMIT - 1) // LIST_LIMIT
        self._normalize_iteration_start(items_no, pages)
        page = (self.iter_start / LIST_LIMIT) + 1 if self.iter_start != 0 else 1
        buttons = ButtonMaker()
        self._add_item_buttons(buttons)
        self._add_pagination_buttons(buttons, items_no)
        self._add_item_type_toggle(buttons)
        self._add_footer_action_buttons(buttons, items_no)
        button = buttons.build_menu(f_cols=2)
        msg = self._build_path_message(items_no, page, pages)
        await self._send_list_message(msg, button)

    async def get_path(self, itype=""):
        if self.list_status == "rcu":
            self.item_type = "--dirs-only"
        elif itype:
            self.item_type = itype
        cmd = [
            "rclone",
            "lsjson",
            self.item_type,
            "--fast-list",
            "--no-mimetype",
            "--no-modtime",
            "--config",
            self.config_path,
            f"{self.remote}{self.path}",
        ]
        if self.listener.is_cancelled:
            return
        res, err, code = await cmd_exec(cmd)
        if code in [0, -9]:
            result = loads(res)
            if (
                len(result) == 0
                and itype != self.item_type
                and self.list_status == "rcd"
            ):
                itype = (
                    "--dirs-only"
                    if self.item_type == "--files-only"
                    else "--files-only"
                )
                self.item_type = itype
                await self.get_path(itype)
            else:
                self.path_list = sorted(result, key=lambda x: x["Path"])
                self.iter_start = 0
                await self.get_path_buttons()
        else:
            LOGGER.error(
                f"While rclone listing. Path: {self.remote}{self.path}. Stderr: {err}"
            )
            self.remote = err[:4000]
            self.path = ""
            self.event.set()

    async def list_remotes(self):
        config = RawConfigParser()
        async with aiopen(self.config_path, "r") as f:
            contents = await f.read()
            config.read_string(contents)
        if config.has_section("combine"):
            config.remove_section("combine")
        self._sections = config.sections()
        if len(self._sections) == 1:
            self.remote = f"{self._sections[0]}:"
            await self.get_path()
        else:
            msg = "Choose Rclone remote:" + (
                "\nTransfer Type: <i>Download</i>"
                if self.list_status == "rcd"
                else "\nTransfer Type: <i>Upload</i>"
            )
            msg += f"\nConfig Path: {self.config_path}"
            msg += (
                f"\nTimeout: {get_readable_time(self._timeout - (time() - self._time))}"
            )
            buttons = ButtonMaker()
            for remote in self._sections:
                buttons.data_button(remote, f"rcq re {remote}:")
            if self._rc_user and self._rc_owner:
                buttons.data_button("Back", "rcq back re", position="footer")
            buttons.data_button("Cancel", "rcq cancel", position="footer")
            button = buttons.build_menu(2)
            await self._send_list_message(msg, button)

    async def list_config(self):
        if self._rc_user and self._rc_owner:
            msg = "Choose Rclone config:" + (
                "\nTransfer Type: Download"
                if self.list_status == "rcd"
                else "\nTransfer Type: Upload"
            )
            msg += (
                f"\nTimeout: {get_readable_time(self._timeout - (time() - self._time))}"
            )
            buttons = ButtonMaker()
            buttons.data_button("Owner Config", "rcq owner")
            buttons.data_button("My Config", "rcq user")
            buttons.data_button("Cancel", "rcq cancel")
            button = buttons.build_menu(2)
            await self._send_list_message(msg, button)
        else:
            self.config_path = "rclone.conf" if self._rc_owner else self.user_rcc_path
            await self.list_remotes()

    async def back_from_path(self):
        if self.path:
            path = self.path.rsplit("/", 1)
            self.path = path[0] if len(path) > 1 else ""
            await self.get_path()
        elif len(self._sections) > 1:
            await self.list_remotes()
        else:
            await self.list_config()

    async def get_rclone_path(self, status, config_path=None):
        self.list_status = status
        if config_path is None:
            self._rc_user, self._rc_owner = await gather(
                aiopath.exists(self.user_rcc_path), aiopath.exists("rclone.conf")
            )
            if not self._rc_owner and not self._rc_user:
                self.event.set()
                return "Rclone Config not Exists!"
            await self.list_config()
        else:
            self.config_path = config_path
            await self.list_remotes()
        await self._event_handler()
        await delete_message(self._reply_to)
        if self.config_path != "rclone.conf" and not self.listener.is_cancelled:
            return f"mrcc:{self.remote}{self.path}"
        return f"{self.remote}{self.path}"
