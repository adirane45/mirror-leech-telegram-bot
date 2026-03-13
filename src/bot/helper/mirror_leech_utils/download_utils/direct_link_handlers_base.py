"""
Direct Link Handler Base Classes and Utilities
Provides common functionality for all download handlers
"""

from urllib.parse import urlparse

from cloudscraper import create_scraper
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ...ext_utils.exceptions import DirectDownloadLinkException
from .direct_link_utils import make_api_request as utils_make_api_request


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
        return utils_make_api_request(session, method, url, use_scraper, **kwargs)

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


class NestedHandler(BaseHandler):
    """
    Base class for handlers with nested logic (callbacks, nested functions).

    Provides:
    - Centralized error handling across nested operations
    - State management via `details` dict
    - Response validation utilities
    - Logging support for nested operations

    Use this for handlers with multiple nested helper functions
    that share state and error handling logic.

    Example:
        class MyHandler(NestedHandler):
            def handle(self):
                self._fetch_data()
                self._process_data()
                return self._format_response()

            def _fetch_data(self):
                try:
                    # nested operation
                except Exception as e:
                    self._handle_error(e)
    """

    def __init__(self, url: str = None, session=None):
        if url:
            super().__init__(url)
        self.session = session or self.create_session_with_retries()
        # Shared state for nested functions
        self.details = {
            "contents": [],
            "title": "",
            "total_size": 0,
            "file_count": 0,
            "folder_count": 0
        }
        self._errors = []

    def _validate_response(self, response, required_key: str = None, error_key: str = "message") -> dict:
        """
        Validate API response with centralized error handling.

        Args:
            response: Response object or dict to validate
            required_key: Key that must exist in response
            error_key: Key that indicates error message

        Returns:
            dict: Validated response data

        Raises:
            DirectDownloadLinkException: If validation fails
        """
        try:
            # Check if response is a requests Response object
            if hasattr(response, 'json'):
                data = response.json()
            elif isinstance(response, dict):
                data = response
            else:
                raise DirectDownloadLinkException("Invalid response format")

            # Check required key
            if required_key and required_key not in data:
                raise DirectDownloadLinkException(
                    f"Missing required field: {required_key}"
                )

            # Check for error indicator
            if error_key in data and data[error_key]:
                raise DirectDownloadLinkException(
                    f"API Error: {data[error_key]}"
                )

            return data
        except DirectDownloadLinkException:
            raise
        except Exception as e:
            raise DirectDownloadLinkException(
                f"Response validation failed: {e.__class__.__name__}: {str(e)}"
            ) from e

    def _handle_error(self, error: Exception, context: str = "") -> None:
        """
        Centralized error handling for nested operations.

        Args:
            error: Exception that occurred
            context: Context about where the error occurred
        """
        error_msg = f"{context}: {str(error)}" if context else str(error)
        self._errors.append({
            "type": error.__class__.__name__,
            "message": error_msg,
            "context": context
        })

        # Log the error for debugging but don't immediately re-raise
        # This allows partial results to be collected in multi-item operations

    def _get_errors(self) -> list:
        """Get list of accumulated errors"""
        return self._errors

    def _clear_errors(self) -> None:
        """Clear accumulated errors"""
        self._errors = []

    def _has_errors(self) -> bool:
        """Check if any errors occurred"""
        return len(self._errors) > 0


class FolderHandler(NestedHandler):
    """
    Base class for handlers that perform recursive folder traversal.

    Provides:
    - Template method pattern for folder traversal
    - Size aggregation logic
    - Depth tracking to prevent infinite recursion
    - Path building utilities

    Use this for handlers that need to:
    - Recursively fetch folder contents
    - Aggregate file sizes and counts
    - Track folder hierarchy

    Example:
        class MyFolderHandler(FolderHandler):
            def handle(self, folder_id):
                self._traverse(folder_id)
                return self._format_response()

            def _traverse(self, folder_id, path=""):
                items = self._fetch_items(folder_id)
                for item in items:
                    if item['is_folder']:
                        self._traverse(item['id'], path + "/" + item['name'])
                    else:
                        self._collect_file(item, path)
    """

    MAX_DEPTH = 50  # Prevent infinite recursion

    def __init__(self, url: str = None, session=None):
        super().__init__(url, session)
        self._traversal_depth = 0
        self._visited_ids = set()  # Track visited to prevent loops

    def _traverse(self, identifier, path: str = "", depth: int = 0) -> None:
        """
        Template method for folder traversal with safety checks.

        Args:
            identifier: Folder/item ID to traverse
            path: Current path in hierarchy
            depth: Current recursion depth

        Raises:
            DirectDownloadLinkException: If depth exceeds MAX_DEPTH
        """
        if depth > self.MAX_DEPTH:
            raise DirectDownloadLinkException(
                f"Maximum folder depth ({self.MAX_DEPTH}) exceeded - possible circular reference"
            )

        if identifier in self._visited_ids:
            # Already visited this folder, skip to prevent infinite loops
            return

        self._visited_ids.add(identifier)
        self._traversal_depth = max(self._traversal_depth, depth)

    def _add_file(self, item_data: dict, folder_path: str = "") -> None:
        """
        Add file to details contents with aggregation.

        Args:
            item_data: File information dict (must have 'name', 'url', 'size')
            folder_path: Path to file in folder hierarchy
        """
        try:
            # Aggregate metrics
            size = item_data.get('size', 0)
            self.details['total_size'] += size
            self.details['file_count'] += 1

            # Build full path
            full_path = f"{folder_path}/{item_data['name']}" if folder_path else item_data['name']

            # Add to contents
            self.details['contents'].append({
                'name': item_data['name'],
                'url': item_data.get('url', ''),
                'size': size,
                'path': full_path,
                'type': 'file'
            })
        except KeyError as e:
            self._handle_error(KeyError(f"Missing field in item: {e}"), "add_file")

    def _add_folder(self, folder_name: str, folder_path: str = "") -> None:
        """
        Track folder addition with aggregation.

        Args:
            folder_name: Name of the folder
            folder_path: Path to folder in hierarchy
        """
        self.details['folder_count'] += 1

    def _size_to_bytes(self, size_str: str) -> int:
        """
        Convert size string to bytes.

        Args:
            size_str: Size string (e.g., "1.5 GB", "512 MB")

        Returns:
            int: Size in bytes
        """
        try:
            if not size_str:
                return 0

            size_str = size_str.strip().upper()
            multipliers = {
                'B': 1,
                'KB': 1024,
                'MB': 1024 ** 2,
                'GB': 1024 ** 3,
                'TB': 1024 ** 4
            }

            for unit, multiplier in multipliers.items():
                if unit in size_str:
                    value = float(size_str.replace(unit, '').strip())
                    return int(value * multiplier)

            # Try to parse as plain number
            return int(float(size_str))
        except (ValueError, AttributeError):
            return 0


class TokenHandler(NestedHandler):
    """
    Base class for handlers with token/auth management and caching.

    Provides:
    - Token caching to reduce API calls
    - Token lifecycle management (fetch, cache, validate)
    - Session management
    - Automatic cache invalidation

    Use this for handlers that require:
    - Authentication tokens (session tokens, API keys)
    - Token caching to prevent redundant API calls
    - Multiple operations with same token

    Example:
        class MyTokenHandler(TokenHandler):
            def handle(self, url):
                token = self.get_or_create_token("api_token", self._fetch_token)
                data = self._fetch_data(token)
                return self._format_response()

            def _fetch_token(self):
                response = self.session.post(...)
                return response.json()['token']
    """

    def __init__(self, url: str = None, session=None):
        super().__init__(url, session)
        self._token_cache = {}  # Cache for tokens
        self._token_metadata = {}  # Track token creation time, expiry

    def get_or_create_token(self, cache_key: str, token_func, force_refresh: bool = False) -> str:
        """
        Get cached token or create new one.

        Args:
            cache_key: Key for caching this token
            token_func: Callable that returns token string
            force_refresh: Bypass cache and force new token creation

        Returns:
            str: Token string

        Raises:
            DirectDownloadLinkException: If token generation fails
        """
        # Return cached token if available and not forcing refresh
        if not force_refresh and cache_key in self._token_cache:
            cached_token = self._token_cache[cache_key]
            metadata = self._token_metadata.get(cache_key, {})

            # Check if token is still valid (simple check)
            if cached_token and not self._is_token_expired(metadata):
                return cached_token

        # Generate new token
        try:
            new_token = token_func()
            if not new_token:
                raise DirectDownloadLinkException("Token generation returned empty value")

            # Cache the token
            self._token_cache[cache_key] = new_token
            self._token_metadata[cache_key] = {
                'created_at': __import__('time').time(),
                'call_count': 0
            }

            return new_token
        except DirectDownloadLinkException:
            raise
        except Exception as e:
            raise DirectDownloadLinkException(
                f"Token generation failed: {e.__class__.__name__}"
            ) from e

    def _is_token_expired(self, metadata: dict, ttl_seconds: int = 3600) -> bool:
        """
        Check if token is expired.

        Args:
            metadata: Token metadata dict with 'created_at'
            ttl_seconds: Time-to-live for token (default 1 hour)

        Returns:
            bool: True if expired, False if still valid
        """
        if not metadata or 'created_at' not in metadata:
            return True

        import time
        age = time.time() - metadata['created_at']
        return age > ttl_seconds

    def _invalidate_token(self, cache_key: str) -> None:
        """
        Manually invalidate cached token.

        Args:
            cache_key: Key of token to invalidate
        """
        if cache_key in self._token_cache:
            del self._token_cache[cache_key]
        if cache_key in self._token_metadata:
            del self._token_metadata[cache_key]

    def _clear_all_tokens(self) -> None:
        """Clear all cached tokens"""
        self._token_cache.clear()
        self._token_metadata.clear()

    def _get_cache_stats(self) -> dict:
        """
        Get token cache statistics.

        Returns:
            dict: Cache hit counts, cache size, etc.
        """
        return {
            'cached_tokens': len(self._token_cache),
            'cache_keys': list(self._token_cache.keys())
        }


class DeprecatedHandler(BaseHandler):
    """Handler for deprecated/removed services"""

    def handle(self) -> str:
        """Raise informative error for deprecated service"""
        raise DirectDownloadLinkException(f"ERROR: R.I.P {self.domain}")
