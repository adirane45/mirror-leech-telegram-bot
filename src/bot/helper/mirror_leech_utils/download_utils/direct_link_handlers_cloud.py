"""Cloud Storage Handlers Module

Handles direct link generation for cloud storage services:
- TeraBox, GoFile, LinkBox, MediaFire Folder
- FilePress, Sharer Scraper, WeTransfer
- pCloud, AKM Files, Shrdsk
"""

from cloudscraper import create_scraper
from hashlib import sha256
from json import loads
from lxml.etree import HTML
from os import path as ospath
from re import findall, match, search
from requests import Session, post, get
from requests.adapters import HTTPAdapter
from urllib.parse import parse_qs, urlparse, quote
from urllib3.util.retry import Retry
from uuid import uuid4
from base64 import b64decode
import time

from ....core.config_manager import Config
from .direct_link_handlers_base import FolderHandler, TokenHandler
from ...ext_utils.exceptions import DirectDownloadLinkException
from ...ext_utils.help_messages import PASSWORD_ERROR_MESSAGE
from ...ext_utils.links_utils import is_share_link
from ...ext_utils.status_utils import speed_string_to_bytes

user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
)


def _extract_password(url, separator="::"):
    """Extract and remove password from URL if present (guard clause style)"""
    if separator not in url:
        return url, ""
    
    parts = url.split(separator)
    if len(parts) != 2:
        return url, ""
    
    return parts[0], parts[1]


def terabox(url):
    if "/file/" in url:
        return url
    api_url = f"https://wdzone-terabox-api.vercel.app/api?url={quote(url)}"
    try:
        with Session() as session:
            req = session.get(api_url, headers={"User-Agent": user_agent}).json()
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e

    details = {"contents": [], "title": "", "total_size": 0}
    if "✅ Status" not in req:
        raise DirectDownloadLinkException("ERROR: File not found!")
    for data in req["📜 Extracted Info"]:
        item = {
            "path": "",
            "filename": data["📂 Title"],
            "url": data["🔽 Direct Download Link"],
        }
        details["contents"].append(item)
        size = (data["📏 Size"]).replace(" ", "")
        size = speed_string_to_bytes(size)
        details["total_size"] += size
    details["title"] = req["📜 Extracted Info"][0]["📂 Title"]
    if len(details["contents"]) == 1:
        return details["contents"][0]["url"]
    return details


def filepress(url):
    try:
        url = get(f"https://filebee.xyz/file/{url.split('/')[-1]}").url
        raw = urlparse(url)
        json_data = {
            "id": raw.path.split("/")[-1],
            "method": "publicDownlaod",
        }
        api = f"{raw.scheme}://{raw.hostname}/api/file/downlaod/"
        res2 = post(
            api,
            headers={"Referer": f"{raw.scheme}://{raw.hostname}"},
            json=json_data,
        ).json()
        json_data2 = {
            "id": res2["data"],
            "method": "publicDownlaod",
        }
        api2 = f"{raw.scheme}://{raw.hostname}/api/file/downlaod2/"
        res = post(
            api2,
            headers={"Referer": f"{raw.scheme}://{raw.hostname}"},
            json=json_data2,
        ).json()
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e

    if "data" not in res:
        raise DirectDownloadLinkException(f'ERROR: {res["statusText"]}')
    return f'https://drive.google.com/uc?id={res["data"]}&export=download'


def sharer_scraper(url):
    cget = create_scraper().request
    try:
        url = cget("GET", url).url
        raw = urlparse(url)
        header = {
            "useragent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.548.0 Safari/534.10"
        }
        res = cget("GET", url, headers=header)
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    key = findall(r'"key",\s+"(.*?)"', res.text)
    if not key:
        raise DirectDownloadLinkException("ERROR: Key not found!")
    key = key[0]
    if not HTML(res.text).xpath("//button[@id='drc']"):
        raise DirectDownloadLinkException(
            "ERROR: This link don't have direct download button"
        )
    boundary = uuid4()
    headers = {
        "Content-Type": f"multipart/form-data; boundary=----WebKitFormBoundary{boundary}",
        "x-token": raw.hostname,
        "useragent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.548.0 Safari/534.10",
    }

    data = (
        f'------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="action"\r\n\r\ndirect\r\n'
        f'------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="key"\r\n\r\n{key}\r\n'
        f'------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="action_token"\r\n\r\n\r\n'
        f"------WebKitFormBoundary{boundary}--\r\n"
    )
    try:
        res = cget("POST", url, cookies=res.cookies, headers=headers, data=data).json()
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if "url" not in res:
        raise DirectDownloadLinkException(
            "ERROR: Drive Link not found, Try in your browser"
        )
    if "drive.google.com" in res["url"] or "drive.usercontent.google.com" in res["url"]:
        return res["url"]
    try:
        res = cget("GET", res["url"])
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if (drive_link := HTML(res.text).xpath("//a[contains(@class,'btn')]/@href")) and (
        "drive.google.com" in drive_link[0]
        or "drive.usercontent.google.com" in drive_link[0]
    ):
        return drive_link[0]
    else:
        raise DirectDownloadLinkException(
            "ERROR: Drive Link not found, Try in your browser"
        )


def wetransfer(url):
    with create_scraper() as session:
        try:
            url = session.get(url).url
            splited_url = url.split("/")
            json_data = {"security_hash": splited_url[-1], "intent": "entire_transfer"}
            res = session.post(
                f"https://wetransfer.com/api/v4/transfers/{splited_url[-2]}/download",
                json=json_data,
            ).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if "direct_link" in res:
        return res["direct_link"]
    elif "message" in res:
        raise DirectDownloadLinkException(f"ERROR: {res['message']}")
    elif "error" in res:
        raise DirectDownloadLinkException(f"ERROR: {res['error']}")
    else:
        raise DirectDownloadLinkException("ERROR: cannot find direct link")


def akmfiles(url):
    with create_scraper() as session:
        try:
            html = HTML(
                session.post(
                    url,
                    data={"op": "download2", "id": url.split("/")[-1]},
                ).text
            )
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if direct_link := html.xpath("//a[contains(@class,'btn btn-dow')]/@href"):
        return direct_link[0]
    else:
        raise DirectDownloadLinkException("ERROR: Direct link not found")


def shrdsk(url):
    with create_scraper() as session:
        try:
            _json = session.get(
                f'https://us-central1-affiliate2apk.cloudfunctions.net/get_data?shortid={url.split("/")[-1]}',
            ).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        if "download_data" not in _json:
            raise DirectDownloadLinkException("ERROR: Download data not found")
        try:
            _res = session.get(
                f"https://shrdsk.me/download/{_json['download_data']}",
                allow_redirects=False,
            )
            if "Location" in _res.headers:
                return _res.headers["Location"]
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    raise DirectDownloadLinkException("ERROR: cannot find direct link in headers")


class LinkBoxHandler(FolderHandler):
    def __init__(self, url: str):
        super().__init__(url, Session())
        self.share_token = self._extract_share_token(url)
        self.details["contents"] = []
        self.details["title"] = ""
        self.details["total_size"] = 0

    def _extract_share_token(self, url):
        parsed_url = urlparse(url)
        try:
            return parsed_url.path.split("/")[-1]
        except Exception as e:
            raise DirectDownloadLinkException("ERROR: invalid URL") from e

    def _fetch_single_item(self, item_id):
        try:
            _json = self.session.get(
                "https://www.linkbox.to/api/file/detail",
                params={"itemId": item_id},
            ).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e

        data = _json["data"]
        if not data:
            if "msg" in _json:
                raise DirectDownloadLinkException(f"ERROR: {_json['msg']}")
            raise DirectDownloadLinkException("ERROR: data not found")

        item_info = data["itemInfo"]
        if not item_info:
            raise DirectDownloadLinkException("ERROR: itemInfo not found")

        filename = item_info["name"]
        sub_type = item_info.get("sub_type")
        if sub_type and not filename.strip().endswith(sub_type):
            filename += f".{sub_type}"
        if not self.details["title"]:
            self.details["title"] = filename

        item = {
            "path": "",
            "filename": filename,
            "url": item_info["url"],
        }
        if "size" in item_info:
            size = item_info["size"]
            if isinstance(size, str) and size.isdigit():
                size = float(size)
            self.details["total_size"] += size
        self.details["contents"].append(item)

    def _traverse_links(self, _id=0, folder_path=""):
        params = {
            "shareToken": self.share_token,
            "pageSize": 1000,
            "pid": _id,
        }
        try:
            _json = self.session.get(
                "https://www.linkbox.to/api/file/share_out_list",
                params=params,
            ).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e

        data = _json["data"]
        if not data:
            if "msg" in _json:
                raise DirectDownloadLinkException(f"ERROR: {_json['msg']}")
            raise DirectDownloadLinkException("ERROR: data not found")

        try:
            if data["shareType"] == "singleItem":
                self._fetch_single_item(data["itemId"])
                return
        except Exception:
            pass

        if not self.details["title"]:
            self.details["title"] = data["dirName"]

        contents = data["list"]
        if not contents:
            return

        for content in contents:
            if content["type"] == "dir" and "url" not in content:
                if not folder_path:
                    new_folder_path = ospath.join(self.details["title"], content["name"])
                else:
                    new_folder_path = ospath.join(folder_path, content["name"])
                if not self.details["title"]:
                    self.details["title"] = content["name"]
                self._traverse_links(content["id"], new_folder_path)
                continue

            if "url" in content:
                effective_folder_path = folder_path if folder_path else self.details["title"]
                filename = content["name"]
                if (
                    sub_type := content.get("sub_type")
                ) and not filename.strip().endswith(sub_type):
                    filename += f".{sub_type}"
                item = {
                    "path": ospath.join(effective_folder_path),
                    "filename": filename,
                    "url": content["url"],
                }
                if "size" in content:
                    size = content["size"]
                    if isinstance(size, str) and size.isdigit():
                        size = float(size)
                    self.details["total_size"] += size
                self.details["contents"].append(item)

    def handle(self):
        try:
            self._traverse_links()
            return self.details
        except DirectDownloadLinkException:
            raise
        finally:
            self.session.close()


def linkBox(url: str):
    return LinkBoxHandler(url).handle()


class GoFileHandler(TokenHandler):
    _shared_token_cache = {"token": "", "created_at": 0.0}
    _token_ttl_seconds = 3600

    def __init__(self, url: str):
        super().__init__(url, Session())
        self.original_url = url
        self.file_id, self._password = self._parse_url(url)
        self.details["contents"] = []
        self.details["title"] = ""
        self.details["total_size"] = 0

    def _parse_url(self, url):
        try:
            if "::" in url:
                _password = url.split("::")[-1]
                _password = sha256(_password.encode("utf-8")).hexdigest()
                url = url.split("::")[-2]
            else:
                _password = ""
            _id = url.split("/")[-1]
            return _id, _password
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e

    @classmethod
    def _get_cached_token(cls):
        token = cls._shared_token_cache.get("token", "")
        created_at = cls._shared_token_cache.get("created_at", 0.0)
        if not token:
            return ""
        if time.time() - created_at > cls._token_ttl_seconds:
            return ""
        return token

    @classmethod
    def _set_cached_token(cls, token):
        cls._shared_token_cache["token"] = token
        cls._shared_token_cache["created_at"] = time.time()

    def _fetch_token(self):
        headers = {
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "*/*",
            "Connection": "keep-alive",
        }
        _url = "https://api.gofile.io/accounts"
        res = self.session.post(_url, headers=headers).json()
        if res["status"] != "ok":
            raise DirectDownloadLinkException("ERROR: Failed to get token.")
        token = res["data"]["token"]
        self._set_cached_token(token)
        return token

    def _collect_contents(self, file_id, token, folder_path=""):
        _url = f"https://api.gofile.io/contents/{file_id}?cache=true"
        headers = {
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "*/*",
            "Connection": "keep-alive",
            "Authorization": "Bearer" + " " + token,
            "X-Website-Token": "4fd6sg89d7s6",
        }
        if self._password:
            _url += f"&password={self._password}"
        try:
            _json = self.session.get(_url, headers=headers).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e

        if _json["status"] in "error-passwordRequired":
            raise DirectDownloadLinkException(
                f"ERROR:\n{PASSWORD_ERROR_MESSAGE.format(self.original_url)}"
            )
        if _json["status"] in "error-passwordWrong":
            raise DirectDownloadLinkException("ERROR: This password is wrong !")
        if _json["status"] in "error-notFound":
            raise DirectDownloadLinkException("ERROR: File not found on gofile's server")
        if _json["status"] in "error-notPublic":
            raise DirectDownloadLinkException("ERROR: This folder is not public")

        data = _json["data"]
        if not self.details["title"]:
            self.details["title"] = data["name"] if data["type"] == "folder" else file_id

        for content in data["children"].values():
            if content["type"] == "folder":
                if not content["public"]:
                    continue
                if not folder_path:
                    new_folder_path = ospath.join(self.details["title"], content["name"])
                else:
                    new_folder_path = ospath.join(folder_path, content["name"])
                self._collect_contents(content["id"], token, new_folder_path)
                continue

            effective_folder_path = folder_path if folder_path else self.details["title"]
            item = {
                "path": ospath.join(effective_folder_path),
                "filename": content["name"],
                "url": content["link"],
            }
            if "size" in content:
                size = content["size"]
                if isinstance(size, str) and size.isdigit():
                    size = float(size)
                self.details["total_size"] += size
            self.details["contents"].append(item)

    def handle(self):
        try:
            token = self._get_cached_token() or self._fetch_token()
            self.details["header"] = f"Cookie: accountToken={token}"
            self._collect_contents(self.file_id, token)
        except DirectDownloadLinkException:
            raise
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        finally:
            self.session.close()

        if len(self.details["contents"]) == 1:
            return (self.details["contents"][0]["url"], self.details["header"])
        return self.details


def gofile(url):
    return GoFileHandler(url).handle()


class MediaFireFolderHandler(FolderHandler):
    def __init__(self, url: str):
        super().__init__(url)
        self.url, self._password = _extract_password(url)
        self.details.update({"header": ""})
        self.details["contents"] = []
        self.details["title"] = ""
        self.details["total_size"] = 0
        self.folder_infos = []

        session = create_scraper()
        adapter = HTTPAdapter(
            max_retries=Retry(total=10, read=10, connect=10, backoff_factor=0.3)
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        self.session = create_scraper(
            browser={"browser": "firefox", "platform": "windows", "mobile": False},
            delay=10,
            sess=session,
        )

    def _parse_folder_key(self):
        try:
            raw = self.url.split("/", 4)[-1]
            folderkey = raw.split("/", 1)[0]
            folderkey = folderkey.split(",")
        except Exception as e:
            raise DirectDownloadLinkException("ERROR: Could not parse ") from e
        if len(folderkey) == 1:
            return folderkey[0]
        return folderkey

    def _fetch_folder_info(self, folderkey):
        try:
            if isinstance(folderkey, list):
                folderkey = ",".join(folderkey)
            data = {
                "recursive": "yes",
                "folder_key": folderkey,
                "response_format": "json",
            }
            _json = self.session.post(
                "https://www.mediafire.com/api/1.5/folder/get_info.php",
                data=data,
            ).json()
        except Exception as e:
            raise DirectDownloadLinkException(
                f"ERROR: {e.__class__.__name__} While getting info"
            ) from e

        _res = _json["response"]
        if "folder_infos" in _res:
            self.folder_infos.extend(_res["folder_infos"])
        elif "folder_info" in _res:
            self.folder_infos.append(_res["folder_info"])
        elif "message" in _res:
            raise DirectDownloadLinkException(f"ERROR: {_res['message']}")
        else:
            raise DirectDownloadLinkException("ERROR: something went wrong!")

    def _decode_scrambled_url(self, html):
        enc_url = html.xpath('//a[@id="downloadButton"]')
        if not enc_url:
            return None

        final_link = enc_url[0].attrib.get("href")
        scrambled = enc_url[0].attrib.get("data-scrambled-url")
        if final_link and scrambled:
            try:
                return b64decode(scrambled).decode("utf-8")
            except Exception:
                return None
        if final_link and final_link.startswith("http"):
            return final_link
        if final_link and final_link.startswith("//"):
            return self._scrape_download_link(f"https:{final_link}")
        return None

    def _scrape_download_link(self, url):
        local_session = create_scraper()
        parsed_url = urlparse(url)
        clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        try:
            html = HTML(local_session.get(clean_url).text)
        except Exception:
            return None

        if html.xpath("//div[@class='passwordPrompt']"):
            if not self._password:
                raise DirectDownloadLinkException(
                    f"ERROR: {PASSWORD_ERROR_MESSAGE}".format(clean_url)
                )
            try:
                html = HTML(local_session.post(clean_url, data={"downloadp": self._password}).text)
            except Exception:
                return None
            if html.xpath("//div[@class='passwordPrompt']"):
                return None

        try:
            return self._decode_scrambled_url(html)
        except Exception:
            return None

    def _collect_folder_contents(self, folder_key, folder_path="", content_type="folders"):
        try:
            params = {
                "content_type": content_type,
                "folder_key": folder_key,
                "response_format": "json",
            }
            _json = self.session.get(
                "https://www.mediafire.com/api/1.5/folder/get_content.php",
                params=params,
            ).json()
        except Exception as e:
            raise DirectDownloadLinkException(
                f"ERROR: {e.__class__.__name__} While getting content"
            ) from e

        _res = _json["response"]
        if "message" in _res:
            raise DirectDownloadLinkException(f"ERROR: {_res['message']}")

        _folder_content = _res["folder_content"]
        if content_type == "folders":
            folders = _folder_content["folders"]
            for folder in folders:
                if folder_path:
                    new_folder_path = ospath.join(folder_path, folder["name"])
                else:
                    new_folder_path = ospath.join(folder["name"])
                self._collect_folder_contents(folder["folderkey"], new_folder_path)
            self._collect_folder_contents(folder_key, folder_path, "files")
            return

        files = _folder_content["files"]
        for file in files:
            file_url = self._scrape_download_link(file["links"]["normal_download"])
            if not file_url:
                continue
            item = {
                "filename": file["filename"],
                "path": ospath.join(folder_path if folder_path else self.details["title"]),
                "url": file_url,
            }
            if "size" in file:
                size = file["size"]
                if isinstance(size, str) and size.isdigit():
                    size = float(size)
                self.details["total_size"] += size
            self.details["contents"].append(item)

    def _format_response(self):
        if len(self.details["contents"]) == 1:
            return (self.details["contents"][0]["url"], [self.details["header"]])
        return self.details

    def handle(self):
        folderkey = self._parse_folder_key()
        try:
            self._fetch_folder_info(folderkey)
            self.details["title"] = self.folder_infos[0]["name"]
            for folder in self.folder_infos:
                self._collect_folder_contents(folder["folderkey"], folder["name"])
            return self._format_response()
        except DirectDownloadLinkException:
            raise
        except Exception as e:
            raise DirectDownloadLinkException(e) from e
        finally:
            self.session.close()


def mediafireFolder(url):
    return MediaFireFolderHandler(url).handle()


def pcloud(url):
    with create_scraper() as session:
        try:
            res = session.get(url)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if link := findall(r".downloadlink.:..(https:.*)..", res.text):
        return link[0].replace(r"\/", "/")
    raise DirectDownloadLinkException("ERROR: Direct link not found")


__all__ = [
    "terabox",
    "filepress",
    "sharer_scraper",
    "wetransfer",
    "akmfiles",
    "shrdsk",
    "linkBox",
    "gofile",
    "mediafireFolder",
    "pcloud",
]
