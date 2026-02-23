"""
Recovery Manager - Automated Recovery and Data Integrity
Handles corruption detection, validation, and data recovery
Safe Innovation Path - Phase 2

Enhanced by: justadi
Date: February 5, 2026
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, UTC
import json
import hashlib
from logging import getLogger

from .config_manager import Config

LOGGER = getLogger(__name__)


class IntegrityCheck:
    """Represents a data integrity check result"""

    def __init__(self, path: str, is_valid: bool, details: Optional[Dict] = None):
        self.path = path
        self.is_valid = is_valid
        self.details = details or {}
        self.timestamp = datetime.now(UTC)


class RecoveryManager:
    """
    Manages recovery procedures and data integrity
    Handles validation, corruption detection, and auto-recovery
    """

    _instance = None
    _enabled = False
    _integrity_checks: List[IntegrityCheck] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RecoveryManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._integrity_checks = []
            self._initialized = True

    def enable(self):
        """Enable recovery manager"""
        self._enabled = getattr(Config, "ENABLE_RECOVERY_MANAGER", False)
        
        if self._enabled:
            LOGGER.info("✅ Recovery manager enabled")
        else:
            LOGGER.debug("Recovery manager disabled")

    @property
    def is_enabled(self) -> bool:
        """Check if recovery manager is enabled"""
        return self._enabled

    async def verify_integrity(
        self,
        path: str,
        check_hash: bool = True,
        check_structure: bool = True,
    ) -> Tuple[bool, Dict]:
        """
        Verify data integrity of a path

        Args:
            path: Path to verify
            check_hash: Verify file hash
            check_structure: Verify directory structure

        Returns:
            Tuple of (is_valid, details_dict)
        """
        if not self._enabled:
            return True, {}

        details = {
            "hash_valid": True,
            "structure_valid": True,
            "errors": [],
        }

        p = Path(path)

        if not p.exists():
            details["errors"].append(f"Path does not exist: {path}")
            return False, details

        # Check hash if file
        if p.is_file() and check_hash:
            try:
                file_hash = self._calculate_hash(p)
                details["file_hash"] = file_hash
            except Exception as e:
                details["errors"].append(f"Hash calculation failed: {e}")
                details["hash_valid"] = False

        # Check structure if directory
        if p.is_dir() and check_structure:
            structure_errors = self._verify_directory_structure(p)
            if structure_errors:
                details["structure_valid"] = False
                details["errors"].extend(structure_errors)

        is_valid = len(details["errors"]) == 0
        check = IntegrityCheck(path, is_valid, details)
        self._integrity_checks.append(check)

        if not is_valid:
            LOGGER.warning(f"Integrity check failed for {path}: {details['errors']}")

        return is_valid, details

    def _calculate_hash(self, file_path: Path, algorithm: str = "sha256") -> str:
        """Calculate file hash"""
        hasher = hashlib.new(algorithm)

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)

        return hasher.hexdigest()

    def _verify_directory_structure(self, dir_path: Path) -> List[str]:
        """Verify directory structure integrity"""
        errors = []

        try:
            # Check if all files are readable
            for item in dir_path.rglob("*"):
                try:
                    if item.is_file():
                        item.stat()
                except PermissionError:
                    errors.append(f"Permission denied: {item}")
                except Exception as e:
                    errors.append(f"Access error: {item} - {e}")

        except Exception as e:
            errors.append(f"Directory traversal error: {e}")

        return errors

    async def repair_corrupted_data(
        self,
        path: str,
        backup_source: Optional[str] = None,
    ) -> bool:
        """
        Attempt to repair corrupted data

        Args:
            path: Path with potential corruption
            backup_source: Path to restore from (if available)

        Returns:
            True if repair successful
        """
        if not self._enabled:
            return False

        try:
            # Check if corruption is detected
            is_valid, details = await self.verify_integrity(path)

            if is_valid:
                LOGGER.info(f"Data is intact: {path}")
                return True

            # Try to restore from backup if available
            if backup_source:
                LOGGER.info(f"Attempting to restore from backup: {backup_source}")
                p = Path(path)
                backup = Path(backup_source)

                if backup.exists():
                    if p.exists():
                        if p.is_file():
                            p.unlink()
                        else:
                            import shutil
                            shutil.rmtree(p)

                    if backup.is_file():
                        import shutil
                        shutil.copy2(backup, p)
                    else:
                        import shutil
                        shutil.copytree(backup, p)

                    LOGGER.info(f"Data restored from backup: {path}")
                    return True

            return False

        except Exception as e:
            LOGGER.error(f"Error repairing data: {e}")
            return False

    async def auto_recover(
        self,
        critical_paths: List[str],
        backup_dir: Optional[str] = None,
    ) -> Dict:
        """
        Perform automatic recovery for critical paths

        Args:
            critical_paths: List of critical paths to check
            backup_dir: Directory containing backups

        Returns:
            Recovery report
        """
        if not self._enabled:
            return {"enabled": False}

        report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_paths": len(critical_paths),
            "valid_paths": 0,
            "repaired_paths": 0,
            "failed_paths": 0,
            "details": [],
        }

        for path in critical_paths:
            try:
                is_valid, details = await self.verify_integrity(path)

                if is_valid:
                    report["valid_paths"] += 1
                    report["details"].append({
                        "path": path,
                        "status": "valid",
                    })
                else:
                    # Try to repair
                    backup_path = None
                    if backup_dir:
                        backup_path = str(Path(backup_dir) / Path(path).name)

                    repaired = await self.repair_corrupted_data(path, backup_path)

                    if repaired:
                        report["repaired_paths"] += 1
                        report["details"].append({
                            "path": path,
                            "status": "repaired",
                        })
                    else:
                        report["failed_paths"] += 1
                        report["details"].append({
                            "path": path,
                            "status": "failed",
                            "errors": details.get("errors", []),
                        })

            except Exception as e:
                report["failed_paths"] += 1
                report["details"].append({
                    "path": path,
                    "status": "failed",
                    "error": str(e),
                })

        LOGGER.info(
            f"Recovery complete: {report['valid_paths']} valid, "
            f"{report['repaired_paths']} repaired, {report['failed_paths']} failed"
        )

        return report

    def get_integrity_history(self, limit: int = 50) -> List[Dict]:
        """Get recent integrity check history"""
        if not self._enabled:
            return []

        checks = self._integrity_checks[-limit:]
        return [
            {
                "path": check.path,
                "is_valid": check.is_valid,
                "timestamp": check.timestamp.isoformat(),
                "details": check.details,
            }
            for check in reversed(checks)
        ]

    def get_recovery_status(self) -> Dict:
        """Get recovery manager status"""
        if not self._enabled:
            return {"enabled": False}

        total_checks = len(self._integrity_checks)
        valid_checks = len([c for c in self._integrity_checks if c.is_valid])

        return {
            "enabled": True,
            "total_checks": total_checks,
            "valid_checks": valid_checks,
            "failed_checks": total_checks - valid_checks,
            "success_rate": (valid_checks / total_checks * 100) if total_checks > 0 else 0,
        }


# Singleton instance
recovery_manager = RecoveryManager()
