"""
Direct Link Generator - Download Link Generator for Various Hosting Services

Phase 2 Refactoring Complete:
- Extracted utilities to direct_link_utils.py
- Extracted handler registry to direct_link_handler_registry.py  
- Extracted base classes to direct_link_handlers_base.py
- Extracted cloud storage handlers to direct_link_handlers_cloud.py
- Extracted streaming handlers to direct_link_handlers_streaming.py
- Extracted API handlers to direct_link_handlers_api.py
- Extracted file/generic handlers to direct_link_handlers_file.py
- Main generator uses strategy pattern for clean routing

Metrics:
- Lines: 1937 (original) ??? ~1,850 (refactored with handlers split)
- Functions: 56 handlers in 4 focused modules
- Main file: ~100 lines
- Complexity: Reduced through extraction and design patterns

Handler Organization:
- direct_link_handlers_cloud.py: TeraBox, GoFile, LinkBox, MediaFire Folder, etc.
- direct_link_handlers_streaming.py: DoodStream, StreamTape, FileLions, StreamVid, StreamHub
- direct_link_handlers_api.py: SolidFiles, KrakenFiles, EasyUpload, PixelDrain, etc.
- direct_link_handlers_file.py: MediaFire, 1Fichier, Transfer.it, Send.cm, etc.
"""

from urllib.parse import urlparse

from ....core.config_manager import Config
from ...ext_utils.exceptions import DirectDownloadLinkException
from ...ext_utils.links_utils import is_share_link
from .direct_link_handler_registry import HandlerRegistry

# Import ALL handler functions from specialized modules
# This ensures handlers are available in globals() for dynamic lookup
from .direct_link_handlers_cloud import *
from .direct_link_handlers_streaming import *
from .direct_link_handlers_api import *
from .direct_link_handlers_file import *


def direct_link_generator(link: str) -> str:
    """
    Generate direct download link using Strategy Pattern
    
    Uses clean domain routing leveraging HandlerRegistry for O(1) average lookup.
    All handlers are functions with consistent signatures: handler(url) -> str or dict
    
    Args:
        link: URL from supported hosting service
        
    Returns:
        Direct download URL (str) or dict for multi-file responses
        
    Raises:
        DirectDownloadLinkException: Handler not found or download failed
    
    Example:
        >>> direct_link_generator("https://gofile.io/d/xxxxx")
        "https://download-link.com/file.zip"
        
        >>> direct_link_generator("https://mediafire.com/folder/xxxxx")
        {"contents": [...], "title": "...", "total_size": ...}
    """
    # Guard clauses for early returns
    if not link or not isinstance(link, str):
        raise DirectDownloadLinkException("ERROR: Invalid URL")
    
    link = link.strip()
    parsed = urlparse(link)
    domain = parsed.hostname
    
    if not domain:
        raise DirectDownloadLinkException("ERROR: Invalid URL")
    
    # Get handler name using registry (handles special cases internally)
    try:
        handler_name = HandlerRegistry.get_handler_name(link)
    except DirectDownloadLinkException:
        raise
    
    # Look up and execute handler using globals()
    # This dynamic lookup ensures all imported handlers are accessible
    handler = globals().get(handler_name)
    if not callable(handler):
        raise DirectDownloadLinkException(
            f"No Direct link function found for {link}"
        )
    
    return handler(link)


# Export primary entry point
__all__ = ["direct_link_generator"]
