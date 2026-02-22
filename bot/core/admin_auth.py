"""
Secure Admin Authentication for Web Interface

Implements:
- Short-lived admin tokens
- Token validation and expiration
- Rate limiting for token requests
- Audit logging of admin access
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from .. import LOGGER
from .config_manager import Config
from .redis_manager import redis_client


class AdminAuthManager:
    """Manage secure admin authentication tokens"""
    
    def __init__(self) -> None:
        self.enabled = bool(getattr(Config, "ENABLE_ADMIN_AUTH", True))
        self.token_ttl_seconds = int(getattr(Config, "ADMIN_TOKEN_TTL_SECONDS", 600))  # 10 min
        self.max_tokens_per_admin = int(getattr(Config, "MAX_ADMIN_TOKENS", 3))
        self.audit_log: Dict[str, list] = {}
    
    def _now(self) -> datetime:
        return datetime.now(timezone.utc)
    
    def _expires_at(self) -> datetime:
        return self._now() + timedelta(seconds=self.token_ttl_seconds)
    
    def _cache_key(self, admin_id: str, token: str) -> str:
        return f"admin_token:{admin_id}:{token}"
    
    def _active_tokens_key(self, admin_id: str) -> str:
        return f"admin_tokens:{admin_id}"
    
    async def create_token(self, admin_id: str) -> Optional[str]:
        """Create a new admin token"""
        if not self.enabled:
            LOGGER.warning("Admin auth is disabled")
            return None
        
        # Check active token limit
        active_key = self._active_tokens_key(admin_id)
        active_count = 0
        if redis_client.is_enabled:
            active_data = await redis_client.get(active_key)
            if active_data:
                active_tokens = active_data.get("tokens", [])
                active_count = len(active_tokens)
        
        if active_count >= self.max_tokens_per_admin:
            LOGGER.warning(f"Admin {admin_id} has too many active tokens ({active_count})")
            return None
        
        # Generate secure token
        token = secrets.token_urlsafe(32)
        expires_at = self._expires_at()
        
        payload = {
            "admin_id": admin_id,
            "created_at": self._now().isoformat(),
            "expires_at": expires_at.isoformat(),
            "ip": getattr(Config, "DEFAULT_IP", "unknown"),
        }
        
        key = self._cache_key(admin_id, token)
        if redis_client.is_enabled:
            await redis_client.set(key, payload, ttl=self.token_ttl_seconds)
            
            # Track active tokens
            active_data = await redis_client.get(active_key) or {"tokens": []}
            active_tokens = active_data.get("tokens", [])
            active_tokens.append(token)
            await redis_client.set(active_key, {"tokens": active_tokens}, ttl=self.token_ttl_seconds)
        
        # Audit log
        self._log_audit("token_created", admin_id, {"token_prefix": token[:10]})
        LOGGER.info(f"Admin token created for {admin_id}: {token[:20]}...")
        
        return token
    
    async def validate_token(self, admin_id: str, token: str) -> bool:
        """Validate an admin token"""
        if not self.enabled:
            return False
        
        key = self._cache_key(admin_id, token)
        payload = None
        
        if redis_client.is_enabled:
            payload = await redis_client.get(key)
        
        if not payload:
            self._log_audit("token_invalid", admin_id, {"reason": "not_found"})
            return False
        
        # Check expiration
        expires_at_str = payload.get("expires_at")
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str)
                if expires_at <= self._now():
                    await self.revoke_token(admin_id, token)
                    self._log_audit("token_expired", admin_id, {})
                    return False
            except ValueError:
                return False
        
        self._log_audit("token_validated", admin_id, {})
        return True
    
    async def revoke_token(self, admin_id: str, token: str) -> bool:
        """Revoke an admin token"""
        if not self.enabled:
            return False
        
        key = self._cache_key(admin_id, token)
        if redis_client.is_enabled:
            await redis_client.delete(key)
        
        # Remove from active tokens list
        active_key = self._active_tokens_key(admin_id)
        active_data = await redis_client.get(active_key) if redis_client.is_enabled else None
        if active_data:
            active_tokens = active_data.get("tokens", [])
            if token in active_tokens:
                active_tokens.remove(token)
                await redis_client.set(active_key, {"tokens": active_tokens}, ttl=self.token_ttl_seconds)
        
        self._log_audit("token_revoked", admin_id, {})
        LOGGER.info(f"Admin token revoked for {admin_id}")
        
        return True
    
    async def revoke_all_tokens(self, admin_id: str) -> bool:
        """Revoke all tokens for an admin"""
        if not self.enabled:
            return False
        
        active_key = self._active_tokens_key(admin_id)
        active_data = await redis_client.get(active_key) if redis_client.is_enabled else None
        
        if active_data:
            active_tokens = active_data.get("tokens", [])
            for token in active_tokens:
                await self.revoke_token(admin_id, token)
        
        if redis_client.is_enabled:
            await redis_client.delete(active_key)
        
        self._log_audit("all_tokens_revoked", admin_id, {})
        LOGGER.info(f"All admin tokens revoked for {admin_id}")
        
        return True
    
    def _log_audit(self, action: str, admin_id: str, details: Dict[str, Any]) -> None:
        """Log audit event"""
        if admin_id not in self.audit_log:
            self.audit_log[admin_id] = []
        
        event = {
            "timestamp": self._now().isoformat(),
            "action": action,
            "details": details,
        }
        self.audit_log[admin_id].append(event)
        
        # Cap audit log size
        if len(self.audit_log[admin_id]) > 1000:
            self.audit_log[admin_id] = self.audit_log[admin_id][-500:]
    
    def get_audit_log(self, admin_id: str) -> list:
        """Get audit log for admin"""
        return self.audit_log.get(admin_id, [])


# Global instance
admin_auth_manager = AdminAuthManager()
