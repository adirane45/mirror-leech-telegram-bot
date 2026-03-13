"""Admin authentication and JWT token management"""
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, cast

from fastapi import HTTPException, status
from jwt import ExpiredSignatureError, InvalidTokenError, decode, encode
from passlib.context import CryptContext

# JWT Configuration
SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AdminAuth:
    """Handle admin authentication"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return cast(str, pwd_context.hash(password))

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return cast(bool, pwd_context.verify(plain_password, hashed_password))

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

        to_encode.update({"exp": expire})
        encoded_jwt = encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify JWT token and return payload"""
        try:
            payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )


# Default admin credentials (from env or hardcoded for first setup)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
_ADMIN_PASSWORD_PLAIN = os.getenv("ADMIN_PASSWORD", "admin123")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")

# Store admin credentials (in production, use database)
def get_admin_credentials() -> Dict[str, str]:
    """Get admin credentials with lazy password hashing"""
    global ADMIN_PASSWORD_HASH
    if not ADMIN_PASSWORD_HASH:
        ADMIN_PASSWORD_HASH = AdminAuth.hash_password(_ADMIN_PASSWORD_PLAIN)
    return {
        ADMIN_USERNAME: ADMIN_PASSWORD_HASH
    }
