# Download Templates Module
# Create presets for common download types
# Reduces manual configuration
# Modified by: justadi

from typing import Optional, Dict
from datetime import datetime
from asyncio import Lock

from .. import LOGGER


class DownloadTemplate:
    """Represents a download template/preset"""
    
    def __init__(self, name: str, description: str = "", **settings):
        self.name = name
        self.description = description
        self.settings = settings
        self.created_at = datetime.now()
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "settings": self.settings,
            "created_at": self.created_at.isoformat()
        }


class TemplateManager:
    """
    Manages download templates and presets
    """
    
    # Default templates
    DEFAULT_TEMPLATES = {
        "movie_mirror": DownloadTemplate(
            "Movie Mirror",
            "Optimized settings for mirroring movies",
            tool="aria2",
            max_connections=16,
            max_split=5,
            category="movies",
            notify_completion=True
        ),
        "document_leech": DownloadTemplate(
            "Document Leech",
            "Quick settings for leaching documents",
            tool="direct",
            priority="high",
            category="documents",
            compress=False,
            notify_completion=True
        ),
        "software_mirror": DownloadTemplate(
            "Software Mirror",
            "Settings for software/application mirroring",
            tool="qbittorrent",
            category="software",
            max_ratio=2.0,
            notify_completion=True
        ),
        "backup_mirror": DownloadTemplate(
            "Backup Mirror",
            "Settings for backup file handling",
            tool="aria2",
            max_split=3,
            category="backups",
            verify_integrity=True,
            notify_completion=True
        ),
    }
    
    templates: Dict[str, DownloadTemplate] = DEFAULT_TEMPLATES.copy()
    _lock = Lock()
    
    @classmethod
    async def create_template(
        cls,
        name: str,
        description: str = "",
        **settings
    ) -> bool:
        """
        Create a new download template
        
        Args:
            name: Template name
            description: Template description
            **settings: Template settings/configuration
            
        Returns:
            True if created successfully
        """
        try:
            template_id = name.lower().replace(" ", "_")
            
            async with cls._lock:
                if template_id in cls.templates:
                    LOGGER.warning(f"Template '{name}' already exists")
                    return False
                
                cls.templates[template_id] = DownloadTemplate(name, description, **settings)
                LOGGER.info(f"Template '{name}' created")
            return True
        except Exception as e:
            LOGGER.error(f"Error creating template: {e}")
            return False
    
    @classmethod
    async def delete_template(cls, name: str) -> bool:
        """Delete a template"""
        try:
            template_id = name.lower().replace(" ", "_")
            
            async with cls._lock:
                if template_id not in cls.templates or template_id in cls.DEFAULT_TEMPLATES:
                    LOGGER.warning(f"Cannot delete default template '{name}'")
                    return False
                
                del cls.templates[template_id]
                LOGGER.info(f"Template '{name}' deleted")
            return True
        except Exception as e:
            LOGGER.error(f"Error deleting template: {e}")
            return False
    
    @classmethod
    async def get_template(cls, name: str) -> Optional[dict]:
        """
        Get a template's settings
        
        Args:
            name: Template name
            
        Returns:
            Template settings dict or None
        """
        try:
            template_id = name.lower().replace(" ", "_")
            
            async with cls._lock:
                if template_id in cls.templates:
                    template = cls.templates[template_id]
                    return template.to_dict()
            return None
        except Exception as e:
            LOGGER.error(f"Error getting template: {e}")
            return None
    
    @classmethod
    async def get_template_settings(cls, name: str) -> Optional[dict]:
        """Get only the settings from a template"""
        try:
            template_id = name.lower().replace(" ", "_")
            
            async with cls._lock:
                if template_id in cls.templates:
                    return cls.templates[template_id].settings.copy()
            return None
        except Exception as e:
            LOGGER.error(f"Error getting template settings: {e}")
            return None
    
    @classmethod
    async def update_template(cls, name: str, **new_settings) -> bool:
        """Update template settings"""
        try:
            template_id = name.lower().replace(" ", "_")
            
            async with cls._lock:
                if template_id not in cls.templates:
                    LOGGER.warning(f"Template '{name}' not found")
                    return False
                
                cls.templates[template_id].settings.update(new_settings)
                LOGGER.info(f"Template '{name}' updated")
            return True
        except Exception as e:
            LOGGER.error(f"Error updating template: {e}")
            return False
    
    @classmethod
    async def duplicate_template(cls, source_name: str, new_name: str) -> bool:
        """Create a copy of an existing template"""
        try:
            source_id = source_name.lower().replace(" ", "_")
            new_id = new_name.lower().replace(" ", "_")
            
            async with cls._lock:
                if source_id not in cls.templates:
                    LOGGER.warning(f"Source template '{source_name}' not found")
                    return False
                
                if new_id in cls.templates:
                    LOGGER.warning(f"Template '{new_name}' already exists")
                    return False
                
                source_template = cls.templates[source_id]
                new_template = DownloadTemplate(
                    new_name,
                    f"Copy of {source_template.description}",
                    **source_template.settings.copy()
                )
                cls.templates[new_id] = new_template
                LOGGER.info(f"Template '{source_name}' duplicated as '{new_name}'")
            return True
        except Exception as e:
            LOGGER.error(f"Error duplicating template: {e}")
            return False
    
    @classmethod
    async def get_all_templates(cls) -> Dict[str, dict]:
        """Get all templates"""
        try:
            async with cls._lock:
                return {
                    name: template.to_dict()
                    for name, template in cls.templates.items()
                }
        except Exception as e:
            LOGGER.error(f"Error getting templates: {e}")
            return {}
    
    @classmethod
    async def get_templates_by_category(cls, category: str) -> Dict[str, dict]:
        """Get all templates for a specific category"""
        try:
            async with cls._lock:
                return {
                    name: template.to_dict()
                    for name, template in cls.templates.items()
                    if template.settings.get("category") == category
                }
        except Exception as e:
            LOGGER.error(f"Error getting templates by category: {e}")
            return {}
