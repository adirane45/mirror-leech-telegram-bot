from time import time
from ... import download_history
from .status_utils import get_readable_time, get_readable_file_size


def add_history(
    name,
    size=0,
    status="success",
    user_id=0,
    tag="",
    link="",
    tool="",
):
    entry = {
        "name": name,
        "size": size,
        "status": status,
        "user_id": user_id,
        "tag": tag,
        "link": link,
        "tool": tool,
        "time": time(),
    }
    download_history.appendleft(entry)


def format_history(entries, limit=10):
    lines = []
    for index, item in enumerate(entries[:limit], start=1):
        status_emoji = "✅" if item["status"] == "success" else "❌"
        age = get_readable_time(int(time() - item["time"]))
        size = get_readable_file_size(item.get("size", 0))
        name = item.get("name", "-")
        lines.append(
            f"{index}. {status_emoji} <code>{name}</code> | {size} | {age} ago"
        )
    return "\n".join(lines)
