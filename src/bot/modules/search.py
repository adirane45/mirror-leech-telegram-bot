from html import escape
from typing import Any
from urllib.parse import quote

from httpx import AsyncClient

from .. import LOGGER
from ..core.config_manager import Config
from ..core.torrent_manager import TorrentManager
from ..helper.ext_utils.bot_utils import new_task
from ..helper.ext_utils.status_utils import get_readable_file_size
from ..helper.ext_utils.telegraph_helper import telegraph
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.message_utils import edit_message, send_message

PLUGINS: list[str] = []
SITES: dict[str, str] | None = None
TELEGRAPH_LIMIT = 300


async def _edit(msg: Any, text: str, button: Any = None) -> Any:
    return await edit_message(msg, text, button)


async def _send(msg: Any, text: str, button: Any = None) -> Any:
    return await send_message(msg, text, button)


async def initiate_search_tools() -> None:
    qb = TorrentManager.qbittorrent
    if qb is None:
        return
    qb_plugins = await qb.search.plugins()
    if qb_plugins:
        names = [plugin.name for plugin in qb_plugins]
        await qb.search.uninstall_plugin(names)
        PLUGINS.clear()
    search_plugins = getattr(Config, "SEARCH_PLUGINS", "")
    if search_plugins:
        await qb.search.install_plugin(search_plugins)

    search_api_link = getattr(Config, "SEARCH_API_LINK", "")
    if search_api_link:
        global SITES
        try:
            async with AsyncClient() as client:
                response = await client.get(f"{search_api_link}/api/v1/sites")
                data: dict[str, Any] = response.json()
            SITES = {
                str(site): str(site).capitalize()
                for site in data.get("supported_sites", [])
            }
            SITES["all"] = "All"
        except Exception as e:
            LOGGER.error(
                f"{e} Can't fetching sites from SEARCH_API_LINK make sure use latest version of API"
            )
            SITES = None


def _get_api_search_url(
    method: str, key: str | None = None, site: str | None = None
) -> str | None:
    """Build API search URL based on method and parameters.
    
    Args:
        method: Search method (apisearch, apitrend, apirecent)
        key: Search query (optional)
        site: Torrent site (optional)
    
    Returns:
        Complete API URL
    """
    search_api_link = getattr(Config, "SEARCH_API_LINK", "")
    search_limit = int(getattr(Config, "SEARCH_LIMIT", 20))
    base_url = f"{search_api_link}/api/v1"
    
    if method == "apisearch":
        if site == "all":
            return f"{base_url}/all/search?query={key}&limit={search_limit}"
        return f"{base_url}/search?site={site}&query={key}&limit={search_limit}"
    
    if method == "apitrend":
        if site == "all":
            return f"{base_url}/all/trending?limit={search_limit}"
        return f"{base_url}/trending?site={site}&limit={search_limit}"
    
    if method == "apirecent":
        if site == "all":
            return f"{base_url}/all/recent?limit={search_limit}"
        return f"{base_url}/recent?site={site}&limit={search_limit}"
    
    return None


async def _search_via_api(
    key: str | None, site: str, message: Any, method: str
) -> tuple[list[dict[str, Any]] | None, str | None]:
    """Perform search via API.
    
    Args:
        key: Search query
        site: Torrent site
        message: Telegram message object
        method: Search method (apisearch, apitrend, apirecent)
    
    Returns:
        Tuple of (search_results, msg) or (None, None) on error
    """
    api_url = _get_api_search_url(method, key, site)
    if api_url is None:
        await _edit(message, "Invalid API method")
        return None, None
    
    try:
        async with AsyncClient() as client:
            response = await client.get(api_url)
            search_results: dict[str, Any] = response.json()
        
        if "error" in search_results or int(search_results.get("total", 0)) == 0:
            site_name = SITES.get(site, site.capitalize()) if SITES else site.capitalize()
            await _edit(
                message,
                f"No result found for <i>{key or ''}</i>\nTorrent Site:- <i>{site_name}</i>",
            )
            return None, None
        
        # Build result message
        total = int(search_results.get("total", 0))
        msg = f"<b>Found {min(total, TELEGRAPH_LIMIT)}</b>"
        site_name = SITES.get(site, site.capitalize()) if SITES else site.capitalize()
        if method == "apitrend":
            msg += f" <b>trending result(s)\nTorrent Site:- <i>{site_name}</i></b>"
        elif method == "apirecent":
            msg += f" <b>recent result(s)\nTorrent Site:- <i>{site_name}</i></b>"
        else:
            msg += f" <b>result(s) for <i>{key or ''}</i>\nTorrent Site:- <i>{site_name}</i></b>"
        
        return list(search_results.get("data", [])), msg
    
    except Exception as e:
        await _edit(message, str(e))
        return None, None


async def _search_via_plugins(
    key: str, site: str, message: Any
) -> tuple[list[Any] | None, str | None]:
    """Perform search via qbittorrent plugins.
    
    Args:
        key: Search query
        site: Torrent site
        message: Telegram message object
    
    Returns:
        Tuple of (search_results, msg) or (None, None) on error
    """
    try:
        qb = TorrentManager.qbittorrent
        if qb is None:
            await _edit(message, "qBittorrent client is not available")
            return None, None

        search = await qb.search.start(
            pattern=key, plugins=[site], category="all"
        )
        search_id = search.id
        
        # Wait for search to complete
        while True:
            result_status = await qb.search.status(search_id)
            if result_status[0].status != "Running":
                break
        
        dict_search_results = await qb.search.results(
            id=search_id, limit=TELEGRAPH_LIMIT
        )
        search_results = dict_search_results.results
        total_results = dict_search_results.total
        
        if total_results == 0:
            await _edit(
                message,
                f"No result found for <i>{key}</i>\nTorrent Site:- <i>{site.capitalize()}</i>",
            )
            return None, None
        
        msg = f"<b>Found {min(total_results, TELEGRAPH_LIMIT)}</b>"
        msg += f" <b>result(s) for <i>{key}</i>\nTorrent Site:- <i>{site.capitalize()}</i></b>"
        
        await qb.search.delete(search_id)
        return search_results, msg
    
    except Exception as e:
        await _edit(message, str(e))
        return None, None


async def search(key: str | None, site: str, message: Any, method: str) -> None:
    """Perform torrent search via API or plugins.
    
    Args:
        key: Search query
        site: Torrent site
        message: Telegram message object
        method: Search method (apisearch, apitrend, apirecent, plugin)
    """
    # Determine search method and execute
    if method.startswith("api"):
        LOGGER.info(f"API Searching: {key} from {site} ({method})")
        search_results, msg = await _search_via_api(key, site, message, method)
    else:
        LOGGER.info(f"PLUGINS Searching: {key} from {site}")
        search_results, msg = await _search_via_plugins(key or "", site, message)
    
    if search_results is None:
        return
    
    # Get results and display
    link = await get_result(search_results, key, message, method)
    buttons = ButtonMaker()
    buttons.url_button("🔎 VIEW", link)
    button = buttons.build_menu(1)
    await _edit(message, str(msg), button)


async def get_result(
    search_results: list[Any], key: str | None, message: Any, method: str
) -> str:
    telegraph_content: list[str] = []
    msg = _build_search_result_title(method, key)
    for index, result in enumerate(search_results, start=1):
        if method.startswith("api"):
            try:
                msg += _build_api_result_message(result)
            except (KeyError, TypeError) as e:
                LOGGER.debug(f"Skipping malformed search result: {e}")
                continue
        else:
            msg += _build_plugin_result_message(result)

        if len(msg.encode("utf-8")) > 39000:
            telegraph_content.append(msg)
            msg = ""

        if index == TELEGRAPH_LIMIT:
            break

    if msg != "":
        telegraph_content.append(msg)

    await _edit(
        message, f"<b>Creating</b> {len(telegraph_content)} <b>Telegraph pages.</b>"
    )
    path = [
        (
            await telegraph.create_page(
                title="Mirror-leech-bot Torrent Search", content=content
            )
        )["path"]
        for content in telegraph_content
    ]
    if len(path) > 1:
        await _edit(
            message, f"<b>Editing</b> {len(telegraph_content)} <b>Telegraph pages.</b>"
        )
        await telegraph.edit_telegraph(path, telegraph_content)
    return f"https://telegra.ph/{path[0]}"


def _build_search_result_title(method: str, key: str | None) -> str:
    titles = {
        "apirecent": "<h4>API Recent Results</h4>",
        "apisearch": f"<h4>API Search Result(s) For {key}</h4>",
        "apitrend": "<h4>API Trending Results</h4>",
    }
    return titles.get(method, f"<h4>PLUGINS Search Result(s) For {key}</h4>")


def _build_api_result_message(result: dict[str, Any]) -> str:
    msg = ""
    if "name" in result.keys():
        msg += f"<code><a href='{result['url']}'>{escape(result['name'])}</a></code><br>"
    if "torrents" in result.keys():
        msg += _build_api_torrents_message(result["torrents"])
    else:
        msg += _build_api_single_result_message(result)
    return msg


def _build_api_torrents_message(torrents: list[dict[str, Any]]) -> str:
    msg = ""
    for subres in torrents:
        msg += f"<b>Quality: </b>{subres['quality']} | <b>Type: </b>{subres['type']} | "
        msg += f"<b>Size: </b>{subres['size']}<br>"
        if "torrent" in subres.keys():
            msg += f"<a href='{subres['torrent']}'>Direct Link</a><br>"
        elif "magnet" in subres.keys():
            msg += "<b>Share Magnet to</b> "
            msg += f"<a href='http://t.me/share/url?url={subres['magnet']}'>Telegram</a><br>"
    msg += "<br>"
    return msg


def _build_api_single_result_message(result: dict[str, Any]) -> str:
    msg = f"<b>Size: </b>{result['size']}<br>"
    try:
        msg += f"<b>Seeders: </b>{result['seeders']} | <b>Leechers: </b>{result['leechers']}<br>"
    except KeyError:
        pass
    if "torrent" in result.keys():
        msg += f"<a href='{result['torrent']}'>Direct Link</a><br><br>"
    elif "magnet" in result.keys():
        msg += "<b>Share Magnet to</b> "
        msg += f"<a href='http://t.me/share/url?url={quote(result['magnet'])}'>Telegram</a><br><br>"
    else:
        msg += "<br>"
    return msg


def _build_plugin_result_message(result: Any) -> str:
    msg = f"<a href='{result.descrLink}'>{escape(result.fileName)}</a><br>"
    msg += f"<b>Size: </b>{get_readable_file_size(result.fileSize)}<br>"
    msg += f"<b>Seeders: </b>{result.nbSeeders} | <b>Leechers: </b>{result.nbLeechers}<br>"
    link = result.fileUrl
    if link.startswith("magnet:"):
        msg += f"<b>Share Magnet to</b> <a href='http://t.me/share/url?url={quote(link)}'>Telegram</a><br><br>"
    else:
        msg += f"<a href='{link}'>Direct Link</a><br><br>"
    return msg


def api_buttons(user_id: int, method: str) -> Any:
    buttons = ButtonMaker()
    for data, name in (SITES or {}).items():
        buttons.data_button(name, f"torser {user_id} {data} {method}")
    buttons.data_button("Cancel", f"torser {user_id} cancel")
    return buttons.build_menu(2)


async def plugin_buttons(user_id: int) -> Any:
    buttons = ButtonMaker()
    if not PLUGINS:
        qb = TorrentManager.qbittorrent
        if qb is None:
            buttons.data_button("Cancel", f"torser {user_id} cancel")
            return buttons.build_menu(2)
        pl = await qb.search.plugins()
        for i in pl:
            PLUGINS.append(i.name)
    for siteName in PLUGINS:
        buttons.data_button(
            siteName.capitalize(), f"torser {user_id} {siteName} plugin"
        )
    buttons.data_button("All", f"torser {user_id} all plugin")
    buttons.data_button("Cancel", f"torser {user_id} cancel")
    return buttons.build_menu(2)


@new_task  # type: ignore[untyped-decorator]
async def torrent_search(_: Any, message: Any) -> None:
    user_id = message.from_user.id
    buttons = ButtonMaker()
    key = message.text.split()
    search_plugins = getattr(Config, "SEARCH_PLUGINS", "")
    if SITES is None and not search_plugins:
        await _send(
            message, "No API link or search PLUGINS added for this function"
        )
    elif len(key) == 1 and SITES is None:
        await _send(message, "Send a search key along with command")
    elif len(key) == 1:
        buttons.data_button("Trending", f"torser {user_id} apitrend")
        buttons.data_button("Recent", f"torser {user_id} apirecent")
        buttons.data_button("Cancel", f"torser {user_id} cancel")
        button = buttons.build_menu(2)
        await _send(message, "Send a search key along with command", button)
    elif SITES is not None and search_plugins:
        buttons.data_button("Api", f"torser {user_id} apisearch")
        buttons.data_button("Plugins", f"torser {user_id} plugin")
        buttons.data_button("Cancel", f"torser {user_id} cancel")
        button = buttons.build_menu(2)
        await _send(message, "Choose tool to search:", button)
    elif SITES is not None:
        button = api_buttons(user_id, "apisearch")
        await _send(message, "Choose site to search | API:", button)
    else:
        button = await plugin_buttons(user_id)
        await _send(message, "Choose site to search | Plugins:", button)


@new_task  # type: ignore[untyped-decorator]
async def torrent_search_update(_: Any, query: Any) -> None:
    user_id = query.from_user.id
    message = query.message
    key = message.reply_to_message.text.split(maxsplit=1)
    key = key[1].strip() if len(key) > 1 else None
    data = query.data.split()
    if user_id != int(data[1]):
        await query.answer("Not Yours!", show_alert=True)
    elif data[2].startswith("api"):
        await query.answer()
        button = api_buttons(user_id, data[2])
        await _edit(message, "Choose site:", button)
    elif data[2] == "plugin":
        await query.answer()
        button = await plugin_buttons(user_id)
        await _edit(message, "Choose site:", button)
    elif data[2] != "cancel":
        await query.answer()
        site = data[2]
        method = data[3]
        if method.startswith("api"):
            if key is None:
                if method == "apirecent":
                    endpoint = "Recent"
                elif method == "apitrend":
                    endpoint = "Trending"
                await edit_message(
                    message,
                    f"<b>Listing {endpoint} Items...\nTorrent Site:- <i>{(SITES or {}).get(site, site.capitalize())}</i></b>",
                )
            else:
                await _edit(
                    message,
                    f"<b>Searching for <i>{key}</i>\nTorrent Site:- <i>{(SITES or {}).get(site, site.capitalize())}</i></b>",
                )
        else:
            await _edit(
                message,
                f"<b>Searching for <i>{key}</i>\nTorrent Site:- <i>{site.capitalize()}</i></b>",
            )
        await search(key, site, message, method)
    else:
        await query.answer()
        await _edit(message, "Search has been canceled!")
