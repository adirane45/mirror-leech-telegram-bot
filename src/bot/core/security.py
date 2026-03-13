"""
Security Enhancements & Access Control for Phase 7

Implements:
- Rate limiting with token bucket algorithm
- Request signing & verification
- Encryption for sensitive data
- Role-based access control (RBAC)
- Audit trail with tamper detection
"""

import hmac
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List,  Dict, Any, Optional, Set
from enum import Enum
from dataclasses import dataclass, field
import json

from .. import LOGGER


class UserRole(str, Enum):
    """User roles"""
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"


@dataclass
class Permission:
    """Permission definition"""
    resource: str
    action: str
    
    def __hash__(self) -> int:
        return hash((self.resource, self.action))
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Permission):
            return False
        return self.resource == other.resource and self.action == other.action


# Predefined permissions
ADMIN_PERMISSIONS = {
    Permission("users", "create"),
    Permission("users", "read"),
    Permission("users", "update"),
    Permission("users", "delete"),
    Permission("system", "configure"),
    Permission("system", "restart"),
    Permission("audit", "read"),
}

MODERATOR_PERMISSIONS = {
    Permission("users", "read"),
    Permission("tasks", "read"),
    Permission("tasks", "cancel"),
    Permission("audit", "read"),
}

USER_PERMISSIONS = {
    Permission("tasks", "create"),
    Permission("tasks", "read"),
    Permission("file", "download"),
}

GUEST_PERMISSIONS = {
    Permission("file", "download"),
}


class TokenBucketRateLimiter:
    """Token bucket algorithm for rate limiting"""
    
    def __init__(self, rate: int, bucket_size: int) -> None:
        """
        Args:
            rate: Tokens per second
            bucket_size: Maximum tokens in bucket
        """
        self.rate = rate
        self.bucket_size = bucket_size
        self.tokens: float = float(bucket_size)
        self.last_refill = datetime.now(timezone.utc)
    
    def allow_request(self, tokens: int = 1) -> bool:
        """Check if request is allowed"""
        now = datetime.now(timezone.utc)
        elapsed = (now - self.last_refill).total_seconds()
        
        # Refill tokens
        self.tokens = min(
            float(self.bucket_size),
            self.tokens + (elapsed * self.rate)
        )
        self.last_refill = now
        
        # Check if we have enough tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def get_retry_after(self) -> float:
        """Get seconds to wait before next request"""
        if self.tokens >= 1:
            return 0
        
        return (1 - self.tokens) / self.rate


class RequestSigner:
    """Sign and verify requests"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()
    
    def sign_request(
        self,
        method: str,
        path: str,
        body: Optional[str] = None,
        timestamp: Optional[str] = None
    ) -> str:
        """Create signature for request"""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()
        
        # Create canonical request string
        canonical = f"{method}|{path}|{body or ''}|{timestamp}"
        
        # Sign with HMAC-SHA256
        signature = hmac.new(
            self.secret_key,
            canonical.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_signature(
        self,
        method: str,
        path: str,
        signature: str,
        body: Optional[str] = None,
        timestamp: Optional[str] = None,
        max_age_seconds: int = 300
    ) -> bool:
        """Verify request signature"""
        if timestamp is None:
            return False
        
        # Check timestamp freshness
        try:
            ts = datetime.fromisoformat(timestamp)
            age = (datetime.now(timezone.utc) - ts).total_seconds()
            
            if age > max_age_seconds or age < 0:
                return False
        
        except (ValueError, TypeError):
            return False
        
        # Verify signature
        expected_sig = self.sign_request(
            method, path, body, timestamp
        )
        
        return hmac.compare_digest(signature, expected_sig)


class DataEncryptor:
    """Encrypt/decrypt sensitive data"""
    
    def __init__(self, key: str):
        self.key = key
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        # Simple XOR encryption for demo (use Fernet in production)
        key_bytes = self.key.encode()
        data_bytes = data.encode()
        
        encrypted = bytes([
            b ^ key_bytes[i % len(key_bytes)]
            for i, b in enumerate(data_bytes)
        ])
        
        return encrypted.hex()
    
    def decrypt(self, encrypted: str) -> Optional[str]:
        """Decrypt string data"""
        try:
            key_bytes = self.key.encode()
            data_bytes = bytes.fromhex(encrypted)
            
            decrypted = bytes([
                b ^ key_bytes[i % len(key_bytes)]
                for i, b in enumerate(data_bytes)
            ])
            
            return decrypted.decode()
        
        except Exception as e:
            LOGGER.error(f"Decrypt error: {e}")
            return None


class RoleBasedAccessControl:
    """Role-based access control"""
    
    def __init__(self) -> None:
        self.role_permissions: Dict[UserRole, Set[Permission]] = {
            UserRole.ADMIN: ADMIN_PERMISSIONS,
            UserRole.MODERATOR: MODERATOR_PERMISSIONS,
            UserRole.USER: USER_PERMISSIONS,
            UserRole.GUEST: GUEST_PERMISSIONS,
        }
    
    def grant_permission(
        self,
        role: UserRole,
        permission: Permission
    ) -> None:
        """Grant permission to role"""
        if role not in self.role_permissions:
            self.role_permissions[role] = set()
        
        self.role_permissions[role].add(permission)
    
    def revoke_permission(
        self,
        role: UserRole,
        permission: Permission
    ) -> None:
        """Revoke permission from role"""
        if role in self.role_permissions:
            self.role_permissions[role].discard(permission)
    
    def check_permission(
        self,
        role: UserRole,
        resource: str,
        action: str
    ) -> bool:
        """Check if role has permission"""
        if role not in self.role_permissions:
            return False
        
        permission = Permission(resource, action)
        return permission in self.role_permissions[role]


@dataclass
class AuditEntry:
    """Audit log entry"""
    timestamp: datetime
    user_id: str
    action: str
    resource: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    status: str = "success"
    error: Optional[str] = None
    ip_address: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "action": self.action,
            "resource": self.resource,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "status": self.status,
            "error": self.error,
            "ip_address": self.ip_address,
        }


class AuditTrail:
    """Tamper-proof audit trail"""
    
    def __init__(self, max_entries: int = 100000):
        self.entries: List[Any] = []
        self.max_entries = max_entries
        self.checksums: List[Any] = []
    
    def _compute_checksum(self, entry_dict: Dict[str, Any]) -> str:
        """Compute checksum for entry"""
        entry_str = json.dumps(entry_dict, sort_keys=True)
        return hashlib.sha256(entry_str.encode()).hexdigest()
    
    def log_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        status: str = "success",
        error: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """Log action to audit trail"""
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            action=action,
            resource=resource,
            old_value=old_value,
            new_value=new_value,
            status=status,
            error=error,
            ip_address=ip_address
        )
        
        entry_dict = entry.to_dict()
        checksum = self._compute_checksum(entry_dict)
        
        self.entries.append(entry)
        self.checksums.append(checksum)
        
        # Manage size
        if len(self.entries) > self.max_entries:
            self.entries.pop(0)
            self.checksums.pop(0)
    
    def verify_integrity(self) -> bool:
        """Verify audit trail integrity"""
        for i, entry in enumerate(self.entries):
            expected = self.checksums[i]
            actual = self._compute_checksum(entry.to_dict())
            
            if expected != actual:
                LOGGER.error(f"Audit trail tamper detected at entry {i}")
                return False
        
        return True
    
    def get_entries(
        self,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Any]:
        """Get audit entries"""
        filtered = self.entries
        
        if user_id:
            filtered = [e for e in filtered if e.user_id == user_id]
        
        if start_time:
            filtered = [e for e in filtered if e.timestamp >= start_time]
        
        if end_time:
            filtered = [e for e in filtered if e.timestamp <= end_time]
        
        return [e.to_dict() for e in filtered]


# Global instances
rbac = RoleBasedAccessControl()
audit_trail = AuditTrail()
