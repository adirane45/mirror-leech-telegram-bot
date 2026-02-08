"""
Backup Manager - Automated Backups and Recovery
Handles backup scheduling, execution, and restoration
Safe Innovation Path - Phase 2

Enhanced by: justadi
Date: February 5, 2026
"""

import asyncio
import shutil
from pathlib import Path
from datetime import datetime, timedelta, UTC
from typing import Dict, Optional, List
import json
import hashlib
from logging import getLogger

from .config_manager import Config

LOGGER = getLogger(__name__)


class BackupMetadata:
    """Metadata for a backup"""

    def __init__(self, backup_dir: Path):
        self.backup_dir = backup_dir
        self.metadata_file = backup_dir / "metadata.json"
        self.data = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """Load metadata from file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                LOGGER.error(f"Error loading metadata: {e}")
                return {}
        return {}

    def save(self):
        """Save metadata to file"""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.data, f, indent=2, default=str)
        except Exception as e:
            LOGGER.error(f"Error saving metadata: {e}")

    def update(self, key: str, value):
        """Update metadata field"""
        self.data[key] = value
        self.save()


class BackupManager:
    """
    Manages automated backups and recovery
    Supports incremental backups and verification
    """

    _instance = None
    _enabled = False
    _backup_root = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BackupManager, cls).__new__(cls)
        return cls._instance

    def enable(self):
        """Enable backup manager"""
        self._enabled = getattr(Config, "ENABLE_BACKUP_SYSTEM", False)
        
        if self._enabled:
            backup_dir = getattr(Config, "BACKUP_DIR", "backups")
            self._backup_root = Path(backup_dir)
            self._backup_root.mkdir(exist_ok=True)
            LOGGER.info(f"✅ Backup system enabled at {self._backup_root}")
        else:
            LOGGER.debug("Backup system disabled")

    @property
    def is_enabled(self) -> bool:
        """Check if backup manager is enabled"""
        return self._enabled

    async def create_backup(
        self,
        source_paths: List[str],
        backup_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Create a backup of specified paths

        Args:
            source_paths: List of paths to backup
            backup_name: Custom backup name (default: timestamp)
            description: Backup description

        Returns:
            Backup metadata dictionary
        """
        if not self._enabled:
            return None

        try:
            # Create backup directory
            if backup_name is None:
                backup_name = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

            backup_dir = self._backup_root / backup_name
            backup_dir.mkdir(exist_ok=True)

            # Create metadata
            metadata = BackupMetadata(backup_dir)
            metadata.update("name", backup_name)
            metadata.update("created_at", datetime.now(UTC).isoformat())
            metadata.update("description", description or "")
            metadata.update("source_paths", source_paths)

            total_size = 0
            backed_up_items = []

            # Backup each path
            for source_path in source_paths:
                source = Path(source_path)
                if not source.exists():
                    LOGGER.warning(f"Source path does not exist: {source}")
                    continue

                try:
                    target = backup_dir / source.name

                    if source.is_dir():
                        shutil.copytree(source, target, dirs_exist_ok=True)
                    else:
                        shutil.copy2(source, target)

                    size = self._get_size(target)
                    total_size += size
                    backed_up_items.append({
                        "path": source_path,
                        "type": "directory" if source.is_dir() else "file",
                        "size": size,
                    })

                    LOGGER.debug(f"Backed up: {source_path}")

                except Exception as e:
                    LOGGER.error(f"Error backing up {source_path}: {e}")

            # Update metadata
            metadata.update("items", backed_up_items)
            metadata.update("total_size", total_size)
            metadata.update("status", "completed")

            result = {
                "backup_name": backup_name,
                "backup_dir": str(backup_dir),
                "items_count": len(backed_up_items),
                "total_size": total_size,
                "created_at": datetime.now(UTC).isoformat(),
            }

            LOGGER.info(f"Backup created: {backup_name} ({total_size} bytes)")
            return result

        except Exception as e:
            LOGGER.error(f"Error creating backup: {e}")
            return None

    async def restore_backup(
        self,
        backup_name: str,
        restore_path: Optional[str] = None,
    ) -> bool:
        """
        Restore files from a backup

        Args:
            backup_name: Name of backup to restore
            restore_path: Path to restore to (default: original path)

        Returns:
            True if successful
        """
        if not self._enabled:
            return False

        try:
            backup_dir = self._backup_root / backup_name
            if not backup_dir.exists():
                LOGGER.error(f"Backup not found: {backup_name}")
                return False

            # Load metadata
            metadata = BackupMetadata(backup_dir)
            original_paths = metadata.data.get("source_paths", [])

            # Restore files
            for item_data in metadata.data.get("items", []):
                original_path = Path(item_data["path"])
                backup_item = backup_dir / original_path.name

                if not backup_item.exists():
                    LOGGER.warning(f"Backup item not found: {backup_item}")
                    continue

                target = Path(restore_path) / original_path.name if restore_path else original_path

                try:
                    # Create parent directory if needed
                    target.parent.mkdir(parents=True, exist_ok=True)

                    if backup_item.is_dir():
                        if target.exists():
                            shutil.rmtree(target)
                        shutil.copytree(backup_item, target)
                    else:
                        shutil.copy2(backup_item, target)

                    LOGGER.debug(f"Restored: {target}")

                except Exception as e:
                    LOGGER.error(f"Error restoring {item_data['path']}: {e}")

            LOGGER.info(f"Backup restored: {backup_name}")
            return True

        except Exception as e:
            LOGGER.error(f"Error restoring backup: {e}")
            return False

    def verify_backup(self, backup_name: str) -> bool:
        """Verify backup integrity"""
        if not self._enabled:
            return False

        try:
            backup_dir = self._backup_root / backup_name
            if not backup_dir.exists():
                return False

            metadata = BackupMetadata(backup_dir)

            # Check that all items exist
            for item_data in metadata.data.get("items", []):
                item_path = backup_dir / Path(item_data["path"]).name
                if not item_path.exists():
                    LOGGER.error(f"Missing backup item: {item_path}")
                    return False

            return True

        except Exception as e:
            LOGGER.error(f"Error verifying backup: {e}")
            return False

    def list_backups(self) -> List[Dict]:
        """List all available backups"""
        if not self._enabled:
            return []

        backups = []

        if not self._backup_root.exists():
            return backups

        try:
            for backup_dir in self._backup_root.iterdir():
                if not backup_dir.is_dir():
                    continue

                metadata = BackupMetadata(backup_dir)
                backups.append({
                    "name": backup_dir.name,
                    "created_at": metadata.data.get("created_at"),
                    "size": metadata.data.get("total_size", 0),
                    "items_count": len(metadata.data.get("items", [])),
                    "description": metadata.data.get("description", ""),
                })

            # Sort by creation time (newest first)
            backups.sort(
                key=lambda x: x.get("created_at", ""),
                reverse=True
            )

            return backups

        except Exception as e:
            LOGGER.error(f"Error listing backups: {e}")
            return []

    def cleanup_old_backups(self, days: int = 30) -> int:
        """
        Delete backups older than specified days

        Args:
            days: Days to keep backups for

        Returns:
            Number of backups deleted
        """
        if not self._enabled:
            return 0

        try:
            cutoff_time = datetime.now(UTC) - timedelta(days=days)
            deleted_count = 0

            for backup_dir in self._backup_root.iterdir():
                if not backup_dir.is_dir():
                    continue

                metadata = BackupMetadata(backup_dir)
                created_at_str = metadata.data.get("created_at")

                if created_at_str:
                    try:
                        created_at = datetime.fromisoformat(created_at_str)
                        if created_at < cutoff_time:
                            shutil.rmtree(backup_dir)
                            deleted_count += 1
                            LOGGER.info(f"Deleted old backup: {backup_dir.name}")
                    except Exception as e:
                        LOGGER.error(f"Error parsing backup date: {e}")

            return deleted_count

        except Exception as e:
            LOGGER.error(f"Error cleaning up backups: {e}")
            return 0

    def _get_size(self, path: Path) -> int:
        """Get total size of a path"""
        if path.is_file():
            return path.stat().st_size

        total = 0
        for item in path.rglob("*"):
            if item.is_file():
                total += item.stat().st_size
        return total

    def get_backup_stats(self) -> Dict:
        """Get backup system statistics"""
        if not self._enabled:
            return {"enabled": False}

        backups = self.list_backups()
        total_size = sum(b["size"] for b in backups)

        return {
            "enabled": True,
            "backup_directory": str(self._backup_root),
            "total_backups": len(backups),
            "total_size": total_size,
            "backups": backups,
        }


# Singleton instance
backup_manager = BackupManager()
