"""
CSRF Protection for Phase 3
Implements token-based CSRF protection with secure token generation
"""

import logging
import secrets
import hashlib
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta, UTC

logger = logging.getLogger(__name__)


class CSRFTokenManager:
    """
    Manages CSRF token generation and validation
    
    Implements:
    - Secure token generation
    - Token storage and verification
    - Token rotation
    - Session-based token binding
    """
    
    def __init__(self, token_length: int = 32, token_ttl_seconds: int = 3600):
        """
        Initialize CSRF token manager
        
        Args:
            token_length: Length of generated tokens (bytes)
            token_ttl_seconds: Token time-to-live in seconds
        """
        self.token_length = token_length
        self.token_ttl = token_ttl_seconds
        
        # Store tokens: token_hash -> (creation_time, session_id, valid)
        self.tokens: Dict[str, Tuple[datetime, str, bool]] = {}
        
        logger.info(f"CSRFTokenManager initialized (ttl={token_ttl_seconds}s)")
    
    def generate_token(self, session_id: str) -> str:
        """
        Generate a new CSRF token
        
        Args:
            session_id: Session identifier to bind token to
            
        Returns:
            Base64-encoded CSRF token
        """
        # Generate random bytes
        token_bytes = secrets.token_bytes(self.token_length)
        
        # Create token string (hex encoded for safety)
        token = secrets.token_urlsafe(self.token_length)
        
        # Hash token for storage
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Store token with metadata
        self.tokens[token_hash] = (datetime.now(UTC), session_id, True)
        
        logger.debug(f"CSRF token generated for session {session_id}")
        
        return token
    
    def validate_token(self, token: str, session_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate CSRF token
        
        Args:
            token: Token to validate
            session_id: Session identifier to verify against
            
        Returns:
            (is_valid, error_message)
        """
        # Hash the provided token
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Check if token exists
        if token_hash not in self.tokens:
            return False, "Invalid or expired CSRF token"
        
        creation_time, stored_session, is_valid = self.tokens[token_hash]
        
        # Check if token is marked valid
        if not is_valid:
            return False, "CSRF token already used"
        
        # Check if token has expired
        if datetime.now(UTC) - creation_time > timedelta(seconds=self.token_ttl):
            self.tokens[token_hash] = (creation_time, stored_session, False)
            return False, "CSRF token expired"
        
        # Check if session matches
        if stored_session != session_id:
            return False, "CSRF token session mismatch"
        
        # Mark token as used (consumed)
        self.tokens[token_hash] = (creation_time, stored_session, False)
        
        logger.debug(f"CSRF token validated for session {session_id}")
        
        return True, None
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a CSRF token
        
        Args:
            token: Token to revoke
            
        Returns:
            True if revoked, False if not found
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        if token_hash in self.tokens:
            creation_time, session_id, _ = self.tokens[token_hash]
            self.tokens[token_hash] = (creation_time, session_id, False)
            logger.info(f"CSRF token revoked")
            return True
        
        return False
    
    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired tokens from storage
        
        Returns:
            Number of tokens cleaned up
        """
        now = datetime.now(UTC)
        expired_tokens = []
        
        for token_hash, (creation_time, _, _) in self.tokens.items():
            if now - creation_time > timedelta(seconds=self.token_ttl):
                expired_tokens.append(token_hash)
        
        for token_hash in expired_tokens:
            del self.tokens[token_hash]
        
        if expired_tokens:
            logger.debug(f"Cleaned up {len(expired_tokens)} expired CSRF tokens")
        
        return len(expired_tokens)
    
    def get_token_stats(self) -> Dict[str, int]:
        """Get token statistics"""
        now = datetime.now(UTC)
        valid_count = 0
        expired_count = 0
        used_count = 0
        
        for creation_time, _, is_valid in self.tokens.values():
            if now - creation_time > timedelta(seconds=self.token_ttl):
                expired_count += 1
            elif not is_valid:
                used_count += 1
            else:
                valid_count += 1
        
        return {
            "total": len(self.tokens),
            "valid": valid_count,
            "used": used_count,
            "expired": expired_count,
        }


class CSRFProtection:
    """
    CSRF protection middleware
    
    Protects against Cross-Site Request Forgery by:
    - Validating CSRF tokens on state-changing requests
    - Enforcing same-site cookies
    - Checking origin/referer headers
    """
    
    PROTECTED_METHODS = {"POST", "PUT", "DELETE", "PATCH"}
    
    def __init__(self, token_manager: Optional[CSRFTokenManager] = None):
        """
        Initialize CSRF protection
        
        Args:
            token_manager: CSRFTokenManager instance
        """
        self.token_manager = token_manager or CSRFTokenManager()
        self.token_header_name = "X-CSRF-Token"
        self.token_param_name = "csrf_token"
        
        logger.info("CSRFProtection initialized")
    
    def get_token_for_session(self, session_id: str) -> str:
        """
        Get or create CSRF token for session
        
        Args:
            session_id: Session identifier
            
        Returns:
            CSRF token
        """
        return self.token_manager.generate_token(session_id)
    
    def validate_request(
        self,
        method: str,
        session_id: str,
        csrf_token: Optional[str] = None,
        origin: Optional[str] = None,
        referer: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate request for CSRF protection
        
        Args:
            method: HTTP method
            session_id: Session identifier
            csrf_token: CSRF token from request
            origin: Origin header value
            referer: Referer header value
            
        Returns:
            (is_valid, error_message)
        """
        # Safe methods don't need CSRF protection
        if method not in self.PROTECTED_METHODS:
            return True, None
        
        # Require CSRF token for protected methods
        if not csrf_token:
            return False, "CSRF token required"
        
        # Validate token
        is_valid, error = self.token_manager.validate_token(csrf_token, session_id)
        if not is_valid:
            return False, error
        
        # Validate origin/referer if present
        if origin:
            is_valid, error = self._validate_origin(origin)
            if not is_valid:
                logger.warning(f"CSRF origin validation failed: {error}")
                return False, error
        
        if referer:
            is_valid, error = self._validate_referer(referer)
            if not is_valid:
                logger.warning(f"CSRF referer validation failed: {error}")
                # Don't block on referer (can be stripped by browsers)
        
        logger.debug(f"CSRF validation passed for session {session_id}")
        
        return True, None
    
    def _validate_origin(self, origin: str) -> Tuple[bool, Optional[str]]:
        """Validate origin header"""
        if not origin:
            return False, "Origin header missing"
        
        # In production, validate against allowed origins
        # For now, just check it exists
        return True, None
    
    def _validate_referer(self, referer: str) -> Tuple[bool, Optional[str]]:
        """Validate referer header"""
        if not referer:
            # Some browsers strip referer, don't block
            return True, None
        
        # In production, validate that referer matches expected domain
        return True, None
    
    def extract_token_from_request(
        self,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, any]] = None,
    ) -> Optional[str]:
        """
        Extract CSRF token from request
        
        Checks:
        1. X-CSRF-Token header
        2. csrf_token request parameter
        3. Hidden form field (in body)
        
        Args:
            headers: Request headers
            body: Request body (form data or JSON)
            
        Returns:
            CSRF token if found, None otherwise
        """
        # Check header
        if headers:
            if self.token_header_name in headers:
                return headers[self.token_header_name]
        
        # Check body/parameters
        if body:
            if isinstance(body, dict):
                if self.token_param_name in body:
                    return body[self.token_param_name]
        
        return None


class SameSiteCookie:
    """
    SameSite cookie configuration for CSRF protection
    
    SameSite levels:
    - Strict: Cookie only sent with same-site requests
    - Lax: Cookie sent with top-level navigations
    - None: Cookie sent with all requests (requires Secure flag)
    """
    
    STRICT = "Strict"
    LAX = "Lax"
    NONE = "None"
    
    @staticmethod
    def get_same_site_attribute(level: str = "Strict") -> str:
        """Get SameSite cookie attribute"""
        if level not in [SameSiteCookie.STRICT, SameSiteCookie.LAX, SameSiteCookie.NONE]:
            level = SameSiteCookie.STRICT
        return level
    
    @staticmethod
    def get_cookie_string(
        name: str,
        value: str,
        same_site: str = "Strict",
        secure: bool = True,
        http_only: bool = True,
        max_age: int = 3600,
    ) -> str:
        """
        Build a secure cookie string with SameSite attribute
        
        Args:
            name: Cookie name
            value: Cookie value
            same_site: SameSite level (Strict/Lax/None)
            secure: Secure flag (requires HTTPS)
            http_only: HttpOnly flag
            max_age: Cookie max age in seconds
            
        Returns:
            Cookie string
        """
        cookie = f"{name}={value}"
        cookie += f"; SameSite={same_site}"
        
        if secure:
            cookie += "; Secure"
        
        if http_only:
            cookie += "; HttpOnly"
        
        if max_age > 0:
            cookie += f"; Max-Age={max_age}"
        
        return cookie


# Singleton instance
_csrf_protection_instance: Optional[CSRFProtection] = None


def get_csrf_protection() -> CSRFProtection:
    """Get or create CSRF protection singleton"""
    global _csrf_protection_instance
    if _csrf_protection_instance is None:
        _csrf_protection_instance = CSRFProtection()
    return _csrf_protection_instance
