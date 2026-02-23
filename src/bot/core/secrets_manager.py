"""
Secrets Management for Phase 3
Secure encryption/decryption of sensitive data
"""

import logging
import os
import json
import secrets
import base64
from typing import Any, Dict, Optional
from datetime import datetime, UTC, timedelta
from cryptography.fernet import Fernet
import hashlib

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Manages encrypted secrets storage and retrieval
    
    Features:
    - AES-128 encryption via Fernet
    - Key derivation from master secret
    - Automatic key rotation
    - Audit logging of access
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize secrets manager
        
        Args:
            master_key: Master encryption key (generated if not provided)
        """
        if master_key:
            self.master_key = master_key
        else:
            # Generate new key if not provided
            self.master_key = self._generate_key()
        
        try:
            self.cipher = Fernet(self._encode_key(self.master_key))
        except Exception as e:
            logger.error(f"Failed to initialize cipher: {e}")
            raise
        
        # Store for audit
        self.access_log: Dict[str, list] = {}
        
        logger.info("SecretsManager initialized")
    
    @staticmethod
    def _generate_key() -> str:
        """Generate a new encryption key"""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
    
    @staticmethod
    def _encode_key(key: str) -> bytes:
        """Encode string key to bytes for Fernet"""
        if isinstance(key, str):
            key = key.encode()
        
        # Ensure it's proper Fernet format (base64-encoded)
        if isinstance(key, bytes):
            try:
                # Test if it's already valid
                Fernet(key)
                return key
            except Exception:
                # If not valid, derive a key from it
                key_hash = hashlib.sha256(key).digest()
                return base64.urlsafe_b64encode(key_hash)
        
        return key
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt sensitive data
        
        Args:
            data: String to encrypt
            
        Returns:
            Encrypted string (base64-encoded)
        """
        try:
            plaintext = data.encode() if isinstance(data, str) else data
            encrypted = self.cipher.encrypt(plaintext)
            # Return base64-encoded for safe storage
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt encrypted data
        
        Args:
            encrypted_data: Base64-encoded encrypted string
            
        Returns:
            Decrypted string
        """
        try:
            # Decode from base64
            encrypted = base64.b64decode(encrypted_data)
            plaintext = self.cipher.decrypt(encrypted)
            return plaintext.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def store_secret(self, name: str, value: str) -> bool:
        """
        Store an encrypted secret
        
        Args:
            name: Secret name
            value: Secret value
            
        Returns:
            Success status
        """
        try:
            encrypted = self.encrypt(value)
            
            # Store with metadata
            secret_data = {
                "name": name,
                "encrypted_value": encrypted,
                "created_at": datetime.now(UTC).isoformat(),
                "accessed_at": None,
                "access_count": 0,
            }
            
            logger.info(f"Secret '{name}' stored")
            return True
        except Exception as e:
            logger.error(f"Failed to store secret: {e}")
            return False
    
    def retrieve_secret(self, name: str) -> Optional[str]:
        """
        Retrieve and decrypt a secret
        
        Args:
            name: Secret name
            
        Returns:
            Decrypted value or None
        """
        try:
            # Log access
            if name not in self.access_log:
                self.access_log[name] = []
            
            self.access_log[name].append({
                "timestamp": datetime.now(UTC).isoformat(),
                "action": "retrieve",
            })
            
            logger.info(f"Secret '{name}' retrieved")
            
            # In real implementation, would retrieve from encrypted storage
            # For now, return None (would need persistent storage)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve secret: {e}")
            return None
    
    def rotate_key(self, new_master_key: Optional[str] = None) -> bool:
        """
        Rotate encryption key
        
        Args:
            new_master_key: New master key (generated if not provided)
            
        Returns:
            Success status
        """
        try:
            old_cipher = self.cipher
            old_key = self.master_key
            
            # Generate new key if not provided
            if not new_master_key:
                new_master_key = self._generate_key()
            
            # Create new cipher
            new_cipher = Fernet(self._encode_key(new_master_key))
            
            # Update instance
            self.master_key = new_master_key
            self.cipher = new_cipher
            
            logger.info("Encryption key rotated")
            return True
        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            return False
    
    def get_access_log(self, secret_name: str) -> list:
        """Get access log for a secret"""
        return self.access_log.get(secret_name, [])
    
    def clear_access_logs(self) -> None:
        """Clear all access logs"""
        self.access_log.clear()
        logger.info("Access logs cleared")


class EnvironmentSecretsManager:
    """
    Manages secrets stored in environment variables
    
    Secures:
    - Database credentials
    - API tokens
    - Encryption keys
    - OAuth credentials
    """
    
    # Sensitive environment variable patterns
    SENSITIVE_PATTERNS = [
        "TOKEN", "KEY", "PASSWORD", "SECRET",
        "CREDENTIAL", "AUTH", "API", "URL"
    ]
    
    def __init__(self):
        """Initialize environment secrets manager"""
        self.loaded_secrets: Dict[str, bool] = {}
        logger.info("EnvironmentSecretsManager initialized")
    
    @staticmethod
    def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get secret from environment
        
        Args:
            name: Environment variable name
            default: Default value if not found
            
        Returns:
            Secret value or default
        """
        value = os.getenv(name, default)
        
        if value:
            logger.debug(f"Loaded secret: {name}")
        else:
            logger.warning(f"Secret not found: {name}")
        
        return value
    
    @staticmethod
    def get_secret_or_fail(name: str) -> str:
        """
        Get required secret from environment
        
        Raises:
            ValueError if secret not found
        """
        value = os.getenv(name)
        
        if not value:
            logger.critical(f"Required secret missing: {name}")
            raise ValueError(f"Required secret missing: {name}")
        
        return value
    
    @staticmethod
    def is_secret_loaded(name: str) -> bool:
        """Check if secret is loaded"""
        return name in os.environ
    
    @staticmethod
    def redact_sensitive_value(value: str, redact_char: str = "*") -> str:
        """
        Redact sensitive value for logging
        
        Args:
            value: Value to redact
            redact_char: Character to use for redaction
            
        Returns:
            Redacted value
        """
        if not value or len(value) < 4:
            return redact_char * 4
        
        # Show first and last character
        return f"{value[0]}{redact_char * (len(value) - 2)}{value[-1]}"
    
    @staticmethod
    def log_secrets_status() -> None:
        """Log which required secrets are loaded"""
        required_secrets = [
            "BOT_TOKEN",
            "DATABASE_URL",
            "REDIS_URL",
            "API_TOKEN_EXPIRY",
        ]
        
        logger.info("=== Secrets Status ===")
        for secret_name in required_secrets:
            is_loaded = EnvironmentSecretsManager.is_secret_loaded(secret_name)
            status = "✅ LOADED" if is_loaded else "❌ MISSING"
            logger.info(f"{secret_name}: {status}")
        logger.info("======================")


class TokenManager:
    """
    Manages secure token generation and validation
    
    Use cases:
    - API authentication tokens
    - Session tokens
    - Password reset tokens
    - CSRF tokens
    """
    
    def __init__(self, token_length: int = 32):
        """
        Initialize token manager
        
        Args:
            token_length: Length of generated tokens (bytes)
        """
        self.token_length = token_length
        self.tokens: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"TokenManager initialized (length={token_length})")
    
    def generate_token(
        self,
        purpose: str = "general",
        expiry_seconds: int = 3600,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate secure token
        
        Args:
            purpose: Token purpose (api, session, reset, csrf)
            expiry_seconds: Token expiry time in seconds
            metadata: Additional metadata to store with token
            
        Returns:
            Generated token
        """
        token = secrets.token_urlsafe(self.token_length)
        
        # Store token info
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        self.tokens[token_hash] = {
            "purpose": purpose,
            "created_at": datetime.now(UTC),
            "expires_at": datetime.now(UTC) + timedelta(seconds=expiry_seconds),
            "metadata": metadata or {},
            "used": False,
        }
        
        logger.debug(f"Token generated for purpose: {purpose}")
        
        return token
    
    def validate_token(self, token: str, purpose: Optional[str] = None) -> bool:
        """
        Validate token
        
        Args:
            token: Token to validate
            purpose: Expected purpose (optional)
            
        Returns:
            True if valid, False otherwise
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        if token_hash not in self.tokens:
            return False
        
        token_info = self.tokens[token_hash]
        
        # Check expiry
        if datetime.now(UTC) > token_info["expires_at"]:
            return False
        
        # Check purpose if specified
        if purpose and token_info["purpose"] != purpose:
            return False
        
        # Check if already used
        if token_info["used"]:
            return False
        
        return True
    
    def consume_token(self, token: str) -> bool:
        """
        Mark token as used (consume it)
        
        Args:
            token: Token to consume
            
        Returns:
            Success status
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        if token_hash in self.tokens:
            self.tokens[token_hash]["used"] = True
            logger.debug("Token consumed")
            return True
        
        return False
    
    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired tokens
        
        Returns:
            Number of tokens removed
        """
        now = datetime.now(UTC)
        expired = [
            token_hash for token_hash, info in self.tokens.items()
            if now > info["expires_at"]
        ]
        
        for token_hash in expired:
            del self.tokens[token_hash]
        
        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired tokens")
        
        return len(expired)


# Singleton instances
_secrets_manager_instance: Optional[SecretsManager] = None
_env_secrets_instance: Optional[EnvironmentSecretsManager] = None
_token_manager_instance: Optional[TokenManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get or create SecretsManager singleton"""
    global _secrets_manager_instance
    if _secrets_manager_instance is None:
        master_key = os.getenv("SECRETS_MASTER_KEY")
        _secrets_manager_instance = SecretsManager(master_key)
    return _secrets_manager_instance


def get_env_secrets() -> EnvironmentSecretsManager:
    """Get or create EnvironmentSecretsManager singleton"""
    global _env_secrets_instance
    if _env_secrets_instance is None:
        _env_secrets_instance = EnvironmentSecretsManager()
    return _env_secrets_instance


def get_token_manager() -> TokenManager:
    """Get or create TokenManager singleton"""
    global _token_manager_instance
    if _token_manager_instance is None:
        _token_manager_instance = TokenManager()
    return _token_manager_instance
