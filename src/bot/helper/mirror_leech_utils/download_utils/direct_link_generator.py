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


class HandlerDispatcher:
    def __init__(self, registry):
        self.registry = registry

    def _validate_url(self, link: str) -> str:
        if not link or not isinstance(link, str):
            raise DirectDownloadLinkException("ERROR: Invalid URL")
        clean_link = link.strip()
        parsed = urlparse(clean_link)
        if not parsed.hostname:
            raise DirectDownloadLinkException("ERROR: Invalid URL")
        return clean_link

    def _resolve_handler(self, link: str):
        handler_name = self.registry.get_handler_name(link)
        handler = globals().get(handler_name)
        if not callable(handler):
            raise DirectDownloadLinkException(
                f"No Direct link function found for {link}"
            )
        return handler

    def _execute_handler(self, handler, link: str):
        try:
            return handler(link)
        except DirectDownloadLinkException:
            raise
        except Exception as e:
            raise DirectDownloadLinkException(
                f"ERROR: {e.__class__.__name__}"
            ) from e

    def execute(self, link: str):
        clean_link = self._validate_url(link)
        handler = self._resolve_handler(clean_link)
        return self._execute_handler(handler, clean_link)


def direct_link_generator(link: str) -> str:
    """
    Generate direct download link using Strategy Pattern.

    Backward-compatible wrapper around HandlerDispatcher.
    """
    return HandlerDispatcher(HandlerRegistry).execute(link)


# Export primary entry point
__all__ = ["direct_link_generator"]
