"""
Direct Link Handler Base Classes and Utilities
Provides common functionality for all download handlers
"""

from cloudscraper import create_scraper
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlparse
import re

from ...ext_utils.exceptions import DirectDownloadLinkException
from ...ext_utils.links_utils import is_share_link


class BaseHandler:
    """Base class for all download handlers"""
    
    # Domain mappings should be defined in subclasses
    DOMAINS = []  # Override in subclass
    
    def __init__(self, url: str):
        self.url = url
        self.parsed = urlparse(url)
        self.domain = self.parsed.hostname or ""
    
    def handle(self) -> str:
        """Main method to generate direct link - override in subclass"""
        raise NotImplementedError(
            f"Handler for {self.domain} must implement handle() method"
        )
    
    @staticmethod
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
    
    @staticmethod
    def extract_password(url: str, separator: str = "::") -> tuple:
        """Extract and remove password from URL if present"""
        if separator not in url:
            return url, ""
        
        parts = url.split(separator)
        if len(parts) != 2:
            return url, ""
        
        return parts[0], parts[1]
    
    @staticmethod
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
    
    @staticmethod
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
    
    @staticmethod
    def parse_url_component(url: str, separator: str, index: int) -> str:
        """Extract URL component safely with error handling"""
        try:
            return url.split(separator)[index]
        except (IndexError, AttributeError) as e:
            raise DirectDownloadLinkException(
                f"ERROR: Invalid URL format - {e.__class__.__name__}"
            ) from e


class APIHandler(BaseHandler):
    """Handler for API-based download services"""
    
    def make_request(self, method: str, url: str, use_scraper=False, **kwargs):
        """Convenience method for making API requests"""
        return self.make_api_request(Session(), method, url, use_scraper, **kwargs)


class ScraperHandler(BaseHandler):
    """Handler for services requiring web scraping"""
    
    def __init__(self, url: str):
        super().__init__(url)
        self.session = self.create_session_with_retries()


class DeprecatedHandler(BaseHandler):
    """Handler for deprecated/removed services"""
    
    def handle(self) -> str:
        """Raise informative error for deprecated service"""
        raise DirectDownloadLinkException(f"ERROR: R.I.P {self.domain}")
