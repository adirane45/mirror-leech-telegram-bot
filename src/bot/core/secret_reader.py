#!/usr/bin/env python3
"""
Secret Reader - Load secrets from multiple sources

Supports:
1. Docker Secrets (mounted at /run/secrets/)
2. Kubernetes Secrets (as environment variables)
3. Direct environment variables
4. File paths (.env files as fallback)

Implements in order of preference:
1. <VAR>_FILE environment variable (points to secret file)
2. Direct <VAR> environment variable
3. /run/secrets/<var_lower> (Docker Secrets mount)
4. .env file values (fallback only)

Usage:
    from bot.core.secret_reader import SecretReader
    
    # Get required secret (raises if not found)
    bot_token = SecretReader.get_secret("BOT_TOKEN")
    
    # Get optional secret (returns None if not found)
    custom_value = SecretReader.get_optional_secret("CUSTOM_VAR", default="default")
    
    # Validate all required secrets are available
    found, missing = SecretReader.validate_secrets([
        "BOT_TOKEN",
        "DATABASE_URL",
        "REDIS_PASSWORD"
    ])
    if not found:
        raise RuntimeError(f"Missing secrets: {missing}")
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, UTC

from .. import LOGGER


class SecretReader:
    """
    Read secrets from environment or mounted secret files
    
    Priority:
    1. ${VAR}_FILE environment variable (Docker Swarm pattern)
    2. ${VAR} direct environment variable (K8s / .env)
    3. /run/secrets/${var_lower} (Docker mount)
    4. ValueError if not found
    
    Example:
        BOT_TOKEN = SecretReader.get_secret("BOT_TOKEN")
        # Tries in order:
        # 1. $BOT_TOKEN_FILE (file path)
        # 2. $BOT_TOKEN (value)
        # 3. /run/secrets/bot_token (Docker)
        # 4. Raise error
    """
    
    @staticmethod
    def get_secret(
        var_name: str,
        default: Optional[str] = None,
        allow_empty: bool = False
    ) -> str:
        """
        Get secret from multiple sources
        
        Args:
            var_name: Environment variable name (e.g., "BOT_TOKEN")
            default: Default value if not found
            allow_empty: If True, empty strings are valid values
        
        Returns:
            Secret value
        
        Raises:
            ValueError: If secret not found and no default
        """
        # Strategy 1: Check _FILE variant (Docker Swarm convention)
        file_var = f"{var_name}_FILE"
        if file_var in os.environ:
            file_path = os.environ[file_var]
            try:
                with open(file_path, 'r') as f:
                    value = f.read().strip()
                    if value or allow_empty:
                        LOGGER.debug(f"✓ Loaded {var_name} from file: {file_path}")
                        return value
            except IOError as e:
                LOGGER.warning(f"⚠️  Could not read secret file {file_path}: {e}")
        
        # Strategy 2: Direct environment variable (K8s or .env)
        if var_name in os.environ:
            value = os.environ[var_name]
            if value or allow_empty:
                LOGGER.debug(f"✓ Loaded {var_name} from environment")
                return value
        
        # Strategy 3: Docker Secrets mount point
        secret_file = Path(f"/run/secrets/{var_name.lower()}")
        if secret_file.exists():
            try:
                with open(secret_file, 'r') as f:
                    value = f.read().strip()
                    if value or allow_empty:
                        LOGGER.debug(f"✓ Loaded {var_name} from Docker secret")
                        return value
            except IOError as e:
                LOGGER.warning(f"⚠️  Could not read Docker secret {secret_file}: {e}")
        
        # Strategy 4: Default value
        if default is not None:
            LOGGER.warning(f"⚠️  Using default for {var_name}")
            return default
        
        # Not found
        raise ValueError(
            f"Secret '{var_name}' not found in:\n"
            f"  - ${var_name}_FILE (file path)\n"
            f"  - ${var_name} (environment)\n"
            f"  - /run/secrets/{var_name.lower()} (Docker)\n"
            f"  - default value"
        )
    
    @staticmethod
    def get_optional_secret(var_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get optional secret (returns None if not found)
        
        Args:
            var_name: Environment variable name
            default: Default value if not found
        
        Returns:
            Secret value or default/None
        """
        try:
            return SecretReader.get_secret(var_name)
        except ValueError:
            return default
    
    @staticmethod
    def get_all_secrets(prefix: str = "") -> Dict[str, str]:
        """
        Get all secrets matching a prefix
        
        Example:
            secrets = SecretReader.get_all_secrets("TELEGRAM_")
            # Returns: {"API": "xxx", "HASH": "yyy", "BOT_TOKEN": "zzz"}
        
        Args:
            prefix: Variable prefix to filter (optional)
        
        Returns:
            Dictionary of var_name: value pairs
        """
        secrets = {}
        
        for key, value in os.environ.items():
            if prefix and not key.startswith(prefix):
                continue
            
            # Skip _FILE variants (already processed)
            if key.endswith("_FILE"):
                continue
            
            # Skip tech vars
            if key in ("PATH", "HOME", "USER", "PWD"):
                continue
            
            try:
                secrets[key] = SecretReader.get_secret(key)
            except ValueError:
                pass
        
        return secrets
    
    @staticmethod
    def validate_secrets(required: list) -> tuple:
        """
        Validate that all required secrets are available
        
        Args:
            required: List of required secret names
        
        Returns:
            (all_found: bool, missing: list[str])
        
        Example:
            found, missing = SecretReader.validate_secrets([
                "BOT_TOKEN",
                "DATABASE_URL",
                "REDIS_PASSWORD"
            ])
            if not found:
                raise ValueError(f"Missing secrets: {missing}")
        """
        missing = []
        for secret_name in required:
            try:
                SecretReader.get_secret(secret_name)
            except ValueError:
                missing.append(secret_name)
        
        return len(missing) == 0, missing
    
    @staticmethod
    def health_check() -> Dict[str, Any]:
        """
        Check secret loading health
        
        Returns:
            Health status dictionary
        """
        status = {
            'timestamp': datetime.now(UTC).isoformat(),
            'sources': {},
            'errors': []
        }
        
        # Check Docker Secrets mount
        docker_secrets_path = Path("/run/secrets")
        if docker_secrets_path.exists():
            try:
                secrets_list = list(docker_secrets_path.glob("*"))
                status['sources']['docker_secrets'] = {
                    'available': True,
                    'count': len(secrets_list)
                }
            except Exception as e:
                status['sources']['docker_secrets'] = {'available': False, 'error': str(e)}
                status['errors'].append(f"Docker Secrets: {e}")
        else:
            status['sources']['docker_secrets'] = {'available': False}
        
        # Check environment variables
        env_count = sum(1 for k in os.environ.keys() if not k.startswith('_'))
        status['sources']['environment'] = {
            'available': True,
            'count': env_count
        }
        
        # Check .env files
        env_files = [
            Path(".env"),
            Path(".env.local"),
            Path("config/.env"),
            Path("config/.env.production")
        ]
        available_env_files = [f for f in env_files if f.exists()]
        status['sources']['env_files'] = {
            'available': len(available_env_files) > 0,
            'count': len(available_env_files),
            'files': [str(f) for f in available_env_files]
        }
        
        return status


__all__ = ['SecretReader']
