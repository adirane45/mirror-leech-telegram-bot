# Task Categorization Module
# Organize tasks into categories
# Better task organization and management
# Modified by: justadi

from typing import Optional, Dict, List
from datetime import datetime
from asyncio import Lock

from .. import LOGGER


class TaskCategory:
    """Represents a task category"""
    
    def __init__(self, name: str, description: str = "", color: str = ""):
        self.name = name
        self.description = description
        self.color = color
        self.tasks: List[str] = []
        self.created_at = datetime.now()
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "task_count": len(self.tasks),
            "created_at": self.created_at.isoformat()
        }


class TaskCategorizer:
    """
    Manages task categories and categorization
    """
    
    # Default categories
    DEFAULT_CATEGORIES = {
        "movies": TaskCategory("Movies", "Video content", "🎬"),
        "software": TaskCategory("Software", "Applications and programs", "💾"),
        "documents": TaskCategory("Documents", "PDFs, Office files, etc.", "📄"),
        "backups": TaskCategory("Backups", "Backup files", "💾"),
        "other": TaskCategory("Other", "Uncategorized", "📦"),
    }
    
    categories: Dict[str, TaskCategory] = DEFAULT_CATEGORIES.copy()
    task_to_category: Dict[str, str] = {}  # task_id -> category_name
    _lock = Lock()
    
    @classmethod
    async def create_category(
        cls,
        name: str,
        description: str = "",
        color: str = ""
    ) -> bool:
        """
        Create a new task category
        
        Args:
            name: Category name (lowercase, no spaces)
            description: Category description
            color: Optional emoji or color code
            
        Returns:
            True if created successfully
        """
        try:
            name = name.lower().replace(" ", "_")
            
            async with cls._lock:
                if name in cls.categories:
                    LOGGER.warning(f"Category '{name}' already exists")
                    return False
                
                cls.categories[name] = TaskCategory(name, description, color)
                LOGGER.info(f"Category '{name}' created")
            return True
        except Exception as e:
            LOGGER.error(f"Error creating category: {e}")
            return False
    
    @classmethod
    async def delete_category(cls, name: str) -> bool:
        """Delete a category"""
        try:
            name = name.lower().replace(" ", "_")
            
            async with cls._lock:
                if name not in cls.categories or name in cls.DEFAULT_CATEGORIES:
                    LOGGER.warning(f"Cannot delete default category '{name}'")
                    return False
                
                # Move tasks to 'other'
                category = cls.categories[name]
                if category.tasks:
                    other_category = cls.categories.get("other")
                    if other_category:
                        other_category.tasks.extend(category.tasks)
                        for task_id in category.tasks:
                            cls.task_to_category[task_id] = "other"
                
                del cls.categories[name]
                LOGGER.info(f"Category '{name}' deleted")
            return True
        except Exception as e:
            LOGGER.error(f"Error deleting category: {e}")
            return False
    
    @classmethod
    async def categorize_task(
        cls,
        task_id: str,
        category_name: str
    ) -> bool:
        """
        Assign a task to a category
        
        Args:
            task_id: Task ID
            category_name: Target category name
            
        Returns:
            True if successful
        """
        try:
            category_name = category_name.lower().replace(" ", "_")
            
            async with cls._lock:
                if category_name not in cls.categories:
                    LOGGER.warning(f"Category '{category_name}' does not exist")
                    return False
                
                # Remove from old category
                old_category = cls.task_to_category.get(task_id)
                if old_category and old_category in cls.categories:
                    if task_id in cls.categories[old_category].tasks:
                        cls.categories[old_category].tasks.remove(task_id)
                
                # Add to new category
                cls.categories[category_name].tasks.append(task_id)
                cls.task_to_category[task_id] = category_name
                
                LOGGER.info(f"Task {task_id} categorized as '{category_name}'")
            return True
        except Exception as e:
            LOGGER.error(f"Error categorizing task: {e}")
            return False
    
    @classmethod
    async def get_tasks_by_category(cls, category_name: str) -> List[str]:
        """Get all tasks in a category"""
        try:
            category_name = category_name.lower().replace(" ", "_")
            async with cls._lock:
                if category_name in cls.categories:
                    return cls.categories[category_name].tasks.copy()
            return []
        except Exception as e:
            LOGGER.error(f"Error getting category tasks: {e}")
            return []
    
    @classmethod
    async def get_task_category(cls, task_id: str) -> Optional[str]:
        """Get the category of a task"""
        async with cls._lock:
            return cls.task_to_category.get(task_id, "other")
    
    @classmethod
    async def get_all_categories(cls) -> Dict[str, dict]:
        """Get all categories with their details"""
        try:
            async with cls._lock:
                return {
                    name: cat.to_dict()
                    for name, cat in cls.categories.items()
                }
        except Exception as e:
            LOGGER.error(f"Error getting categories: {e}")
            return {}
    
    @classmethod
    async def get_category_stats(cls) -> dict:
        """Get categorization statistics"""
        try:
            async with cls._lock:
                total_tasks = len(cls.task_to_category)
                return {
                    "total_tasks": total_tasks,
                    "total_categories": len(cls.categories),
                    "categories": {
                        name: {
                            "name": cat.name,
                            "count": len(cat.tasks),
                            "percentage": (len(cat.tasks) / total_tasks * 100) if total_tasks > 0 else 0
                        }
                        for name, cat in cls.categories.items()
                    }
                }
        except Exception as e:
            LOGGER.error(f"Error getting category stats: {e}")
            return {}
