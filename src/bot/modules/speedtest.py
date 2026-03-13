from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE

from ..helper.ext_utils.bot_utils import new_task
from ..helper.telegram_helper.message_utils import edit_message, send_message


def _format_success_result(ping, download, upload):
    result_text = "<b>🚀 Speedtest Results</b>\n"
    result_text += "=" * 25 + "\n\n"
    result_text += f"<b>📡 Ping:</b> <code>{ping:.2f}</code> ms\n"
    result_text += f"<b>⬇️ Download:</b> <code>{download / 1_000_000:.2f}</code> Mbps\n"
    result_text += f"<b>⬆️ Upload:</b> <code>{upload / 1_000_000:.2f}</code> Mbps\n\n"
    result_text += "=" * 25 + "\n"
    result_text += "<b>Status:</b> ✅ Test Completed\n"
    return result_text


def _format_cli_result(ping, download, upload):
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
    return result_text


async def _update_progress(speed_msg, status, bar):
    await edit_message(
        speed_msg,
        f"<b>🚀 Running speedtest...</b>\n\n<b>{status}</b>\n<code>{bar}</code>",
    )


async def _run_python_speedtest(speed_msg):
    import speedtest

    await _update_progress(speed_msg, "Connecting to servers...", "■░░░░░░░░░░░░░░░░░░")
    st = speedtest.Speedtest()
    st.get_servers()

    await _update_progress(
        speed_msg, "Testing download speed...", "■■■■░░░░░░░░░░░░░░░"
    )
    download = st.download()

    await _update_progress(
        speed_msg, "Testing upload speed...", "■■■■■■■■■■░░░░░░░░░"
    )
    upload = st.upload()

    await _update_progress(speed_msg, "Getting ping...", "■■■■■■■■■■■■■■■■░░░")
    st.get_best_server()
    ping = st.results.ping

    return _format_success_result(ping, download, upload)


async def _exec_speedtest_command(cmd):
    process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = await process.communicate()
    return process.returncode, stdout, stderr


def _decode_output(stdout, stderr):
    output = stdout.decode().strip() if stdout else ""
    stderr_text = stderr.decode().strip() if stderr else ""
    return output, stderr_text


def _parse_cli_output(output):
    ping = download = upload = None
    for line in output.splitlines():
        if line.startswith("Ping:"):
            ping = line.split("Ping:", 1)[1].strip().replace("ms", "").strip()
        elif line.startswith("Download:"):
            download = line.split("Download:", 1)[1].strip()
        elif line.startswith("Upload:"):
            upload = line.split("Upload:", 1)[1].strip()
    return ping, download, upload


async def _run_cli_speedtest():
    return_code, stdout, stderr = await _exec_speedtest_command(
        ["speedtest-cli", "--simple", "--secure"]
    )
    if return_code != 0:
        return_code, stdout, stderr = await _exec_speedtest_command(
            ["python3", "-m", "speedtest", "--simple", "--secure"]
        )
        if return_code != 0:
            _, stderr_text = _decode_output(stdout, stderr)
            error_msg = stderr_text or "Command not found"
            return (
                "<b>❌ Speedtest Failed!</b>\n\n"
                f"<code>{error_msg}</code>\n\n"
                "<i>Make sure speedtest-cli is installed:\n"
                "pip install speedtest-cli</i>"
            )

    output, stderr_text = _decode_output(stdout, stderr)
    if not output:
        return (
            "<b>❌ Speedtest Error!</b>\n\n"
            f"<code>{stderr_text or 'No output received from speedtest'}</code>"
        )

    ping, download, upload = _parse_cli_output(output)
    if ping or download or upload:
        return _format_cli_result(ping, download, upload)
    return f"<b>Speedtest Results:</b>\n<code>{output}</code>"


@new_task
async def speedtest(_, message):
    """Run speedtest and display results with progress - Modified by: justadi"""
    speed_msg = await send_message(message, "<b>🚀 Running speedtest...</b>\n<i>Please wait, this may take a moment.</i>")

    try:
        try:
            result_text = await _run_python_speedtest(speed_msg)
        except ImportError:
            result_text = await _run_cli_speedtest()

        await edit_message(speed_msg, result_text)

    except Exception as e:
        await edit_message(
            speed_msg,
            f"<b>❌ Speedtest Error!</b>\n\n<code>{str(e)[:200]}</code>"
        )
