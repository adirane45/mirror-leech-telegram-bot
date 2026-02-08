"""
Security Audit Logging for Phase 3
Comprehensive audit trail for security-sensitive operations
"""

import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime, UTC
from enum import Enum
from logging.handlers import RotatingFileHandler
import os

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of security audit events"""
    
    # Authentication events
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    LOGOUT = "LOGOUT"
    TOKEN_GENERATED = "TOKEN_GENERATED"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    
    # Authorization events
    PERMISSION_GRANTED = "PERMISSION_GRANTED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    ROLE_ASSIGNED = "ROLE_ASSIGNED"
    ROLE_REMOVED = "ROLE_REMOVED"
    
    # Access events
    API_ACCESS = "API_ACCESS"
    RESOURCE_ACCESS = "RESOURCE_ACCESS"
    ADMIN_ACCESS = "ADMIN_ACCESS"
    SENSITIVE_DATA_ACCESS = "SENSITIVE_DATA_ACCESS"
    
    # Security events
    CSRF_DETECTION = "CSRF_DETECTION"
    XSS_DETECTION = "XSS_DETECTION"
    SQL_INJECTION_DETECTION = "SQL_INJECTION_DETECTION"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    
    # Configuration events
    CONFIG_CHANGE = "CONFIG_CHANGE"
    SECRET_ROTATION = "SECRET_ROTATION"
    POLICY_CHANGE = "POLICY_CHANGE"
    
    # System events
    SYSTEM_START = "SYSTEM_START"
    SYSTEM_STOP = "SYSTEM_STOP"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    SECURITY_SCAN = "SECURITY_SCAN"


class AuditSeverity(Enum):
    """Audit severity levels"""
    
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AuditEntry:
    """Single audit log entry"""
    
    def __init__(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        result: bool = True,
        severity: AuditSeverity = AuditSeverity.INFO,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize audit entry
        
        Args:
            event_type: Type of audit event
            user_id: ID of user performing action
            resource: Resource affected
            action: Action performed
            result: Success/failure status
            severity: Event severity
            details: Additional details
            ip_address: Source IP address
            user_agent: User agent string
        """
        self.timestamp = datetime.now(UTC)
        self.event_type = event_type
        self.user_id = user_id or "SYSTEM"
        self.resource = resource
        self.action = action
        self.result = result
        self.severity = severity
        self.details = details or {}
        self.ip_address = ip_address
        self.user_agent = user_agent
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "resource": self.resource,
            "action": self.action,
            "result": "SUCCESS" if self.result else "FAILURE",
            "severity": self.severity.value,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "details": self.details,
        }
    
    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps(self.to_dict())


class AuditLogger:
    """
    Security audit logger
    
    Features:
    - JSON structured logging
    - Rotating file handler for large log volumes
    - Severity-based filtering
    - Sensitive data redaction
    - Real-time alerting for critical events
    """
    
    def __init__(
        self,
        log_file: str = "data/logs/security-audit.log",
        max_file_size: int = 52428800,  # 50MB
        backup_count: int = 10,
        min_severity: AuditSeverity = AuditSeverity.INFO,
    ):
        """
        Initialize audit logger
        
        Args:
            log_file: Path to audit log file
            max_file_size: Maximum file size before rotation
            backup_count: Number of backup files to keep
            min_severity: Minimum severity to log
        """
        self.log_file = log_file
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.min_severity = min_severity
        
        # Create logger
        self.logger = logging.getLogger("security-audit")
        self.logger.setLevel(logging.DEBUG)
        
        # Create log directory if needed
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Create rotating file handler
        handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
        )
        
        # Use JSON formatter
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        
        logger.info(f"AuditLogger initialized: {log_file}")
    
    def _should_log(self, severity: AuditSeverity) -> bool:
        """Check if event should be logged based on severity"""
        severity_order = {
            AuditSeverity.INFO: 0,
            AuditSeverity.WARNING: 1,
            AuditSeverity.CRITICAL: 2,
        }
        
        return severity_order.get(severity, 0) >= severity_order.get(self.min_severity, 0)
    
    def log_event(self, entry: AuditEntry) -> None:
        """
        Log an audit event
        
        Args:
            entry: AuditEntry to log
        """
        if not self._should_log(entry.severity):
            return
        
        # Log to audit logger
        self.logger.info(entry.to_json())
        
        # Alert on critical events
        if entry.severity == AuditSeverity.CRITICAL:
            self._alert_critical(entry)
    
    def _alert_critical(self, entry: AuditEntry) -> None:
        """Alert on critical security events"""
        logger.critical(f"SECURITY ALERT: {entry.event_type.value} - {entry.details}")
    
    def log_login(
        self,
        user_id: str,
        success: bool = True,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log login event"""
        event_type = AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILURE
        severity = AuditSeverity.INFO if success else AuditSeverity.WARNING
        
        entry = AuditEntry(
            event_type=event_type,
            user_id=user_id,
            action="login",
            result=success,
            severity=severity,
            ip_address=ip_address,
            details=details or {},
        )
        
        self.log_event(entry)
    
    def log_api_access(
        self,
        user_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        ip_address: Optional[str] = None,
        response_time_ms: Optional[int] = None,
    ) -> None:
        """Log API access"""
        success = 200 <= status_code < 300
        severity = AuditSeverity.INFO if success else AuditSeverity.WARNING
        
        if status_code == 401:
            severity = AuditSeverity.WARNING
        elif status_code == 403:
            severity = AuditSeverity.WARNING
        elif status_code >= 500:
            severity = AuditSeverity.CRITICAL
        
        entry = AuditEntry(
            event_type=AuditEventType.API_ACCESS,
            user_id=user_id,
            resource=endpoint,
            action=f"{method} {endpoint}",
            result=success,
            severity=severity,
            ip_address=ip_address,
            details={
                "method": method,
                "status_code": status_code,
                "response_time_ms": response_time_ms,
            },
        )
        
        self.log_event(entry)
    
    def log_security_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """
        Log security-related event
        
        Events logged as CRITICAL include:
        - CSRF detection
        - XSS injection detection
        - SQL injection detection
        - Unauthorized access
        - Rate limit exceeded
        """
        critical_events = {
            AuditEventType.CSRF_DETECTION,
            AuditEventType.XSS_DETECTION,
            AuditEventType.SQL_INJECTION_DETECTION,
            AuditEventType.UNAUTHORIZED_ACCESS,
            AuditEventType.RATE_LIMIT_EXCEEDED,
        }
        
        severity = AuditSeverity.CRITICAL if event_type in critical_events else AuditSeverity.WARNING
        
        entry = AuditEntry(
            event_type=event_type,
            user_id=user_id,
            result=False,
            severity=severity,
            ip_address=ip_address,
            details=details or {},
        )
        
        self.log_event(entry)
    
    def log_config_change(
        self,
        user_id: str,
        config_key: str,
        old_value: Any,
        new_value: Any,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log configuration change"""
        entry = AuditEntry(
            event_type=AuditEventType.CONFIG_CHANGE,
            user_id=user_id,
            resource=config_key,
            action=f"Changed {config_key}",
            severity=AuditSeverity.WARNING,
            ip_address=ip_address,
            details={
                "config_key": config_key,
                "old_value": self._redact_sensitive(config_key, old_value),
                "new_value": self._redact_sensitive(config_key, new_value),
            },
        )
        
        self.log_event(entry)
    
    def log_permission_change(
        self,
        user_id: str,
        target_user: str,
        permission: str,
        granted: bool,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log permission change"""
        event_type = AuditEventType.PERMISSION_GRANTED if granted else AuditEventType.PERMISSION_DENIED
        
        entry = AuditEntry(
            event_type=event_type,
            user_id=user_id,
            resource=target_user,
            action=f"{'Granted' if granted else 'Denied'} {permission}",
            severity=AuditSeverity.WARNING,
            ip_address=ip_address,
            details={
                "target_user": target_user,
                "permission": permission,
            },
        )
        
        self.log_event(entry)
    
    @staticmethod
    def _redact_sensitive(key: str, value: Any) -> Any:
        """Redact sensitive values"""
        sensitive_keywords = ["password", "token", "secret", "key", "credential", "api"]
        
        if any(keyword in key.lower() for keyword in sensitive_keywords):
            if isinstance(value, str) and len(value) > 0:
                return f"{value[0]}{'*' * (len(value) - 2)}{value[-1]}"
            return "***REDACTED***"
        
        return value


# Singleton instance
_audit_logger_instance: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create AuditLogger singleton"""
    global _audit_logger_instance
    if _audit_logger_instance is None:
        _audit_logger_instance = AuditLogger()
    return _audit_logger_instance
