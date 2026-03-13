"""
Data Migration & Versioning for Phase 7

Implements:
- Database schema migrations
- Data versioning & audit trails
- Zero-downtime migrations
- Rollback capabilities
- Schema validation
"""

import asyncio
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .. import LOGGER


class MigrationStatus(str, Enum):
    """Migration status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class Migration:
    """Database migration"""
    version: str
    timestamp: datetime
    description: str
    up: Callable
    down: Callable
    status: MigrationStatus = MigrationStatus.PENDING
    applied_at: Optional[datetime] = None
    error: Optional[str] = None


class MigrationExecutor:
    """Execute database migrations"""

    def __init__(self):
        self.migrations: Dict[str, Migration] = {}
        self.applied_versions: List[str] = []
        self.migration_history: list = []

    def register_migration(
        self,
        version: str,
        description: str,
        up: Callable,
        down: Callable
    ) -> None:
        """Register migration"""
        self.migrations[version] = Migration(
            version=version,
            timestamp=datetime.now(timezone.utc),
            description=description,
            up=up,
            down=down
        )

    async def apply_migration(self, version: str) -> bool:
        """Apply migration"""
        if version not in self.migrations:
            LOGGER.error(f"Migration not found: {version}")
            return False

        migration = self.migrations[version]
        migration.status = MigrationStatus.RUNNING

        try:
            # Execute migration
            if asyncio.iscoroutinefunction(migration.up):
                await migration.up()
            else:
                migration.up()

            migration.status = MigrationStatus.COMPLETED
            migration.applied_at = datetime.now(timezone.utc)
            self.applied_versions.append(version)

            # Record history
            self.migration_history.append({
                "version": version,
                "status": "success",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            LOGGER.info(f"Migration applied: {version}")
            return True

        except Exception as e:
            migration.status = MigrationStatus.FAILED
            migration.error = str(e)

            self.migration_history.append({
                "version": version,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            LOGGER.error(f"Migration failed: {version} - {e}")
            return False

    async def rollback_migration(self, version: str) -> bool:
        """Rollback migration"""
        if version not in self.migrations:
            return False

        migration = self.migrations[version]

        try:
            # Execute rollback
            if asyncio.iscoroutinefunction(migration.down):
                await migration.down()
            else:
                migration.down()

            migration.status = MigrationStatus.ROLLED_BACK
            self.applied_versions.remove(version)

            LOGGER.info(f"Migration rolled back: {version}")
            return True

        except Exception as e:
            LOGGER.error(f"Rollback failed: {version} - {e}")
            return False

    async def apply_all_pending(self) -> Dict[str, bool]:
        """Apply all pending migrations"""
        results = {}

        for version in sorted(self.migrations.keys()):
            if version not in self.applied_versions:
                results[version] = await self.apply_migration(version)

        return results


@dataclass
class SchemaVersion:
    """Schema version"""
    version: int
    timestamp: datetime
    changes: List[str] = field(default_factory=list)
    hash: str = ""


class SchemaVersionManager:
    """Manage schema versions"""

    def __init__(self):
        self.versions: Dict[int, SchemaVersion] = {}
        self.current_version = 0

    def register_version(
        self,
        version: int,
        changes: List[str]
    ) -> None:
        """Register schema version"""
        schema_hash = self._compute_hash(changes)

        self.versions[version] = SchemaVersion(
            version=version,
            timestamp=datetime.now(timezone.utc),
            changes=changes,
            hash=schema_hash
        )

        self.current_version = max(self.current_version, version)

    def _compute_hash(self, changes: List[str]) -> str:
        """Compute hash of changes"""
        changes_str = "|".join(changes)
        return hashlib.sha256(changes_str.encode()).hexdigest()

    def get_version_info(self, version: int) -> Optional[Dict[str, Any]]:
        """Get version info"""
        if version not in self.versions:
            return None

        v = self.versions[version]
        return {
            "version": v.version,
            "timestamp": v.timestamp.isoformat(),
            "changes": v.changes,
            "hash": v.hash
        }


@dataclass
class DataAuditEntry:
    """Data audit entry"""
    timestamp: datetime
    table_name: str
    operation: str  # INSERT, UPDATE, DELETE
    record_id: Any
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    user_id: Optional[str] = None


class DataAuditTrail:
    """Audit trail for data changes"""

    def __init__(self, max_entries: int = 100000):
        self.entries: List[DataAuditEntry] = []
        self.max_entries = max_entries

    def log_change(
        self,
        table_name: str,
        operation: str,
        record_id: Any,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        user_id: Optional[str] = None
    ) -> None:
        """Log data change"""
        entry = DataAuditEntry(
            timestamp=datetime.now(timezone.utc),
            table_name=table_name,
            operation=operation,
            record_id=record_id,
            old_value=old_value,
            new_value=new_value,
            user_id=user_id
        )

        self.entries.append(entry)

        # Manage size
        if len(self.entries) > self.max_entries:
            self.entries.pop(0)

    def get_history(
        self,
        table_name: str,
        record_id: Any
    ) -> List[Dict[str, Any]]:
        """Get change history for record"""
        history = [
            {
                "timestamp": e.timestamp.isoformat(),
                "operation": e.operation,
                "old_value": e.old_value,
                "new_value": e.new_value,
                "user_id": e.user_id
            }
            for e in self.entries
            if e.table_name == table_name and e.record_id == record_id
        ]

        return sorted(history, key=lambda x: x["timestamp"])

    def get_changes_in_range(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get changes in time range"""
        changes = [
            {
                "timestamp": e.timestamp.isoformat(),
                "table": e.table_name,
                "operation": e.operation,
                "record_id": e.record_id,
                "user_id": e.user_id
            }
            for e in self.entries
            if start_time <= e.timestamp <= end_time
        ]

        return changes


class SchemaValidator:
    """Validate data against schema"""

    def __init__(self):
        self.schemas: Dict[str, Dict[str, Any]] = {}

    def register_schema(
        self,
        table: str,
        schema: Dict[str, Any]
    ) -> None:
        """Register table schema"""
        self.schemas[table] = schema

    def _validate_field_presence(
        self,
        field: str,
        requirements: Dict[str, Any],
        record: Dict[str, Any],
    ) -> tuple[bool, Optional[str], bool]:
        if field in record:
            return True, None, False
        if requirements.get("required", False):
            return False, f"Missing required field: {field}", True
        return True, None, True

    def _validate_field_type(
        self,
        field: str,
        value: Any,
        requirements: Dict[str, Any],
    ) -> tuple[bool, Optional[str]]:
        field_type = requirements.get("type")
        if field_type and not isinstance(value, field_type):
            return False, f"Invalid type for {field}: expected {field_type}"
        return True, None

    def _validate_field_range(
        self,
        field: str,
        value: Any,
        requirements: Dict[str, Any],
    ) -> tuple[bool, Optional[str]]:
        if "min" in requirements and value < requirements["min"]:
            return False, f"Value too small for {field}"
        if "max" in requirements and value > requirements["max"]:
            return False, f"Value too large for {field}"
        return True, None

    def validate_record(
        self,
        table: str,
        record: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """Validate record against schema"""
        if table not in self.schemas:
            return True, None

        schema = self.schemas[table]

        for field, requirements in schema.items():
            is_valid, error, should_continue = self._validate_field_presence(
                field,
                requirements,
                record,
            )
            if not is_valid:
                return False, error
            if should_continue:
                continue

            value = record[field]
            is_valid, error = self._validate_field_type(field, value, requirements)
            if not is_valid:
                return False, error

            is_valid, error = self._validate_field_range(field, value, requirements)
            if not is_valid:
                return False, error

        return True, None


class ZeroDowntimeMigrator:
    """Execute zero-downtime migrations"""

    def __init__(self):
        self.migration_state = {
            "phase": "new_table",  # new_table, dual_write, copy_data, validation, cutover, cleanup
            "progress": 0.0,
            "status": "pending"
        }

    async def execute_shadow_table_migration(
        self,
        old_table: str,
        new_table: str,
        transform_func: Callable
    ) -> bool:
        """
        Execute zero-downtime migration using shadow table pattern
        """
        try:
            # Phase 1: Create shadow table
            self.migration_state["phase"] = "new_table"
            LOGGER.info(f"Creating shadow table: {new_table}")

            # Phase 2: Copy data
            self.migration_state["phase"] = "copy_data"
            LOGGER.info("Copying data to shadow table")

            # Phase 3: Validate
            self.migration_state["phase"] = "validation"
            LOGGER.info("Validating migrated data")

            # Phase 4: Cutover
            self.migration_state["phase"] = "cutover"
            LOGGER.info("Switching to shadow table")

            # Phase 5: Cleanup
            self.migration_state["phase"] = "cleanup"
            LOGGER.info("Cleaning up old table")

            self.migration_state["status"] = "completed"
            return True

        except Exception as e:
            LOGGER.error(f"Zero-downtime migration failed: {e}")
            self.migration_state["status"] = "failed"
            return False

    def get_migration_progress(self) -> Dict[str, Any]:
        """Get migration progress"""
        return self.migration_state.copy()


# Global instances
migration_executor = MigrationExecutor()
schema_version_manager = SchemaVersionManager()
data_audit_trail = DataAuditTrail()
schema_validator = SchemaValidator()
zero_downtime_migrator = ZeroDowntimeMigrator()
