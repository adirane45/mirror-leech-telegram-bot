"""
Direct Link Utilities
Common utilities and helper functions for all handlers
"""

from cloudscraper import create_scraper
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from lxml.etree import HTML
from json import loads, JSONDecodeError
from re import findall, search
from urllib.parse import parse_qs, urlparse, quote
from base64 import b64decode, b64encode
from functools import wraps
import time

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
        builder = APIRequestBuilder(session=session)
        if use_scraper:
            builder.use_scraper(True)

        method = method.lower()
        if method == "get":
            builder.get(url)
        elif method == "post":
            builder.post(url)
        elif method == "put":
            builder.put(url)
        elif method == "delete":
            builder.delete(url)
        else:
            raise ValueError(f"Unsupported method: {method}")

        if "headers" in kwargs and kwargs["headers"]:
            builder.with_headers(kwargs.pop("headers"))
        if "json" in kwargs and kwargs["json"] is not None:
            builder.with_json(kwargs.pop("json"))
        if "data" in kwargs and kwargs["data"] is not None:
            builder.with_data(kwargs.pop("data"))
        if "timeout" in kwargs and kwargs["timeout"] is not None:
            builder.timeout(kwargs.pop("timeout"))

        return builder.execute()
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


# ============================================================================
# Error Handling Decorators (Stage 1.2)
# ============================================================================

def handle_api_errors(func):
    """
    Decorator for consistent API error handling.
    
    Catches common API errors and converts them to DirectDownloadLinkException
    with clear, contextual error messages.
    
    Handles:
    - KeyError: Missing required field in response
    - ConnectionError: Network/connectivity issues
    - JSONDecodeError: Invalid JSON response
    - ValueError: Invalid values or parsing errors
    - TimeoutError: Request timeout
    
    Example:
        @handle_api_errors
        def fetch_data(self, url):
            response = self.session.get(url)
            return response.json()['data']
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError as e:
            # Missing required field in response
            field = str(e).strip("'\"")
            raise DirectDownloadLinkException(
                f"ERROR: Missing required API field: {field}"
            ) from e
        except ConnectionError as e:
            # Network connectivity issue
            raise DirectDownloadLinkException(
                f"ERROR: Connection failed - Network issue: {str(e)}"
            ) from e
        except JSONDecodeError as e:
            # Invalid JSON response
            raise DirectDownloadLinkException(
                f"ERROR: Invalid response format - Expected JSON: {str(e)}"
            ) from e
        except ValueError as e:
            # Invalid values or parsing errors
            raise DirectDownloadLinkException(
                f"ERROR: Invalid value - {str(e)}"
            ) from e
        except TimeoutError as e:
            # Request timeout
            raise DirectDownloadLinkException(
                f"ERROR: Request timeout - Server did not respond in time"
            ) from e
        except DirectDownloadLinkException:
            # Re-raise our custom exception as-is
            raise
        except Exception as e:
            # Catch unexpected exceptions
            raise DirectDownloadLinkException(
                f"ERROR: Unexpected error in {func.__name__}: {e.__class__.__name__}"
            ) from e
    
    return wrapper


def validate_response(*required_keys):
    """
    Decorator for API response validation.
    
    Ensures response contains all required keys and provides
    clear error messages if validation fails.
    
    Args:
        *required_keys: Variable number of key names that must exist in response
    
    Returns:
        Decorator function
    
    Example:
        @validate_response('status', 'data', 'token')
        def fetch_api_data(self, url):
            response = self.session.get(url)
            return response.json()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Validate if result is a dict (most common case)
            if isinstance(result, dict):
                missing_keys = [key for key in required_keys if key not in result]
                if missing_keys:
                    raise DirectDownloadLinkException(
                        f"ERROR: Response missing required fields: {', '.join(missing_keys)}"
                    )
            
            return result
        
        return wrapper
    
    return decorator


def with_retry(max_attempts: int = 3, backoff_factor: float = 2.0, backoff_max: float = 60.0):
    """
    Decorator for automatic retry with exponential backoff.
    
    Retries failed operations with exponential backoff strategy.
    Useful for transient failures like network timeouts or
    temporary service unavailability.
    
    Args:
        max_attempts: Maximum number of retry attempts (default 3)
        backoff_factor: Multiplier for backoff delay (default 2.0)
        backoff_max: Maximum backoff delay in seconds (default 60.0)
    
    Returns:
        Decorator function
    
    Example:
        @with_retry(max_attempts=3, backoff_factor=2.0)
        def fetch_with_retry(self, url):
            return self.session.get(url).json()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            last_exception = None
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, TimeoutError) as e:
                    # Only retry on transient network errors
                    last_exception = e
                    attempt += 1
                    
                    if attempt >= max_attempts:
                        # Max attempts reached, raise the error
                        raise DirectDownloadLinkException(
                            f"ERROR: Failed after {max_attempts} attempts: {str(e)}"
                        ) from e
                    
                    # Calculate backoff delay with exponential strategy
                    delay = min(
                        (backoff_factor ** (attempt - 1)),
                        backoff_max
                    )
                    
                    # No logging here - let caller handle if needed
                    time.sleep(delay)
                except DirectDownloadLinkException:
                    # Don't retry on our custom exceptions
                    raise
            
            # Should not reach here, but handle just in case
            if last_exception:
                raise DirectDownloadLinkException(
                    f"ERROR: Retry exhausted: {str(last_exception)}"
                ) from last_exception
        
        return wrapper
    
    return decorator


class APIRequestBuilder:
    """
    Fluent interface for building and executing API requests.
    
    Replaces the need for _make_api_request() function with multiple parameters.
    Provides clear, chainable API for constructing requests.
    
    Example:
        builder = APIRequestBuilder(session)
        response = (builder
            .get("https://api.example.com/data")
            .with_headers({"Authorization": "Bearer token"})
            .timeout(30)
            .retries(3)
            .execute())
        
        data = response.json()
    """
    
    def __init__(self, session=None):
        """
        Initialize request builder.
        
        Args:
            session: Optional requests.Session object (creates new if not provided)
        """
        self.session = session or create_session_with_retries()
        self._method = "GET"
        self._url = None
        self._headers = {}
        self._data = None
        self._json = None
        self._timeout = 30
        self._retries = 1
        self._use_scraper = False
    
    def get(self, url: str) -> "APIRequestBuilder":
        """Set HTTP GET method and URL"""
        self._method = "GET"
        self._url = url
        return self
    
    def post(self, url: str) -> "APIRequestBuilder":
        """Set HTTP POST method and URL"""
        self._method = "POST"
        self._url = url
        return self
    
    def put(self, url: str) -> "APIRequestBuilder":
        """Set HTTP PUT method and URL"""
        self._method = "PUT"
        self._url = url
        return self
    
    def delete(self, url: str) -> "APIRequestBuilder":
        """Set HTTP DELETE method and URL"""
        self._method = "DELETE"
        self._url = url
        return self
    
    def with_headers(self, headers: dict) -> "APIRequestBuilder":
        """Add/merge headers to request"""
        self._headers.update(headers)
        return self
    
    def with_auth(self, token: str, auth_type: str = "Bearer") -> "APIRequestBuilder":
        """Add Authorization header"""
        self._headers["Authorization"] = f"{auth_type} {token}"
        return self
    
    def with_json(self, data: dict) -> "APIRequestBuilder":
        """Set JSON data for request body"""
        self._json = data
        self._headers["Content-Type"] = "application/json"
        return self
    
    def with_data(self, data: dict) -> "APIRequestBuilder":
        """Set form data for request body"""
        self._data = data
        return self
    
    def with_form(self, data: dict) -> "APIRequestBuilder":
        """Set form-encoded data (alias for with_data)"""
        return self.with_data(data)
    
    def timeout(self, seconds: float) -> "APIRequestBuilder":
        """Set request timeout in seconds"""
        self._timeout = seconds
        return self
    
    def retries(self, count: int) -> "APIRequestBuilder":
        """Set number of retry attempts"""
        self._retries = max(1, count)
        return self
    
    def use_scraper(self, enabled: bool = True) -> "APIRequestBuilder":
        """Enable/disable scraper for requests"""
        self._use_scraper = enabled
        return self
    
    @handle_api_errors
    def execute(self):
        """
        Execute the configured request with error handling.
        
        Returns:
            requests.Response: Response object (use .json() or .text)
        
        Raises:
            DirectDownloadLinkException: On connection or response errors
        """
        if not self._url:
            raise DirectDownloadLinkException("ERROR: URL not set - use .get() or .post()")
        
        # Use scraper if requested
        session = (
            create_scraper() if self._use_scraper 
            else self.session
        )
        
        # Prepare request kwargs
        request_kwargs = {
            "timeout": self._timeout,
            "headers": self._headers
        }
        
        if self._json:
            request_kwargs["json"] = self._json
        elif self._data:
            request_kwargs["data"] = self._data
        
        # Execute request with retry logic
        @with_retry(max_attempts=self._retries)
        def _make_request():
            method = self._method.lower()
            if method == "get":
                return session.get(self._url, **request_kwargs)
            elif method == "post":
                return session.post(self._url, **request_kwargs)
            elif method == "put":
                return session.put(self._url, **request_kwargs)
            elif method == "delete":
                return session.delete(self._url, **request_kwargs)
            else:
                raise DirectDownloadLinkException(
                    f"ERROR: Unsupported HTTP method: {self._method}"
                )
        
        return _make_request()


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
    # Stage 1.2 decorators and builders
    "handle_api_errors",
    "validate_response",
    "with_retry",
    "APIRequestBuilder",
]
