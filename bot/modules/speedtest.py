from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE

from ..helper.ext_utils.bot_utils import new_task
from ..helper.telegram_helper.message_utils import send_message, edit_message


@new_task
async def speedtest(_, message):
    """Run speedtest and display results with progress - Modified by: justadi"""
    speed_msg = await send_message(message, "<b>🚀 Running speedtest...</b>\n<i>Please wait, this may take a moment.</i>")
    
    try:
        # Try using Python speedtest module directly (most reliable)
        try:
            import speedtest
            
            # Update message with connecting status
            await edit_message(speed_msg, "<b>🚀 Running speedtest...</b>\n\n<b>Connecting to servers...</b>\n<code>■░░░░░░░░░░░░░░░░░░</code>")
            
            st = speedtest.Speedtest()
            st.get_servers()
            
            # Update message with testing download
            await edit_message(speed_msg, "<b>🚀 Running speedtest...</b>\n\n<b>Testing download speed...</b>\n<code>■■■■░░░░░░░░░░░░░░░</code>")
            
            download = st.download()
            
            # Update message with testing upload
            await edit_message(speed_msg, "<b>🚀 Running speedtest...</b>\n\n<b>Testing upload speed...</b>\n<code>■■■■■■■■■■░░░░░░░░░</code>")
            
            upload = st.upload()
            
            # Update message with getting ping
            await edit_message(speed_msg, "<b>🚀 Running speedtest...</b>\n\n<b>Getting ping...</b>\n<code>■■■■■■■■■■■■■■■■░░░</code>")
            
            st.get_best_server()
            ping = st.results.ping
            
            # Format results
            result_text = "<b>🚀 Speedtest Results</b>\n"
            result_text += "=" * 25 + "\n\n"
            result_text += f"<b>📡 Ping:</b> <code>{ping:.2f}</code> ms\n"
            result_text += f"<b>⬇️ Download:</b> <code>{download / 1_000_000:.2f}</code> Mbps\n"
            result_text += f"<b>⬆️ Upload:</b> <code>{upload / 1_000_000:.2f}</code> Mbps\n\n"
            result_text += "=" * 25 + "\n"
            result_text += "<b>Status:</b> ✅ Test Completed\n"
            
            await edit_message(speed_msg, result_text)
            
        except ImportError:
            # Fallback to subprocess call
            cmd = ["speedtest-cli", "--simple", "--secure"]
            process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                # Try alternative command
                cmd = ["python3", "-m", "speedtest", "--simple", "--secure"]
                process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    error_msg = stderr.decode().strip() if stderr else "Command not found"
                    await edit_message(
                        speed_msg,
                        f"<b>❌ Speedtest Failed!</b>\n\n"
                        f"<code>{error_msg}</code>\n\n"
                        "<i>Make sure speedtest-cli is installed:\n"
                        "pip install speedtest-cli</i>"
                    )
                    return
            
            output = stdout.decode().strip()
            if not output:
                stderr_text = stderr.decode().strip() if stderr else ""
                await edit_message(
                    speed_msg,
                    "<b>❌ Speedtest Error!</b>\n\n"
                    f"<code>{stderr_text or 'No output received from speedtest'}</code>"
                )
                return

            ping = download = upload = None
            for line in output.splitlines():
                if line.startswith("Ping:"):
                    ping = line.split("Ping:", 1)[1].strip().replace("ms", "").strip()
                elif line.startswith("Download:"):
                    download = line.split("Download:", 1)[1].strip()
                elif line.startswith("Upload:"):
                    upload = line.split("Upload:", 1)[1].strip()

            if ping or download or upload:
                result_text = "<b>🚀 Speedtest Results</b>\n"
                result_text += "=" * 25 + "\n\n"
                if ping:
                    result_text += f"<b>📡 Ping:</b> <code>{ping}</code> ms\n"
                if download:
                    result_text += f"<b>⬇️ Download:</b> <code>{download}</code>\n"
                if upload:
                    result_text += f"<b>⬆️ Upload:</b> <code>{upload}</code>\n"
                result_text += "\n" + "=" * 25 + "\n"
                result_text += "<b>Status:</b> ✅ Test Completed\n"
                await edit_message(speed_msg, result_text)
            else:
                await edit_message(speed_msg, f"<b>Speedtest Results:</b>\n<code>{output}</code>")
        
    except Exception as e:
        await edit_message(
            speed_msg,
            f"<b>❌ Speedtest Error!</b>\n\n<code>{str(e)[:200]}</code>"
        )
