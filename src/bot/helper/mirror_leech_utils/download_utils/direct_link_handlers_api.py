"""API-Based Handlers Module

Handles direct link generation for services using APIs:
- Solid Files, Kraken Files, Easy Upload
- PixelDrain, Racaty
- OneDrive, GitHub, Yandex.Disk
- OSDN
"""

from cloudscraper import create_scraper
from lxml.etree import HTML
from re import findall, search, match
from requests import Session, get, post
from requests.adapters import HTTPAdapter
from urllib.parse import parse_qs, urlparse
from urllib3.util.retry import Retry
from uuid import uuid4
from base64 import b64encode

from ....core.config_manager import Config
from ...ext_utils.exceptions import DirectDownloadLinkException
from ...ext_utils.help_messages import PASSWORD_ERROR_MESSAGE


def osdn(url):
    with create_scraper() as session:
        try:
            html = HTML(session.get(url).text)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        if not (direct_link := html.xapth('//a[@class="mirror_link"]/@href')):
            raise DirectDownloadLinkException("ERROR: Direct link not found")
        return f"https://osdn.net{direct_link[0]}"


def yandex_disk(url: str) -> str:
    """Yandex.Disk direct link generator
    Based on https://github.com/wldhx/yadisk-direct"""
    try:
        link = findall(r"\b(https?://(yadi\.sk|disk\.yandex\.(com|ru))\S+)", url)[0][0]
    except IndexError:
        return "No Yandex.Disk links found\n"
    api = "https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={}"
    try:
        return get(api.format(link)).json()["href"]
    except KeyError as e:
        raise DirectDownloadLinkException(
            "ERROR: File not found/Download limit reached"
        ) from e


def github(url):
    """GitHub direct links generator"""
    try:
        # Support both release URLs and archive URLs
        match_result = findall(r"\bhttps?://.*github\.com.*(?:releases|archive)\S+", url)[0]
    except IndexError as e:
        # If not a releases or archive URL, treat as archive attempt
        if "github.com" not in url:
            raise DirectDownloadLinkException("Not a GitHub link") from e
        # Try to handle as direct archive link
        match_result = url
    
    with create_scraper() as session:
        _res = session.get(match_result, stream=True, allow_redirects=True)
        # For archive URLs, get the final URL after redirect
        if _res.url != match_result:
            return _res.url
        # For release URLs, check for location header
        if "location" in _res.headers:
            return _res.headers["location"]
        # If it's an archive URL, return the final resolved URL
        if "/archive/" in match_result or "/releases/" in match_result:
            return _res.url
        raise DirectDownloadLinkException("ERROR: Can't extract the link")


def onedrive(link):
    """Onedrive direct link generator
    By https://github.com/junedkh"""
    with create_scraper() as session:
        try:
            link = session.get(link).url
            parsed_link = urlparse(link)
            link_data = parse_qs(parsed_link.query)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        if not link_data:
            raise DirectDownloadLinkException("ERROR: Unable to find link_data")
        folder_id = link_data.get("resid")
        if not folder_id:
            raise DirectDownloadLinkException("ERROR: folder id not found")
        folder_id = folder_id[0]
        authkey = link_data.get("authkey")
        if not authkey:
            raise DirectDownloadLinkException("ERROR: authkey not found")
        authkey = authkey[0]
        boundary = uuid4()
        headers = {"content-type": f"multipart/form-data;boundary={boundary}"}
        data = f"--{boundary}\r\nContent-Disposition: form-data;name=data\r\nPrefer: Migration=EnableRedirect;FailOnMigratedFiles\r\nX-HTTP-Method-Override: GET\r\nContent-Type: application/json\r\n\r\n--{boundary}--"
        try:
            resp = session.get(
                f'https://api.onedrive.com/v1.0/drives/{folder_id.split("!", 1)[0]}/items/{folder_id}?$select=id,@content.downloadUrl&ump=1&authKey={authkey}',
                headers=headers,
                data=data,
            ).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if "@content.downloadUrl" not in resp:
        raise DirectDownloadLinkException("ERROR: Direct link not found")
    return resp["@content.downloadUrl"]


def pixeldrain(url):
    try:
        url = url.rstrip("/")
        code = url.split("/")[-1].split("?", 1)[0]
        response = get("https://pd.cybar.xyz/", allow_redirects=True)
        return response.url + code
    except Exception as e:
        raise DirectDownloadLinkException("ERROR: Direct link not found")


def racaty(url):
    with create_scraper() as session:
        try:
            url = session.get(url).url
            json_data = {"op": "download2", "id": url.split("/")[-1]}
            html = HTML(session.post(url, data=json_data).text)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if direct_link := html.xpath("//a[@id='uniqueExpirylink']/@href"):
        return direct_link[0]
    else:
        raise DirectDownloadLinkException("ERROR: Direct link not found")


def solidfiles(url):
    """Solidfiles direct link generator
    Based on https://github.com/Xonshiz/SolidFiles-Downloader
    By https://github.com/Jusidama18"""
    with create_scraper() as session:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36"
            }
            pageSource = session.get(url, headers=headers).text
            mainOptions = str(
                search(r"viewerOptions\'\,\ (.*?)\)\;", pageSource).group(1)
            )
            from json import loads
            return loads(mainOptions)["downloadUrl"]
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e


def krakenfiles(url):
    with Session() as session:
        try:
            _res = session.get(url)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        html = HTML(_res.text)
        if post_url := html.xpath('//form[@id="dl-form"]/@action'):
            post_url = f"https://krakenfiles.com{post_url[0]}"
        else:
            raise DirectDownloadLinkException("ERROR: Unable to find post link.")
        if token := html.xpath('//input[@id="dl-token"]/@value'):
            data = {"token": token[0]}
        else:
            raise DirectDownloadLinkException("ERROR: Unable to find token for post.")
        try:
            _json = session.post(post_url, data=data).json()
        except Exception as e:
            raise DirectDownloadLinkException(
                f"ERROR: {e.__class__.__name__} While send post request"
            ) from e
    if _json["status"] != "ok":
        raise DirectDownloadLinkException(
            "ERROR: Unable to find download after post request"
        )
    return _json["url"]


def get_captcha_token(session, params):
    recaptcha_api = "https://www.google.com/recaptcha/api2"
    res = session.get(f"{recaptcha_api}/anchor", params=params)
    anchor_html = HTML(res.text)
    if not (anchor_token := anchor_html.xpath('//input[@id="recaptcha-token"]/@value')):
        return None
    params["c"] = anchor_token[0]
    params["reason"] = "q"
    res = session.post(f"{recaptcha_api}/reload", params=params)
    if token := findall(r'"rresp","(.*?)"', res.text):
        return token[0]


def easyupload(url):
    if "::" in url:
        _password = url.split("::")[-1]
        url = url.split("::")[-2]
    else:
        _password = ""
    file_id = url.split("/")[-1]
    with create_scraper() as session:
        try:
            _res = session.get(url)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
        first_page_html = HTML(_res.text)
        if (
            first_page_html.xpath("//h6[contains(text(),'Password Protected')]")
            and not _password
        ):
            raise DirectDownloadLinkException(
                f"ERROR:\n{PASSWORD_ERROR_MESSAGE.format(url)}"
            )
        if not (
            match_result := search(
                r"https://eu(?:[1-9][0-9]?|100)\.easyupload\.io/action\.php", _res.text
            )
        ):
            raise DirectDownloadLinkException(
                "ERROR: Failed to get server for EasyUpload Link"
            )
        action_url = match_result.group()
        session.headers.update({"referer": "https://easyupload.io/"})
        recaptcha_params = {
            "k": "6LfWajMdAAAAAGLXz_nxz2tHnuqa-abQqC97DIZ3",
            "ar": "1",
            "co": "aHR0cHM6Ly9lYXN5dXBsb2FkLmlvOjQ0Mw..",
            "hl": "en",
            "v": "0hCdE87LyjzAkFO5Ff-v7Hj1",
            "size": "invisible",
            "cb": "c3o1vbaxbmwe",
        }
        if not (captcha_token := get_captcha_token(session, recaptcha_params)):
            raise DirectDownloadLinkException("ERROR: Captcha token not found")
        try:
            data = {
                "type": "download-token",
                "url": file_id,
                "value": _password,
                "captchatoken": captcha_token,
                "method": "regular",
            }
            json_resp = session.post(url=action_url, data=data).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if "download_link" in json_resp:
        return json_resp["download_link"]
    elif "data" in json_resp:
        raise DirectDownloadLinkException(
            f"ERROR: Failed to generate direct link due to {json_resp['data']}"
        )
    raise DirectDownloadLinkException(
        "ERROR: Failed to generate direct link from EasyUpload."
    )


__all__ = [
    "osdn",
    "yandex_disk",
    "github",
    "onedrive",
    "pixeldrain",
    "racaty",
    "solidfiles",
    "krakenfiles",
    "easyupload",
]
