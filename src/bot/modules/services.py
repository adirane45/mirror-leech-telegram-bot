from time import time
from datetime import datetime
import asyncio

from ..helper.ext_utils.bot_utils import new_task
from ..helper.ext_utils.files_utils import get_mime_type
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.message_utils import send_message, edit_message, send_file
from ..helper.telegram_helper.filters import CustomFilters
from ..helper.telegram_helper.bot_commands import BotCommands
from ..core.config_manager import Config
from ..core.stream_proxy import stream_proxy


@new_task
async def start(_, message):
    from .. import LOGGER
    LOGGER.info(f"🔵 START command received from user {message.from_user.id}")
    buttons = ButtonMaker()
    buttons.url_button(
        "Repo", "https://www.github.com/adirane45/mirror-leech-telegram-bot"
    )
    buttons.url_button("Code Owner", "https://t.me/anas_tayyar")
    buttons.data_button("Get Started", "onboard start")
    buttons.data_button("Help Menu", "help menu")
    buttons.data_button("Settings", "quick_settings")
    reply_markup = buttons.build_menu(2)
    
    cf = CustomFilters()
    auth_result = await cf.authorized_user(_, message)
    LOGGER.info(f"🔵 User auth check result: {auth_result}")
    
    if auth_result:
        start_string = f"""
This bot can mirror from links|tgfiles|torrents|nzb|rclone-cloud to any rclone cloud, Google Drive or to telegram.
Type /{BotCommands.HelpCommand} to open the command menu
"""
        LOGGER.info(f"🔵 Sending authorized response to user {message.from_user.id}")
        await send_message(message, start_string, reply_markup)
        LOGGER.info(f"🔵 Message sent successfully")
    else:
        LOGGER.info(f"🔵 Sending unauthorized response to user {message.from_user.id}")
        await send_message(
            message,
            "This bot can mirror from links|tgfiles|torrents|nzb|rclone-cloud to any rclone cloud, Google Drive or to telegram.\n\n⚠️ You Are not authorized user! Deploy your own mirror-leech bot",
            reply_markup,
        )
        LOGGER.info(f"🔵 Unauthorized message sent successfully")


@new_task
async def ping(_, message):
    start_time = int(round(time() * 1000))
    reply = await send_message(message, "Starting Ping")
    end_time = int(round(time() * 1000))
    await edit_message(reply, f"{end_time - start_time} ms")


@new_task
async def log(_, message):
    await send_file(message, "data/logs/log.txt")


@new_task
async def web_logs(_, message):
    """Generate secure token for web log viewer access"""
    from logging import getLogger
    LOGGER = getLogger(__name__)
    
    cf = CustomFilters()
    if not await cf.sudo_user(_, message):
        await send_message(message, "⛔ This command is only for sudo users.")
        return
    
    try:
        # Import admin auth manager from web module
        from web.admin_logs import admin_auth_manager
        
        # Get user ID
        user_id = str(message.from_user.id)
        
        # Create token
        token = await admin_auth_manager.create_token(user_id)
        
        if not token:
            await send_message(message, "❌ Failed to generate access token. Please try again.")
            return
        
        # Build log viewer URL
        base_url = getattr(Config, 'WEB_SERVER_URL', 'http://localhost:8060')
        viewer_url = f"{base_url}/admin/logs/viewer?token={token}"
        
        # Generate QR code for easy access
        qr_image_path = None
        try:
            import qrcode
            import os
            
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(viewer_url)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_image_path = f"/tmp/weblogs_qr_{user_id}.png"
            qr_img.save(qr_image_path)
            
        except Exception as e:
            LOGGER.warning(f"QR code generation failed: {e}")
        
        # Create message
        text = (
            "<b>📊 Real-Time Web Log Viewer</b>\n\n"
            f"🔗 <b>Access URL:</b>\n<code>{viewer_url}</code>\n\n"
            "⏰ <b>Expires in:</b> 10 minutes\n"
            "🔐 <b>Security:</b> One-time use token\n\n"
            "<i>Features:</i>\n"
            "• Live log streaming with color coding\n"
            "• Filter by ERROR/WARNING/INFO/DEBUG\n"
            "• Search functionality\n"
            "• Auto-scroll and pause controls\n\n"
            "Scan the QR code or click the link to access logs!"
        )
        
        # Send with QR code if available
        qr_exists = (
            await asyncio.to_thread(os.path.exists, qr_image_path)
            if qr_image_path
            else False
        )
        if qr_exists:
            try:
                await send_file(message, qr_image_path, caption=text)
                await asyncio.to_thread(os.remove, qr_image_path)
            except Exception as e:
                LOGGER.warning(f"Failed to send QR code: {e}")
                await send_message(message, text)
        else:
            await send_message(message, text)
            
    except Exception as e:
        LOGGER.error(f"Error in web_logs command: {e}", exc_info=True)
        await send_message(
            message,
            "❌ An error occurred while generating the log viewer access.\n"
            "Please ensure the web server is running."
        )


@new_task
async def reload_config(_, message):
    """Manually trigger configuration reload"""
    from logging import getLogger
    LOGGER = getLogger(__name__)
    
    cf = CustomFilters()
    if not await cf.sudo_user(_, message):
        await send_message(message, "⛔ This command is only for sudo users.")
        return
    
    status_msg = await send_message(message, "🔄 Reloading configuration...")
    
    try:
        from ..core.config_watcher import config_watcher
        from ..core.config_manager import Config
        from pathlib import Path
        
        # Reload main config file
        config_file = (
            Path("config/.env")
            if await asyncio.to_thread(Path("config/.env").exists)
            else None
        )
        
        if not config_file:
            await edit_message(status_msg, "❌ No config file found to reload.")
            return
        
        # Trigger reload
        await config_watcher._reload_config(config_file)
        
        # Show summary
        text = (
            "<b>✅ Configuration Reloaded</b>\n\n"
            f"📄 <b>File:</b> <code>{config_file.name}</code>\n"
            f"🕐 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "<i>Note: Changes applied to all running workers.\n"
            "No restart required!</i>"
        )
        
        await edit_message(status_msg, text)
        LOGGER.info(f"Config reloaded by user {message.from_user.id}")
        
    except Exception as e:
        LOGGER.error(f"Error in reload_config command: {e}", exc_info=True)
        await edit_message(
            status_msg,
            f"❌ Config reload failed:\n<code>{str(e)}</code>"
        )


def _extract_stream_media(message):
    media = (
        message.document
        or message.video
        or message.audio
        or message.photo
        or message.animation
    )
    if not media:
        return None, None, None
    file_id = media.file_id
    file_name = getattr(media, "file_name", None) or "download"
    file_type = media.__class__.__name__.lower()
    return file_id, file_name, file_type


@new_task
async def stream_link(_, message):
    cf = CustomFilters()
    if not await cf.authorized_user(_, message):
        return

    reply = message.reply_to_message
    if reply:
        file_id, file_name, file_type = _extract_stream_media(reply)
    else:
        file_id = None
        file_name = None
        file_type = None

    if not file_id:
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            file_id = parts[1].strip()
            file_name = "download"
            file_type = "document"

    if not file_id:
        usage = f"Usage: /{BotCommands.StreamLinkCommand[0]} <file_id> or reply to a file"
        await send_message(message, usage)
        return

    mime_type = "application/octet-stream"
    if reply and reply.document and reply.document.file_name:
        mime_type = get_mime_type(reply.document.file_name)

    token = await stream_proxy.create_token(
        file_id=file_id,
        file_name=file_name or "download",
        file_type=file_type or "document",
        mime_type=mime_type,
    )

    if not token:
        await send_message(message, "Stream links are disabled.")
        return

    link = stream_proxy.build_url(token.token)
    ttl_minutes = int(getattr(Config, "STREAM_LINK_TTL_SECONDS", 1800) / 60)
    
    # Generate QR code for easy mobile sharing
    qr_image_path = None
    try:
        import qrcode
        from io import BytesIO
        import os
        
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(link)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to temp file
        qr_image_path = f"/tmp/qr_{token.token[:16]}.png"
        qr_img.save(qr_image_path)
        
    except Exception as e:
        LOGGER.warning(f"QR code generation failed: {e}")
    
    text = (
        "<b>🔗 Stream Link Generated</b>\n\n"
        f"📱 <b>File:</b> <code>{file_name}</code>\n"
        f"🔗 <b>Link:</b> <code>{link}</code>\n"
        f"⏰ <b>Expires in:</b> {ttl_minutes} minutes\n\n"
        "Share this link to download via browser, IDM, or any download manager.\n"
        "Scan the QR code for instant mobile access!"
    )
    
    # Send with QR code if generated
    qr_exists = (
        await asyncio.to_thread(os.path.exists, qr_image_path)
        if qr_image_path
        else False
    )
    if qr_exists:
        try:
            await send_file(message, qr_image_path, caption=text)
            await asyncio.to_thread(os.remove, qr_image_path)  # Clean up temp file
        except Exception as e:
            LOGGER.warning(f"Failed to send QR code: {e}")
            await send_message(message, text)
    else:
        await send_message(message, text)


@new_task
async def onboarding_callback(_, query):
    data = query.data.split()
    message = query.message

    if len(data) < 2:
        await query.answer()
        return

    step = data[1]
    buttons = ButtonMaker()

    if step == "start":
        text = (
            "<b>🚀 Getting Started</b>\n\n"
            "1) Send a link with /mirror or /leech\n"
            "2) Set your default upload destination\n"
            "3) Track tasks with /status\n\n"
            "Pick a step below."
        )
        buttons.data_button("Mirror a Link", "onboard mirror")
        buttons.data_button("Leech to Telegram", "onboard leech")
        buttons.data_button("Set Upload", "onboard settings")
        buttons.data_button("Help Menu", "help menu", position="footer")
        buttons.data_button("Close", "help close", position="footer")
        await edit_message(message, text, buttons.build_menu(2))
        await query.answer()
        return

    if step == "mirror":
        text = (
            "<b>📥 Mirror a Link</b>\n\n"
            "Use: <code>/mirror [link]</code>\n"
            "Tip: /dl is a short alias.\n\n"
            "Reply to a link or file to mirror it."
        )
    elif step == "leech":
        text = (
            "<b>📤 Leech to Telegram</b>\n\n"
            "Use: <code>/leech [link]</code>\n"
            "Tip: /ul is a short alias.\n\n"
            "Reply to a link or file to leech it."
        )
    elif step == "settings":
        text = (
            "<b>⚙️ Set Your Defaults</b>\n\n"
            f"Open user settings: <code>/{BotCommands.UserSetCommand[0]}</code>\n"
            "Pick your default upload target and preferences."
        )
    else:
        await query.answer()
        return

    buttons.data_button("Back", "onboard start")
    buttons.data_button("Help Menu", "help menu")
    buttons.data_button("Close", "help close")
    await edit_message(message, text, buttons.build_menu(2))
    await query.answer()
