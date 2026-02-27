"""
Core settings management - Handles user preference retrieval and validation
Cohesive module: Single responsibility for getting and validating settings
"""

from typing import Any, Dict, Optional
from aiofiles.os import path as aiopath

from .. import user_data
from ..core.config_manager import Config
from ..core.telegram_manager import TgClient


class SettingsRetriever:
    """Retrieve user settings with fallback to global config"""

    @staticmethod
    def get_setting(
        user_id: int,
        setting_key: str,
        default: Optional[Any] = None,
        fallback_to_config: bool = True,
    ) -> Any:
        """
        Get a setting from user data or config with fallback.

        Args:
            user_id: User ID
            setting_key: Setting key name
            default: Default value if not found
            fallback_to_config: Whether to fall back to Config

        Returns:
            Setting value or default
        """
        user_dict = user_data.get(user_id, {})

        # Try user data first
        if setting_key in user_dict and user_dict[setting_key]:
            return user_dict[setting_key]

        # Fall back to Config if enabled
        if fallback_to_config:
            config_value = getattr(Config, setting_key, None)
            if config_value:
                return config_value

        return default

    @staticmethod
    def get_bool_setting(
        user_id: int, setting_key: str, premium_only: bool = False
    ) -> bool:
        """Get boolean setting with premium check."""
        if premium_only and not TgClient.IS_PREMIUM_USER:
            return False
        return SettingsRetriever.get_setting(user_id, setting_key, False)

    @staticmethod
    async def file_exists(filepath: str) -> bool:
        """Check if file exists."""
        return await aiopath.exists(filepath)

    @staticmethod
    def format_size(value: Any) -> str:
        """Format value as size string."""
        return str(value) if value else "None"

    @staticmethod
    def format_status(exists: bool) -> str:
        """Format existence status."""
        return "Exists" if exists else "Not Exists"
