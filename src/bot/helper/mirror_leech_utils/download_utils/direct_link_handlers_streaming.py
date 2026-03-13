"""Streaming Handlers Module

Handles direct link generation for streaming video services:
- DoodStream (multiple domain variants)
- StreamTape (multiple domain variants)
- FileLions & StreamWish (multi-platform)
- StreamVid, StreamHub (quality variants)
"""

from re import findall, search
from time import sleep
from urllib.parse import urlparse

from cloudscraper import create_scraper
from lxml.etree import HTML
from requests import get

from ....core.config_manager import Config
from ...ext_utils.exceptions import DirectDownloadLinkException

user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
)


def streamtape(url):
    splitted_url = url.split("/")
    _id = splitted_url[4] if len(splitted_url) >= 6 else splitted_url[-1]
    try:
        html = HTML(get(url).text)
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    script = html.xpath(
        "//script[contains(text(),'ideoooolink')]/text()"
    ) or html.xpath("//script[contains(text(),'ideoolink')]/text()")
    if not script:
        raise DirectDownloadLinkException("ERROR: requeries script not found")
    if not (link := findall(r"(&expires\S+)'", script[0])):
        raise DirectDownloadLinkException("ERROR: Download link not found")
    return f"https://streamtape.com/get_video?id={_id}{link[-1]}"


def doods(url):
    if "/e/" in url:
        url = url.replace("/e/", "/d/")
    parsed_url = urlparse(url)
    with create_scraper() as session:
        try:
            html = HTML(session.get(url).text)
        except Exception as e:
            raise DirectDownloadLinkException(
                f"ERROR: {e.__class__.__name__} While fetching token link"
            ) from e
        if not (link := html.xpath("//div[@class='download-content']//a/@href")):
            raise DirectDownloadLinkException(
                "ERROR: Token Link not found or maybe not allow to download! open in browser."
            )
        link = f"{parsed_url.scheme}://{parsed_url.hostname}{link[0]}"
        sleep(2)
        try:
            _res = session.get(link)
        except Exception as e:
            raise DirectDownloadLinkException(
                f"ERROR: {e.__class__.__name__} While fetching download link"
            ) from e
    if not (link := search(r"window\.open\('(\S+)'", _res.text)):
        raise DirectDownloadLinkException("ERROR: Download link not found try again")
    return (link.group(1), [f"Referer: {parsed_url.scheme}://{parsed_url.hostname}/"])


def filelions_and_streamwish(url):
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    scheme = parsed_url.scheme
    
    apiKey, apiUrl = _get_api_config(hostname, scheme)
    file_code, quality = _parse_file_code(url)
    
    url = f"{scheme}://{hostname}/{file_code}"
    result = _fetch_file_info(apiUrl, apiKey, file_code)
    
    return _get_quality_url(result, quality)


def _get_api_config(hostname, scheme):
    if any(
        x in hostname
        for x in [
            "filelions.co",
            "filelions.live",
            "filelions.to",
            "filelions.site",
            "cabecabean.lol",
            "filelions.online",
            "mycloudz.cc",
        ]
    ):
        apiKey = Config.FILELION_API
        apiUrl = "https://vidhideapi.com"
    elif any(
        x in hostname
        for x in [
            "embedwish.com",
            "kissmovies.net",
            "kitabmarkaz.xyz",
            "wishfast.top",
            "streamwish.to",
        ]
    ):
        apiKey = Config.STREAMWISH_API
        apiUrl = "https://api.streamwish.com"
    else:
        apiKey = None
        apiUrl = None
    
    if not apiKey:
        raise DirectDownloadLinkException(
            f"ERROR: API is not provided get it from {scheme}://{hostname}"
        )
    return apiKey, apiUrl


def _parse_file_code(url):
    file_code = url.split("/")[-1]
    quality = ""
    if bool(file_code.strip().endswith(("_o", "_h", "_n", "_l"))):
        spited_file_code = file_code.rsplit("_", 1)
        quality = spited_file_code[1]
        file_code = spited_file_code[0]
    return file_code, quality


def _fetch_file_info(apiUrl, apiKey, file_code):
    try:
        _res = get(
            f"{apiUrl}/api/file/direct_link",
            params={"key": apiKey, "file_code": file_code, "hls": "1"},
        ).json()
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if _res["status"] != 200:
        raise DirectDownloadLinkException(f"ERROR: {_res['msg']}")
    return _res["result"]


def _get_quality_url(result, quality):
    if not result["versions"]:
        raise DirectDownloadLinkException("ERROR: File Not Found")
    error = "\nProvide a quality to download the video\nAvailable Quality:"
    for version in result["versions"]:
        if quality == version["name"]:
            return version["url"]
        elif version["name"] == "l":
            error += "\nLow"
            error += "\nNormal"
        elif version["name"] == "o":
            error += "\nOriginal"
        elif version["name"] == "h":
            error += "\nHD"
        error += f" <code>{url}_{version['name']}</code>"
    raise DirectDownloadLinkException(f"ERROR: {error}")


def streamvid(url: str):
    url = _parse_streamvid_url(url)
    with create_scraper() as session:
        try:
            html = HTML(session.get(url).text)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        quality_defined = bool(url.strip().endswith(("_o", "_h", "_n", "_l")))
        if quality_defined:
            return _streamvid_handle_with_quality(session, url, html)
        return _streamvid_handle_quality_options(html)


def _parse_streamvid_url(url: str) -> str:
    file_code = url.split("/")[-1]
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.hostname}/d/{file_code}"


def _streamvid_handle_with_quality(session, url: str, html):
    data = _streamvid_extract_form_data(html)
    try:
        html = HTML(session.post(url, data=data).text)
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    return _streamvid_extract_direct_link(html)


def _streamvid_extract_form_data(html):
    data = {}
    if not (inputs := html.xpath('//form[@id="F1"]//input')):
        raise DirectDownloadLinkException("ERROR: No inputs found")
    for i in inputs:
        if key := i.get("name"):
            data[key] = i.get("value")
    return data


def _streamvid_extract_direct_link(html):
    script = html.xpath('//script[contains(text(),"document.location.href")]/text()')
    if not script:
        if error := html.xpath('//div[@class="alert alert-danger"][1]/text()[2]'):
            raise DirectDownloadLinkException(f"ERROR: {error[0]}")
        raise DirectDownloadLinkException("ERROR: direct link script not found!")
    directLink = findall(r'document\.location\.href="(.*)"', script[0])
    if directLink:
        return directLink[0]
    raise DirectDownloadLinkException("ERROR: direct link not found! in the script")


def _streamvid_handle_quality_options(html):
    qualities_urls = html.xpath('//div[@id="dl_versions"]/a/@href')
    qualities = html.xpath('//div[@id="dl_versions"]/a/text()[2]')
    if qualities_urls and qualities:
        error = "\nProvide a quality to download the video\nAvailable Quality:"
        for quality_url, quality in zip(qualities_urls, qualities):
            error += f"\n{quality.strip()} <code>{quality_url}</code>"
        raise DirectDownloadLinkException(f"ERROR: {error}")
    error = html.xpath('//div[@class="not-found-text"]/text()')
    if error:
        raise DirectDownloadLinkException(f"ERROR: {error[0]}")
    raise DirectDownloadLinkException("ERROR: Something went wrong")


def streamhub(url):
    file_code = url.split("/")[-1]
    parsed_url = urlparse(url)
    url = f"{parsed_url.scheme}://{parsed_url.hostname}/d/{file_code}"
    with create_scraper() as session:
        try:
            html = HTML(session.get(url).text)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        if not (inputs := html.xpath('//form[@name="F1"]//input')):
            raise DirectDownloadLinkException("ERROR: No inputs found")
        data = {}
        for i in inputs:
            if key := i.get("name"):
                data[key] = i.get("value")
        session.headers.update({"referer": url})
        sleep(1)
        try:
            html = HTML(session.post(url, data=data).text)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        if directLink := html.xpath(
            '//a[@class="btn btn-primary btn-go downloadbtn"]/@href'
        ):
            return directLink[0]
        if error := html.xpath('//div[@class="alert alert-danger"]/text()[2]'):
            raise DirectDownloadLinkException(f"ERROR: {error[0]}")
        raise DirectDownloadLinkException("ERROR: direct link not found!")


__all__ = [
    "streamtape",
    "doods",
    "filelions_and_streamwish",
    "streamvid",
    "streamhub",
]
