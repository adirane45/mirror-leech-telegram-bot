from psutil import cpu_percent, virtual_memory, disk_usage
from time import time
from re import findall

from apscheduler.triggers.interval import IntervalTrigger

from .. import user_data, ui_settings, DOWNLOAD_DIR, LOGGER, scheduler
from ..core.config_manager import Config
from ..core.telegram_manager import TgClient
from .queue_manager import pause_all_tasks_auto
from ..helper.ext_utils.bot_utils import new_task
from ..helper.ext_utils.status_utils import get_readable_file_size
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.message_utils import send_message, edit_message


def _get_user_pref(user_id):
    prefs = user_data.get(user_id, {})
    if "UI_VIEW" not in prefs:
        prefs["UI_VIEW"] = "detailed"
    if "UI_THEME" not in prefs:
        prefs["UI_THEME"] = "dark"
    if "UI_NOTIF" not in prefs:
        prefs["UI_NOTIF"] = True
    user_data[user_id] = prefs
    return prefs


def _settings_message(user_id):
    prefs = _get_user_pref(user_id)
    ap = ui_settings["auto_pause"]
    text = "<b>⚙️ Settings Panel</b>\n\n"
    text += f"<b>View:</b> {prefs['UI_VIEW'].title()}\n"
    text += f"<b>Theme:</b> {prefs['UI_THEME'].title()}\n"
    text += f"<b>Notifications:</b> {'On' if prefs['UI_NOTIF'] else 'Off'}\n\n"
    text += "<b>Auto-Pause Thresholds</b>\n"
    text += f"• Enabled: {'Yes' if ap['enabled'] else 'No'}\n"
    text += f"• CPU: {ap['cpu']}% | RAM: {ap['ram']}% | Disk: {ap['disk']}%\n"
    text += "\nUse /setalert cpu=85 ram=85 disk=90 on|off to update thresholds."
    return text


def _settings_buttons(user_id):
    prefs = _get_user_pref(user_id)
    buttons = ButtonMaker()
    buttons.data_button("View: Compact", f"settings view compact")
    buttons.data_button("View: Detailed", f"settings view detailed")
    buttons.data_button("Theme: Light", f"settings theme light")
    buttons.data_button("Theme: Dark", f"settings theme dark")
    buttons.data_button("Notif: On", f"settings notif on")
    buttons.data_button("Notif: Off", f"settings notif off")
    buttons.data_button("Auto-Pause: On", f"settings autopause on")
    buttons.data_button("Auto-Pause: Off", f"settings autopause off")
    buttons.data_button("Close", f"settings close", position="footer")
    return buttons.build_menu(2)


@new_task
async def settings_panel(_, message):
    user_id = message.from_user.id if message.from_user else message.sender_chat.id
    await send_message(message, _settings_message(user_id), _settings_buttons(user_id))


@new_task
async def view_toggle(_, message):
    user_id = message.from_user.id if message.from_user else message.sender_chat.id
    prefs = _get_user_pref(user_id)
    prefs["UI_VIEW"] = "compact" if prefs["UI_VIEW"] == "detailed" else "detailed"
    await send_message(
        message,
        f"✅ View set to <b>{prefs['UI_VIEW'].title()}</b>",
    )


@new_task
async def set_alerts(_, message):
    if not message.from_user or message.from_user.id != Config.OWNER_ID:
        await send_message(message, "❌ Only the owner can update alert thresholds!")
        return

    text = message.text
    cpu = findall(r"cpu=(\d+)", text)
    ram = findall(r"ram=(\d+)", text)
    disk = findall(r"disk=(\d+)", text)
    if cpu:
        ui_settings["auto_pause"]["cpu"] = min(99, max(1, int(cpu[0])))
    if ram:
        ui_settings["auto_pause"]["ram"] = min(99, max(1, int(ram[0])))
    if disk:
        ui_settings["auto_pause"]["disk"] = min(99, max(1, int(disk[0])))

    if " on" in text:
        ui_settings["auto_pause"]["enabled"] = True
    if " off" in text:
        ui_settings["auto_pause"]["enabled"] = False

    ap = ui_settings["auto_pause"]
    await send_message(
        message,
        f"✅ Auto-Pause settings updated.\nCPU: {ap['cpu']}% | RAM: {ap['ram']}% | Disk: {ap['disk']}%\nEnabled: {'Yes' if ap['enabled'] else 'No'}",
    )


async def settings_callback(_, query):
    user_id = query.from_user.id
    data = query.data.split()
    if len(data) < 3:
        await query.answer()
        return

    action = data[1]
    value = data[2]
    prefs = _get_user_pref(user_id)

    if action == "view":
        prefs["UI_VIEW"] = value
    elif action == "theme":
        prefs["UI_THEME"] = value
    elif action == "notif":
        prefs["UI_NOTIF"] = value == "on"
    elif action == "autopause":
        ui_settings["auto_pause"]["enabled"] = value == "on"
    elif action == "close":
        await query.message.delete()
        await query.answer()
        return

    await query.answer("Updated!")
    await edit_message(query.message, _settings_message(user_id), _settings_buttons(user_id))


async def auto_pause_monitor():
    ap = ui_settings.get("auto_pause", {})
    if not ap.get("enabled"):
        return

    now = time()
    last_trigger = ap.get("last_trigger", 0)
    if now - last_trigger < 300:
        return

    cpu = cpu_percent()
    ram = virtual_memory().percent
    disk = disk_usage(DOWNLOAD_DIR).percent

    if cpu >= ap.get("cpu", 90) or ram >= ap.get("ram", 90) or disk >= ap.get("disk", 95):
        paused_count, total = await pause_all_tasks_auto()
        ap["last_trigger"] = now
        try:
            await TgClient.bot.send_message(
                Config.OWNER_ID,
                f"⚠️ Auto-Pause Triggered!\nCPU: {cpu}% | RAM: {ram}% | Disk: {disk}%\nPaused: {paused_count}/{total} tasks.",
            )
        except Exception as e:
            LOGGER.error(str(e))


def init_ui_monitor():
    try:
        scheduler.add_job(
            auto_pause_monitor,
            trigger=IntervalTrigger(seconds=60),
            id="ui_auto_pause",
            replace_existing=True,
        )
        if not scheduler.running:
            scheduler.start()
    except Exception as e:
        LOGGER.error(str(e))
