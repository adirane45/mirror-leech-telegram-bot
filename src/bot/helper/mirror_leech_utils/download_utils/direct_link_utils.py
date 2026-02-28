"""
Direct Link Utilities
Common utilities and helper functions for all handlers
"""

from cloudscraper import create_scraper
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from lxml.etree import HTML
from json import loads
from re import findall, search
from urllib.parse import parse_qs, urlparse, quote
from base64 import b64decode, b64encode

from ...ext_utils.exceptions import DirectDownloadLinkException


user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
)


def create_session_with_retries(max_retries=10):
    """Create session with retry logic"""
    session = create_scraper()
    adapter = HTTPAdapter(
        max_retries=Retry(
            total=max_retries,
            read=max_retries,
            connect=max_retries,
            backoff_factor=0.3
        )
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def extract_password(url: str, separator: str = "::") -> tuple:
    """Extract and remove password from URL if present (guard clause style)"""
    if separator not in url:
        return url, ""
    
    parts = url.split(separator)
    if len(parts) != 2:
        return url, ""
    
    return parts[0], parts[1]


def validate_json_response(json_data, error_key="message", ok_status="ok") -> bool:
    """Validate API response with guard clauses"""
    if isinstance(json_data, dict):
        if "status" in json_data and json_data["status"] != ok_status:
            raise DirectDownloadLinkException(
                f"ERROR: API returned status {json_data['status']}"
            )
        if error_key in json_data:
            raise DirectDownloadLinkException(
                f"ERROR: {json_data[error_key]}"
            )
    return True


def make_api_request(session, method: str, url: str, use_scraper=False, **kwargs):
    """Make API request with unified error handling"""
    try:
        if use_scraper:
            session = create_scraper()
        
        if method.lower() == "get":
            response = session.get(url, **kwargs)
        elif method.lower() == "post":
            response = session.post(url, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response
    except Exception as e:
        raise DirectDownloadLinkException(
            f"ERROR: {e.__class__.__name__}"
        ) from e


def parse_url_component(url: str, separator: str, index: int) -> str:
    """Extract URL component safely with error handling"""
    try:
        return url.split(separator)[index]
    except (IndexError, AttributeError) as e:
        raise DirectDownloadLinkException(
            f"ERROR: Invalid URL format - {e.__class__.__name__}"
        ) from e


def get_captcha_token(session, params):
    """Get reCAPTCHA token"""
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


def cf_bypass_helper(url):
    """Cloudflare bypass helper for scraper"""
    return url


# Re-exports for backward compatibility
__all__ = [
    "user_agent",
    "create_session_with_retries",
    "extract_password",
    "validate_json_response",
    "make_api_request",
    "parse_url_component",
    "get_captcha_token",
    "cf_bypass_helper",
]
