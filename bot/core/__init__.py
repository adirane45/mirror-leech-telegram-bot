"""
Bot Core Module
Centralized imports for core components
"""

from logging import getLogger
from config.main_config import Config

LOGGER = getLogger(__name__)

__all__ = ["LOGGER", "Config"]

