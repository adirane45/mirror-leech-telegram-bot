from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE

from ..helper.ext_utils.bot_utils import new_task
from ..helper.telegram_helper.message_utils import send_message, edit_message


@new_task
async def speedtest(_, message):
    """Run speedtest and display results - Modified by: justadi"""
    speed_msg = await send_message(message, "<b>🚀 Running speedtest...</b>\n<i>Modified by: justadi</i>")
    
    try:
        # Run speedtest-cli with simple output
        cmd = ["speedtest-cli", "--simple"]
        process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode().strip() if stderr else "Unknown error"
            await edit_message(
                speed_msg,
                f"<b>❌ Speedtest Failed!</b>\n\n<code>{error_msg}</code>\n\n<i>Modified by: justadi</i>"
            )
            return
        
        # Parse the output
        output = stdout.decode().strip()
        lines = output.split('\n')
        
        result_text = "<b>🚀 Speedtest Results</b>\n"
        result_text += "<i>Modified by: justadi</i>\n\n"
        
        for line in lines:
            if line.startswith("Ping:"):
                ping = line.split(":")[1].strip()
                result_text += f"<b>📡 Ping:</b> <code>{ping}</code> ms\n"
            elif line.startswith("Download:"):
                download = line.split(":")[1].strip()
                result_text += f"<b>⬇️ Download:</b> <code>{download}</code> Mbps\n"
            elif line.startswith("Upload:"):
                upload = line.split(":")[1].strip()
                result_text += f"<b>⬆️ Upload:</b> <code>{upload}</code> Mbps\n"
        
        await edit_message(speed_msg, result_text)
        
    except FileNotFoundError:
        await edit_message(
            speed_msg,
            "<b>❌ Speedtest Error!</b>\n\n"
            "<code>speedtest-cli is not installed.\n"
            "Please install it using:\n"
            "pip install speedtest-cli</code>\n\n"
            "<i>Modified by: justadi</i>"
        )
    except Exception as e:
        await edit_message(
            speed_msg,
            f"<b>❌ Speedtest Error!</b>\n\n<code>{str(e)}</code>\n\n<i>Modified by: justadi</i>"
        )
