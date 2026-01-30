from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE

from ..helper.ext_utils.bot_utils import new_task
from ..helper.telegram_helper.message_utils import send_message, edit_message


@new_task
async def speedtest(_, message):
    """Run speedtest and display results - Modified by: justadi"""
    speed_msg = await send_message(message, "<b>🚀 Running speedtest...</b>\n<i>Please wait, this may take a moment.</i>")
    
    try:
        # Try ookla speedtest first (more reliable)
        cmd = ["speedtest", "--accept-license", "--accept-gdpr"]
        process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            # Fallback to speedtest-cli
            cmd = ["speedtest-cli", "--simple", "--secure"]
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
        
        if not output:
            await edit_message(
                speed_msg,
                "<b>❌ Speedtest Error!</b>\n\n<code>No output received from speedtest</code>\n\n<i>Modified by: justadi</i>"
            )
            return
            
        lines = output.split('\n')
        
        result_text = "<b>🚀 Speedtest Results</b>\n"
        result_text += "<i>Modified by: justadi</i>\n\n"
        
        found_data = False
        # Parse ookla speedtest output
        for line in lines:
            if "Latency:" in line or "Idle Latency:" in line:
                try:
                    ping = line.split(":")[1].strip().split()[0]
                    result_text += f"<b>📡 Ping:</b> <code>{ping}</code> ms\n"
                    found_data = True
                except:
                    pass
            elif "Download:" in line:
                try:
                    download = line.split(":")[1].strip()
                    result_text += f"<b>⬇️ Download:</b> <code>{download}</code>\n"
                    found_data = True
                except:
                    pass
            elif "Upload:" in line:
                try:
                    upload = line.split(":")[1].strip()
                    result_text += f"<b>⬆️ Upload:</b> <code>{upload}</code>\n"
                    found_data = True
                except:
                    pass
            # Fallback for speedtest-cli format
            elif line.startswith("Ping:"):
                try:
                    ping = line.split(":")[1].strip()
                    result_text += f"<b>📡 Ping:</b> <code>{ping}</code>\n"
                    found_data = True
                except:
                    pass
        
        if not found_data:
            # If parsing failed, show raw output
            result_text += f"\n<code>{output[:500]}</code>"
            
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
