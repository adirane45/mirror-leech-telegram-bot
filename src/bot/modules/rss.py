from asyncio import CancelledError, Lock, sleep
from datetime import datetime, timedelta
from functools import partial
from io import BytesIO
from re import I, compile
from time import time

from apscheduler.triggers.interval import IntervalTrigger
from feedparser import parse as feed_parse
from httpx import AsyncClient
from pyrogram.filters import create
from pyrogram.handlers import MessageHandler

from .. import LOGGER, rss_dict, scheduler
from ..core.config_manager import Config
from ..helper.ext_utils.bot_utils import arg_parser, get_size_bytes, new_task
from ..helper.ext_utils.db_handler import database
from ..helper.ext_utils.exceptions import RssShutdownException
from ..helper.ext_utils.help_messages import RSS_HELP_MESSAGE
from ..helper.ext_utils.status_utils import get_readable_file_size
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.filters import CustomFilters
from ..helper.telegram_helper.message_utils import delete_message, edit_message, send_file, send_message, send_rss

rss_dict_lock = Lock()
handler_dict = {}
size_regex = compile(r"(\d+(\.\d+)?\s?(GB|MB|KB|GiB|MiB|KiB))", I)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


async def rss_menu(event):
    user_id = event.from_user.id
    buttons = ButtonMaker()
    buttons.data_button("Subscribe", f"rss sub {user_id}")
    buttons.data_button("Subscriptions", f"rss list {user_id} 0")
    buttons.data_button("Get Items", f"rss get {user_id}")
    buttons.data_button("Edit", f"rss edit {user_id}")
    buttons.data_button("Pause", f"rss pause {user_id}")
    buttons.data_button("Resume", f"rss resume {user_id}")
    buttons.data_button("Unsubscribe", f"rss unsubscribe {user_id}")
    if await CustomFilters.sudo("", event):
        buttons.data_button("All Subscriptions", f"rss listall {user_id} 0")
        buttons.data_button("Pause All", f"rss allpause {user_id}")
        buttons.data_button("Resume All", f"rss allresume {user_id}")
        buttons.data_button("Unsubscribe All", f"rss allunsub {user_id}")
        buttons.data_button("Delete User", f"rss deluser {user_id}")
        if scheduler.running:
            buttons.data_button("Shutdown Rss", f"rss shutdown {user_id}")
        else:
            buttons.data_button("Start Rss", f"rss start {user_id}")
    buttons.data_button("Close", f"rss close {user_id}")
    button = buttons.build_menu(2)
    msg = f"Rss Menu | Users: {len(rss_dict)} | Running: {scheduler.running}"
    return msg, button


async def update_rss_menu(query):
    msg, button = await rss_menu(query)
    await edit_message(query.message, msg, button)


@new_task
async def get_rss_menu(_, message):
    msg, button = await rss_menu(message)
    await send_message(message, msg, button)


def _build_filter_list(filter_string):
    """Parse filter string and build nested list for OR conditions."""
    filter_list = []
    filters = filter_string.split("|")
    for f in filters:
        filter_list.append(f.split(" or "))
    return filter_list


def _parse_subscription_args(args):
    """Parse command arguments for RSS subscription."""
    if len(args) <= 2:
        return None, None, None, False, [], []
    
    arg_base = {"-c": None, "-inf": None, "-exf": None, "-stv": None}
    arg_parser(args[2:], arg_base)
    cmd = arg_base["-c"]
    inf = arg_base["-inf"]
    exf = arg_base["-exf"]
    stv = arg_base["-stv"]
    
    if stv is not None:
        stv = stv.lower() == "true"
    else:
        stv = False
    
    inf_lists = _build_filter_list(inf) if inf is not None else []
    exf_lists = _build_filter_list(exf) if exf is not None else []
    
    return cmd, inf, exf, stv, inf_lists, exf_lists


async def _fetch_rss_feed(feed_link):
    """Fetch RSS feed from URL."""
    async with AsyncClient(
        headers=headers, follow_redirects=True, timeout=60, verify=False
    ) as client:
        res = await client.get(feed_link)
    return feed_parse(res.text)


def _extract_feed_size(entry):
    """Extract size from RSS feed entry."""
    if entry.get("size"):
        return int(entry["size"])
    if entry.get("summary"):
        summary = entry["summary"]
        matches = size_regex.findall(summary)
        if matches:
            sizes = [match[0] for match in matches]
            return get_size_bytes(sizes[0])
    return 0


def _get_feed_link(entry):
    """Extract link from RSS feed entry."""
    try:
        return entry["links"][1]["href"]
    except IndexError:
        return entry["link"]


def _build_subscription_message(title, feed_link, rss_d, last_title, last_link, size, cmd, inf, exf, stv):
    """Build subscription confirmation message."""
    msg = "<b>Subscribed!</b>"
    msg += f"\n<b>Title: </b><code>{title}</code>\n<b>Feed Url: </b>{feed_link}"
    msg += f"\n<b>latest record for </b>{rss_d.feed.title}:"
    msg += f"\nName: <code>{last_title.replace('>', '').replace('<', '')}</code>"
    msg += f"\n<b>Link: </b><code>{last_link}</code>"
    if size:
        msg += f"\nSize: {get_readable_file_size(size)}"
    msg += f"\n<b>Command: </b><code>{cmd}</code>"
    msg += f"\n<b>Filters:-</b>\ninf: <code>{inf}</code>\nexf: <code>{exf}</code>\n<b>sensitive: </b>{stv}"
    return msg


def _create_subscription_entry(feed_link, last_link, last_title, inf_lists, exf_lists, cmd, stv, tag):
    """Create subscription entry dictionary."""
    return {
        "link": feed_link,
        "last_feed": last_link,
        "last_title": last_title,
        "inf": inf_lists,
        "exf": exf_lists,
        "paused": False,
        "command": cmd,
        "sensitive": stv,
        "tag": tag,
    }


async def _process_rss_sub_item(message, user_id, tag, index, item):
    args = item.split()
    if len(args) < 2:
        await send_message(
            message,
            f"{item}. Wrong Input format. Read help message before adding new subscription!",
        )
        return ""

    title = args[0].strip()
    if (user_feeds := rss_dict.get(user_id, False)) and title in user_feeds:
        await send_message(
            message, f"This title {title} already subscribed! Choose another title!"
        )
        return ""

    feed_link = args[1].strip()
    if feed_link.startswith(("-inf", "-exf", "-c")):
        await send_message(
            message,
            f"Wrong input in line {index}! Add Title! Read the example!",
        )
        return ""

    cmd, inf, exf, stv, inf_lists, exf_lists = _parse_subscription_args(args)

    try:
        rss_d = await _fetch_rss_feed(feed_link)
        last_title = rss_d.entries[0]["title"]
        size = _extract_feed_size(rss_d.entries[0])
        last_link = _get_feed_link(rss_d.entries[0])

        msg = _build_subscription_message(
            title, feed_link, rss_d, last_title, last_link, size, cmd, inf, exf, stv
        )

        subscription_entry = _create_subscription_entry(
            feed_link, last_link, last_title, inf_lists, exf_lists, cmd, stv, tag
        )

        async with rss_dict_lock:
            if rss_dict.get(user_id, False):
                rss_dict[user_id][title] = subscription_entry
            else:
                rss_dict[user_id] = {title: subscription_entry}

        LOGGER.info(
            f"Rss Feed Added: id: {user_id} - title: {title} - link: {feed_link} - c: {cmd} - inf: {inf} - exf: {exf} - stv: {stv}"
        )
        return msg
    except (IndexError, AttributeError) as e:
        emsg = f"The link: {feed_link} doesn't seem to be a RSS feed or it's region-blocked!"
        await send_message(message, emsg + "\nError: " + str(e))
    except Exception as e:
        await send_message(message, str(e))
    return ""


@new_task
async def rss_sub(_, message, pre_event):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    tag = f"@{message.from_user.username}" if message.from_user.username else message.from_user.mention

    msg = ""
    for index, item in enumerate(message.text.split("\n"), start=1):
        msg += await _process_rss_sub_item(message, user_id, tag, index, item)

    if msg:
        await database.rss_update(user_id)
        await send_message(message, msg)
        is_sudo = await CustomFilters.sudo("", message)
        if scheduler.state == 2:
            scheduler.resume()
        elif is_sudo and not scheduler.running:
            add_job()
            scheduler.start()
    await update_rss_menu(pre_event)


async def get_user_id(title):
    async with rss_dict_lock:
        return next(
            (
                (True, user_id)
                for user_id, feed in rss_dict.items()
                if feed["title"] == title
            ),
            (False, False),
        )


@new_task
async def rss_update(_, message, pre_event, state):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    titles = message.text.split()
    is_sudo = await CustomFilters.sudo("", message)
    updated = []
    for title in titles:
        title = title.strip()
        target_user_id = await _resolve_rss_target_user(
            message,
            title,
            user_id,
            is_sudo,
        )
        if target_user_id is None:
            continue

        if _is_rss_state_already_applied(target_user_id, title, state):
            await send_message(message, f"{title} already {state}d!")
            continue

        await _apply_rss_state_update(target_user_id, title, state)
        updated.append(title)

        if state == "resume":
            _resume_scheduler_if_needed(is_sudo)

        if is_sudo and Config.DATABASE_URL and target_user_id != message.from_user.id:
            await database.rss_update(target_user_id)

        await _cleanup_empty_rss_user(target_user_id)

        user_id = target_user_id
    if updated:
        LOGGER.info(f"Rss link with Title(s): {updated} has been {state}d!")
        await send_message(
            message,
            f"Rss links with Title(s): <code>{updated}</code> has been {state}d!",
        )
        if rss_dict.get(user_id):
            await database.rss_update(user_id)
    await update_rss_menu(pre_event)


async def _resolve_rss_target_user(message, title: str, user_id: int, is_sudo: bool):
    if rss_dict[user_id].get(title, False):
        return user_id
    if is_sudo:
        found, target_user_id = await get_user_id(title)
        if found:
            return target_user_id
    await send_message(message, f"{title} not found!")
    return None


def _is_rss_state_already_applied(user_id: int, title: str, state: str):
    is_paused = rss_dict[user_id][title].get("paused", False)
    return (is_paused and state == "pause") or (not is_paused and state == "resume")


async def _apply_rss_state_update(user_id: int, title: str, state: str):
    async with rss_dict_lock:
        if state == "unsubscribe":
            del rss_dict[user_id][title]
        elif state == "pause":
            rss_dict[user_id][title]["paused"] = True
        elif state == "resume":
            rss_dict[user_id][title]["paused"] = False


def _resume_scheduler_if_needed(is_sudo: bool):
    if scheduler.state == 2:
        scheduler.resume()
    elif is_sudo and not scheduler.running:
        add_job()
        scheduler.start()


async def _cleanup_empty_rss_user(user_id: int):
    if rss_dict[user_id]:
        return
    async with rss_dict_lock:
        del rss_dict[user_id]
    await database.rss_delete(user_id)
    if not rss_dict:
        await database.trunc_table("rss")


async def rss_list(query, start, all_users=False):
    user_id = query.from_user.id
    buttons = ButtonMaker()
    if all_users:
        list_feed = f"<b>All subscriptions | Page: {int(start / 5)} </b>"
        async with rss_dict_lock:
            keysCount = sum(len(v.keys()) for v in rss_dict.values())
            index = 0
            for titles in rss_dict.values():
                for index, (title, data) in enumerate(
                    list(titles.items())[start : 5 + start]
                ):
                    list_feed += f"\n\n<b>Title:</b> <code>{title}</code>\n"
                    list_feed += f"<b>Feed Url:</b> <code>{data['link']}</code>\n"
                    list_feed += f"<b>Command:</b> <code>{data['command']}</code>\n"
                    list_feed += f"<b>Inf:</b> <code>{data['inf']}</code>\n"
                    list_feed += f"<b>Exf:</b> <code>{data['exf']}</code>\n"
                    list_feed += f"<b>Sensitive:</b> <code>{data.get('sensitive', False)}</code>\n"
                    list_feed += f"<b>Paused:</b> <code>{data['paused']}</code>\n"
                    list_feed += f"<b>User:</b> {data['tag'].replace('@', '', 1)}"
                    index += 1
                    if index == 5:
                        break
    else:
        list_feed = f"<b>Your subscriptions | Page: {int(start / 5)} </b>"
        async with rss_dict_lock:
            keysCount = len(rss_dict.get(user_id, {}).keys())
            for title, data in list(rss_dict[user_id].items())[start : 5 + start]:
                list_feed += f"\n\n<b>Title:</b> <code>{title}</code>\n<b>Feed Url: </b><code>{data['link']}</code>\n"
                list_feed += f"<b>Command:</b> <code>{data['command']}</code>\n"
                list_feed += f"<b>Inf:</b> <code>{data['inf']}</code>\n"
                list_feed += f"<b>Exf:</b> <code>{data['exf']}</code>\n"
                list_feed += (
                    f"<b>Sensitive:</b> <code>{data.get('sensitive', False)}</code>\n"
                )
                list_feed += f"<b>Paused:</b> <code>{data['paused']}</code>\n"
    buttons.data_button("Back", f"rss back {user_id}")
    buttons.data_button("Close", f"rss close {user_id}")
    if keysCount > 5:
        for x in range(0, keysCount, 5):
            buttons.data_button(
                f"{int(x / 5)}", f"rss list {user_id} {x}", position="footer"
            )
    button = buttons.build_menu(2)
    if query.message.text.html == list_feed:
        return
    await edit_message(query.message, list_feed, button)


@new_task
async def rss_get(_, message, pre_event):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    args = message.text.split()
    if len(args) < 2:
        await send_message(
            message,
            f"{args}. Wrong Input format. You should add number of the items you want to get. Read help message before adding new subscription!",
        )
        await update_rss_menu(pre_event)
        return
    try:
        title = args[0]
        count = int(args[1])
        data = rss_dict[user_id].get(title, False)
        if data and count > 0:
            try:
                msg = await send_message(
                    message, f"Getting the last <b>{count}</b> item(s) from {title}"
                )
                async with AsyncClient(
                    headers=headers, follow_redirects=True, timeout=60, verify=False
                ) as client:
                    res = await client.get(data["link"])
                html = res.text
                rss_d = feed_parse(html)
                item_info = ""
                for item_num in range(count):
                    try:
                        link = rss_d.entries[item_num]["links"][1]["href"]
                    except IndexError:
                        link = rss_d.entries[item_num]["link"]
                    item_info += f"<b>Name: </b><code>{rss_d.entries[item_num]['title'].replace('>', '').replace('<', '')}</code>\n"
                    item_info += f"<b>Link: </b><code>{link}</code>\n\n"
                item_info_ecd = item_info.encode()
                if len(item_info_ecd) > 4000:
                    with BytesIO(item_info_ecd) as out_file:
                        out_file.name = f"rssGet {title} items_no. {count}.txt"
                        await send_file(message, out_file)
                    await delete_message(msg)
                else:
                    await edit_message(msg, item_info)
            except IndexError as e:
                LOGGER.error(str(e))
                await edit_message(
                    msg, "Parse depth exceeded. Try again with a lower value."
                )
            except Exception as e:
                LOGGER.error(str(e))
                await edit_message(msg, str(e))
        else:
            await send_message(message, "Enter a valid title. Title not found!")
    except Exception as e:
        LOGGER.error(str(e))
        await send_message(message, f"Enter a valid value!. {e}")
    await update_rss_menu(pre_event)


@new_task
async def rss_edit(_, message, pre_event):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    items = message.text.split("\n")
    updated = False
    for item in items:
        args = item.split()
        title = args[0].strip()
        if len(args) < 2:
            await send_message(
                message,
                f"{item}. Wrong Input format. Read help message before editing!",
            )
            continue
        elif not rss_dict[user_id].get(title, False):
            await send_message(message, "Enter a valid title. Title not found!")
            continue
        updated = await _apply_rss_edit_item(user_id, title, args) or updated
    if updated:
        await database.rss_update(user_id)
    await update_rss_menu(pre_event)


def _parse_rss_edit_values(args):
    arg_base = {"-c": None, "-inf": None, "-exf": None, "-stv": None}
    arg_parser(args[1:], arg_base)
    return arg_base["-c"], arg_base["-inf"], arg_base["-exf"], arg_base["-stv"]


def _normalize_edit_command(cmd):
    if cmd is None:
        return None
    return None if cmd.lower() == "none" else cmd


def _normalize_edit_filters(value):
    if value is None:
        return None
    if value.lower() == "none":
        return []
    return _build_filter_list(value)


async def _apply_rss_edit_item(user_id, title, args):
    cmd, inf, exf, stv = _parse_rss_edit_values(args)
    async with rss_dict_lock:
        if stv is not None:
            rss_dict[user_id][title]["sensitive"] = stv.lower() == "true"
        normalized_cmd = _normalize_edit_command(cmd)
        if cmd is not None:
            rss_dict[user_id][title]["command"] = normalized_cmd
        inf_filters = _normalize_edit_filters(inf)
        if inf is not None:
            rss_dict[user_id][title]["inf"] = inf_filters
        exf_filters = _normalize_edit_filters(exf)
        if exf is not None:
            rss_dict[user_id][title]["exf"] = exf_filters
    return any(value is not None for value in (cmd, inf, exf, stv))


@new_task
async def rss_delete(_, message, pre_event):
    handler_dict[message.from_user.id] = False
    users = message.text.split()
    for user in users:
        user = int(user)
        async with rss_dict_lock:
            del rss_dict[user]
        await database.rss_delete(user)
    await update_rss_menu(pre_event)


async def event_handler(client, query, pfunc):
    user_id = query.from_user.id
    handler_dict[user_id] = True
    start_time = time()

    async def event_filter(_, __, event):
        user = event.from_user or event.sender_chat
        return bool(
            user.id == user_id and event.chat.id == query.message.chat.id and event.text
        )

    handler = client.add_handler(MessageHandler(pfunc, create(event_filter)), group=-1)
    while handler_dict[user_id]:
        await sleep(0.5)
        if time() - start_time > 60:
            handler_dict[user_id] = False
            await update_rss_menu(query)
    client.remove_handler(*handler)


def _has_subscriptions(user_id):
    return len(rss_dict.get(int(user_id), {})) != 0


async def _show_no_subscriptions(query):
    await query.answer(text="No subscriptions!", show_alert=True)


async def _show_text_prompt(message, user_id, text):
    buttons = ButtonMaker()
    buttons.data_button("Back", f"rss back {user_id}")
    buttons.data_button("Close", f"rss close {user_id}")
    button = buttons.build_menu(2)
    await edit_message(message, text, button)


async def _handle_uall_action(query, action, target_user_id):
    if not _has_subscriptions(target_user_id):
        await _show_no_subscriptions(query)
        return True

    await query.answer()
    if action.endswith("unsub"):
        async with rss_dict_lock:
            del rss_dict[int(target_user_id)]
        await database.rss_delete(int(target_user_id))
        await update_rss_menu(query)
    elif action.endswith("pause"):
        async with rss_dict_lock:
            for info in rss_dict[int(target_user_id)].values():
                info["paused"] = True
        await database.rss_update(int(target_user_id))
        await update_rss_menu(query)
    elif action.endswith("resume"):
        async with rss_dict_lock:
            for info in rss_dict[int(target_user_id)].values():
                info["paused"] = False
        if scheduler.state == 2:
            scheduler.resume()
        await database.rss_update(int(target_user_id))
        await update_rss_menu(query)
    return True


async def _execute_all_unsub(query):
    async with rss_dict_lock:
        rss_dict.clear()
    await database.trunc_table("rss")
    await update_rss_menu(query)


async def _execute_all_pause():
    async with rss_dict_lock:
        for user_feeds in rss_dict.values():
            for feed in user_feeds.values():
                feed["paused"] = True
    if scheduler.running:
        scheduler.pause()
    await database.rss_update_all()


async def _execute_all_resume(query):
    async with rss_dict_lock:
        for user_feeds in rss_dict.values():
            for feed in user_feeds.values():
                feed["paused"] = False
    if scheduler.state == 2:
        scheduler.resume()
    elif not scheduler.running:
        add_job()
        scheduler.start()
        await update_rss_menu(query)
    await database.rss_update_all()


async def _handle_all_action(query, action):
    if len(rss_dict) == 0:
        await _show_no_subscriptions(query)
        return True

    await query.answer()
    if action.endswith("unsub"):
        await _execute_all_unsub(query)
    elif action.endswith("pause"):
        await _execute_all_pause()
    elif action.endswith("resume"):
        await _execute_all_resume(query)
    return True


async def _handle_scheduler_action(query, action):
    if action == "shutdown":
        if scheduler.running:
            await query.answer()
            scheduler.shutdown(wait=False)
            await sleep(0.5)
            await update_rss_menu(query)
        else:
            await query.answer(text="Already Stopped!", show_alert=True)
        return True

    if action == "start":
        if not scheduler.running:
            await query.answer()
            add_job()
            scheduler.start()
            await update_rss_menu(query)
        else:
            await query.answer(text="Already Running!", show_alert=True)
        return True

    return False


@new_task
async def rss_listener(client, query):
    user_id = query.from_user.id
    message = query.message
    data = query.data.split()
    action = data[1]
    target_user_id = int(data[2])

    if target_user_id != user_id and not await CustomFilters.sudo("", query):
        await query.answer(
            text="You don't have permission to use these buttons!", show_alert=True
        )
        return

    handlers = {
        "close": partial(_handle_rss_close, query, message, user_id),
        "back": partial(_handle_rss_back, query, user_id),
        "sub": partial(_handle_rss_sub_action, client, query, message, user_id),
        "list": partial(_handle_rss_list_action, query, target_user_id, data),
        "get": partial(_handle_rss_get_action, client, query, message, user_id, target_user_id),
        "unsubscribe": partial(_handle_rss_update_action, client, query, message, user_id, target_user_id, "unsubscribe"),
        "pause": partial(_handle_rss_update_action, client, query, message, user_id, target_user_id, "pause"),
        "resume": partial(_handle_rss_update_action, client, query, message, user_id, target_user_id, "resume"),
        "edit": partial(_handle_rss_edit_action, client, query, message, user_id, target_user_id),
        "deluser": partial(_handle_rss_delete_user_action, client, query, message, user_id),
        "listall": partial(_handle_rss_list_all_action, query, data),
    }
    handler = handlers.get(action)
    if handler:
        await handler()
        return

    if action.startswith("uall"):
        handler_dict[user_id] = False
        await _handle_uall_action(query, action, target_user_id)
        return

    if action.startswith("all"):
        await _handle_all_action(query, action)
        return

    await _handle_scheduler_action(query, action)


async def _handle_rss_close(query, message, user_id: int):
    await query.answer()
    handler_dict[user_id] = False
    await delete_message(message.reply_to_message)
    await delete_message(message)


async def _handle_rss_back(query, user_id: int):
    await query.answer()
    handler_dict[user_id] = False
    await update_rss_menu(query)


async def _handle_rss_sub_action(client, query, message, user_id: int):
    await query.answer()
    handler_dict[user_id] = False
    await _show_text_prompt(message, user_id, RSS_HELP_MESSAGE)
    pfunc = partial(rss_sub, pre_event=query)
    await event_handler(client, query, pfunc)


async def _handle_rss_list_action(query, target_user_id: int, data: list):
    handler_dict[query.from_user.id] = False
    if not _has_subscriptions(target_user_id):
        await _show_no_subscriptions(query)
        return
    await query.answer()
    start = int(data[3])
    await rss_list(query, start)


async def _handle_rss_get_action(client, query, message, user_id: int, target_user_id: int):
    handler_dict[user_id] = False
    if not _has_subscriptions(target_user_id):
        await _show_no_subscriptions(query)
        return
    await query.answer()
    await _show_text_prompt(
        message,
        user_id,
        "Send one title with value separated by space get last X items.\nTitle Value\nTimeout: 60 sec.",
    )
    pfunc = partial(rss_get, pre_event=query)
    await event_handler(client, query, pfunc)


def _build_rss_update_buttons(user_id: int, action: str):
    buttons = ButtonMaker()
    buttons.data_button("Back", f"rss back {user_id}")
    labels = {
        "pause": "Pause AllMyFeeds",
        "resume": "Resume AllMyFeeds",
        "unsubscribe": "Unsub AllMyFeeds",
    }
    callbacks = {
        "pause": f"rss uallpause {user_id}",
        "resume": f"rss uallresume {user_id}",
        "unsubscribe": f"rss uallunsub {user_id}",
    }
    buttons.data_button(labels[action], callbacks[action])
    buttons.data_button("Close", f"rss close {user_id}")
    return buttons.build_menu(2)


async def _handle_rss_update_action(
    client,
    query,
    message,
    user_id: int,
    target_user_id: int,
    action: str,
):
    handler_dict[user_id] = False
    if not _has_subscriptions(target_user_id):
        await _show_no_subscriptions(query)
        return
    await query.answer()
    button = _build_rss_update_buttons(user_id, action)
    await edit_message(
        message,
        f"Send one or more rss titles separated by space to {action}.\nTimeout: 60 sec.",
        button,
    )
    pfunc = partial(rss_update, pre_event=query, state=action)
    await event_handler(client, query, pfunc)


async def _handle_rss_edit_action(client, query, message, user_id: int, target_user_id: int):
    handler_dict[user_id] = False
    if not _has_subscriptions(target_user_id):
        await _show_no_subscriptions(query)
        return
    await query.answer()
    buttons = ButtonMaker()
    buttons.data_button("Back", f"rss back {user_id}")
    buttons.data_button("Close", f"rss close {user_id}")
    button = buttons.build_menu(2)
    msg = """Send one or more rss titles with new filters or command separated by new line.
Examples:
Title1 -c mirror -up remote:path/subdir -exf none -inf 1080 or 720 -stv true
Title2 -c none -inf none -stv false
Title3 -c mirror -rcf xxx -up xxx -z pswd -stv false
Note: Only what you provide will be edited, the rest will be the same like example 2: exf will stay same as it is.
Timeout: 60 sec. Argument -c for command and arguments
            """
    await edit_message(message, msg, button)
    pfunc = partial(rss_edit, pre_event=query)
    await event_handler(client, query, pfunc)


async def _handle_rss_delete_user_action(client, query, message, user_id: int):
    if len(rss_dict) == 0:
        await _show_no_subscriptions(query)
        return
    await query.answer()
    await _show_text_prompt(
        message,
        user_id,
        "Send one or more user_id separated by space to delete their resources.\nTimeout: 60 sec.",
    )
    pfunc = partial(rss_delete, pre_event=query)
    await event_handler(client, query, pfunc)


async def _handle_rss_list_all_action(query, data: list):
    if not rss_dict:
        await _show_no_subscriptions(query)
        return
    await query.answer()
    start = int(data[3])
    await rss_list(query, start, all_users=True)


def _resolve_rss_chat(chat):
    rss_topic_id = rss_chat_id = None
    if isinstance(chat, int):
        rss_chat_id = chat
    elif "|" in chat:
        rss_chat_id, rss_topic_id = list(
            map(
                lambda x: int(x) if x.lstrip("-").isdigit() else x,
                chat.split("|", 1),
            )
        )
    elif chat.lstrip("-").isdigit():
        rss_chat_id = int(chat)
    return rss_chat_id, rss_topic_id


async def _fetch_rss_html(link):
    tries = 0
    while True:
        try:
            async with AsyncClient(
                headers=headers,
                follow_redirects=True,
                timeout=60,
                verify=False,
            ) as client:
                res = await client.get(link)
            return res.text
        except Exception as e:
            tries += 1
            LOGGER.debug(f"RSS fetch attempt {tries} failed: {e}")
            if tries > 3:
                raise


def _entry_link(entry):
    links = entry.get("links", [])
    if len(links) > 1:
        return links[1].get("href")
    if links:
        return links[0].get("href")
    return entry.get("link")


def _entry_size(entry):
    if entry.get("size"):
        return int(entry["size"])
    if entry.get("summary"):
        summary = entry["summary"]
        matches = size_regex.findall(summary)
        sizes = [match[0] for match in matches]
        if sizes:
            return get_size_bytes(sizes[0])
    return 0


def _passes_inf_filters(item_title, inf_filters, sensitive):
    for flist in inf_filters:
        if (sensitive and all(x.lower() not in item_title.lower() for x in flist)) or (
            not sensitive and all(x not in item_title for x in flist)
        ):
            return False
    return True


def _passes_exf_filters(item_title, exf_filters, sensitive):
    for flist in exf_filters:
        if (sensitive and any(x.lower() in item_title.lower() for x in flist)) or (
            not sensitive and any(x in item_title for x in flist)
        ):
            return False
    return True


def _build_feed_message(item_title, url, size, command, user, tag):
    if command:
        if size and Config.RSS_SIZE_LIMIT and Config.RSS_SIZE_LIMIT < size:
            return None
        cmd = command.split(maxsplit=1)
        cmd.insert(1, url)
        feed_msg = " ".join(cmd)
        if not feed_msg.startswith("/"):
            feed_msg = f"/{feed_msg}"
    else:
        feed_msg = (
            f"<b>Name: </b><code>{item_title.replace('>', '').replace('<', '')}</code>"
        )
        feed_msg += f"\n\n<b>Link: </b><code>{url}</code>"
        if size:
            feed_msg += f"\n<b>Size: </b>{get_readable_file_size(size)}"
    feed_msg += f"\n<b>Tag: </b><code>{tag}</code> <code>{user}</code>"
    return feed_msg


def _next_feed_entry(rss_d, data, title, feed_count):
    try:
        entry = rss_d.entries[feed_count]
    except IndexError:
        LOGGER.warning(
            f"Reached Max index no. {feed_count} for this feed: {title}. Maybe you need to use less RSS_DELAY to not miss some torrents"
        )
        return None, True

    item_title = entry["title"]
    url = _entry_link(entry)
    if data["last_feed"] == url or data["last_title"] == item_title:
        return None, True

    return {
        "title": item_title,
        "url": url,
        "size": _entry_size(entry),
    }, False


def _entry_is_filtered(data, item_title):
    sensitive = data.get("sensitive", False)
    return not _passes_inf_filters(item_title, data["inf"], sensitive) or not _passes_exf_filters(
        item_title,
        data["exf"],
        sensitive,
    )


async def _dispatch_feed_entry(entry_data, data, user, rss_chat_id, rss_topic_id):
    feed_msg = _build_feed_message(
        entry_data["title"],
        entry_data["url"],
        entry_data["size"],
        data["command"],
        user,
        data["tag"],
    )
    if feed_msg is None:
        return
    await send_rss(feed_msg, rss_chat_id, rss_topic_id)


async def _process_rss_feed(user, title, data, rss_chat_id, rss_topic_id):
    html = await _fetch_rss_html(data["link"])
    rss_d = feed_parse(html)
    if not rss_d.entries:
        LOGGER.warning(
            f"No entries found for > Feed Title: {title} - Feed Link: {data['link']}"
        )
        return False

    entry0 = rss_d.entries[0]
    last_link = _entry_link(entry0)
    last_title = entry0.get("title")

    if data["last_feed"] == last_link or data["last_title"] == last_title:
        return True

    feed_count = 0
    while True:
        try:
            await sleep(10)
        except CancelledError:
            raise RssShutdownException("Rss Monitor Stopped!")

        entry_data, should_stop = _next_feed_entry(rss_d, data, title, feed_count)
        if should_stop:
            break

        if _entry_is_filtered(data, entry_data["title"]):
            feed_count += 1
            continue

        await _dispatch_feed_entry(entry_data, data, user, rss_chat_id, rss_topic_id)
        feed_count += 1

    async with rss_dict_lock:
        if user not in rss_dict or not rss_dict[user].get(title, False):
            return True
        rss_dict[user][title].update({"last_feed": last_link, "last_title": last_title})
    await database.rss_update(user)
    LOGGER.info(f"Feed Name: {title}")
    LOGGER.info(f"Last item: {last_link}")
    return True


def _prepare_rss_monitor_context():
    chat = Config.RSS_CHAT
    if not chat:
        LOGGER.warning("RSS_CHAT not added! Shutting down rss scheduler...")
        scheduler.shutdown(wait=False)
        return None
    if len(rss_dict) == 0:
        scheduler.pause()
        return None
    return _resolve_rss_chat(chat)


async def _process_user_rss_items(user, items, rss_chat_id, rss_topic_id):
    processed_any = False
    for title, data in items.items():
        try:
            if data["paused"]:
                continue
            processed = await _process_rss_feed(
                user,
                title,
                data,
                rss_chat_id,
                rss_topic_id,
            )
            if processed:
                processed_any = True
        except RssShutdownException as ex:
            LOGGER.info(ex)
            break
        except Exception as e:
            LOGGER.error(f"{e} - Feed Name: {title} - Feed Link: {data['link']}")
            continue
    return processed_any


async def rss_monitor():
    rss_chat = _prepare_rss_monitor_context()
    if rss_chat is None:
        return

    all_paused = True
    rss_chat_id, rss_topic_id = rss_chat

    for user, items in list(rss_dict.items()):
        processed = await _process_user_rss_items(
            user,
            items,
            rss_chat_id,
            rss_topic_id,
        )
        if processed:
            all_paused = False

    if all_paused:
        scheduler.pause()


def add_job():
    scheduler.add_job(
        rss_monitor,
        trigger=IntervalTrigger(seconds=Config.RSS_DELAY),
        id="0",
        name="RSS",
        misfire_grace_time=15,
        max_instances=1,
        next_run_time=datetime.now() + timedelta(seconds=20),
        replace_existing=True,
    )


add_job()
