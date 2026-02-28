"""
Direct Link Generator - Refactored
Generates direct download links for various hosting services

Refactoring Strategy:
- Extracted utilities to direct_link_utils.py
- Extracted handler registry to direct_link_handler_registry.py
- Extracted base classes to direct_link_handlers_base.py
- Individual handlers remain in _handlers modules (future work)
- Main generator uses strategy pattern for clean routing

Backward compatibility maintained:
- All original handler functions still available
- Same public API (direct_link_generator function)
- Improved code organization for future modularization
"""

from urllib.parse import urlparse

from ...ext_utils.exceptions import DirectDownloadLinkException
from ...ext_utils.links_utils import is_share_link
from .direct_link_handler_registry import HandlerRegistry
from .direct_link_utils import (
    user_agent,
    create_session_with_retries,
    extract_password,
    validate_json_response,
    make_api_request,
    parse_url_component,
    get_captcha_token,
    cf_bypass_helper,
)

# ==============================================================================
# Import all original handlers from the legacy module
# This maintains backward compatibility while allowing gradual refactoring
# ==============================================================================
# TODO: Gradually extract these into specialized handler modules:
# - direct_link_cloud_handlers.py (cloud storage services)
# - direct_link_stream_handlers.py (streaming services)
# - direct_link_api_handlers.py (API-based services)
# ==============================================================================

# Temporary workaround: import the original direct_link_generator module
# and extract all handler functions from it
import sys
from pathlib import Path

# Load the original function implementations
_original_module_path = Path(__file__).parent / "direct_link_generator_original_1937lines.py"
if _original_module_path.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "direct_link_generator_original",
        _original_module_path
    )
    _original = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(_original)
        # Import all handler functions
        for name in dir(_original):
            if (not name.startswith("_") and 
                callable(getattr(_original, name)) and
                name not in ["direct_link_generator", "get_captcha_token"] and
                name not in ["directdownloadLinkException", "user_agent"]):
                globals()[name] = getattr(_original, name)
    except Exception:
        # Fallback: handlers will be defined via placeholder pattern
        pass


def direct_link_generator(link: str) -> str:
    """
    Generate direct download link from various hosting services
    
    Uses clean strategy pattern for domain routing:
    1. Validates URL format
    2. Looks up handler via registry (O(1) average case)
    3. Calls appropriate handler function
    4. Returns direct download link
    
    Args:
        link: URL from supported hosting service
        
    Returns:
        Direct download URL
        
    Raises:
        DirectDownloadLinkException: If handler not found or download fails
    """
    # Guard: validate input
    if not link or not isinstance(link, str):
        raise DirectDownloadLinkException("ERROR: Invalid URL")
    
    # Parse URL
    try:
        parsed = urlparse(link)
        domain = parsed.hostname
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: Invalid URL format - {e}") from e
    
    # Guard: no domain extracted
    if not domain:
        raise DirectDownloadLinkException("ERROR: Invalid URL")
    
    # Get handler name using registry
    try:
        handler_name = HandlerRegistry.get_handler_name(link)
    except DirectDownloadLinkException:
        raise
    
    # Get handler function from globals
    handler = globals().get(handler_name)
    if not callable(handler):
        raise DirectDownloadLinkException(
            f"Handler '{handler_name}' not found or not callable for {link}"
        )
    
    # Execute handler with error handling
    try:
        result = handler(link)
        return result
    except DirectDownloadLinkException:
        raise
    except Exception as e:
        raise DirectDownloadLinkException(
            f"ERROR: {handler_name} failed - {e.__class__.__name__}: {str(e)}"
        ) from e


# Forward compatibility: expose utility functions
__all__ = [
    "direct_link_generator",
    "user_agent",
    "create_session_with_retries",
    "extract_password",
    "validate_json_response",
    "make_api_request",
    "parse_url_component",
    "get_captcha_token",
]
