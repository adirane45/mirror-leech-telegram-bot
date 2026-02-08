"""
Phase 5: Multi-Factor Authentication (MFA) Manager
Provides TOTP-based two-factor authentication for enhanced security
"""

import pyotp
import qrcode
import io
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, UTC
from dataclasses import dataclass, field
import secrets
import string
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class MFADevice:
    """MFA device (TOTP authenticator)"""
    device_id: str
    user_id: str
    device_name: str
    secret: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_used: Optional[datetime] = None
    is_verified: bool = False
    backup_codes: List[str] = field(default_factory=list)


@dataclass
class MFASession:
    """MFA session tracking"""
    session_id: str
    user_id: str
    device_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = field(default_factory=lambda: datetime.now(UTC) + timedelta(hours=24))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class MFAManager:
    """
    Multi-Factor Authentication Manager
    
    Features:
    - TOTP-based 2FA (Google Authenticator, Authy compatible)
    - Backup code generation and validation
    - Device management (multiple devices per user)
    - Session management with MFA verification
    - QR code generation for easy setup
    
    Usage:
        mfa = MFAManager()
        
        # Enroll user
        secret, qr_code = mfa.enroll_user(user_id="123", device_name="iPhone")
        
        # Verify TOTP code
        is_valid = mfa.verify_totp(user_id="123", code="123456")
        
        # Generate backup codes
        codes = mfa.generate_backup_codes(user_id="123")
    """
    
    def __init__(self, issuer_name: str = "MirrorBot"):
        self.issuer_name = issuer_name
        self.devices: Dict[str, MFADevice] = {}  # device_id -> MFADevice
        self.user_devices: Dict[str, List[str]] = {}  # user_id -> [device_ids]
        self.sessions: Dict[str, MFASession] = {}  # session_id -> MFASession
        self.used_backup_codes: Dict[str, List[str]] = {}  # user_id -> [used_codes]
        
        logger.info(f"MFAManager initialized (issuer={issuer_name})")
    
    # ========================================================================
    # ENROLLMENT
    # ========================================================================
    
    def enroll_user(
        self,
        user_id: str,
        device_name: str = "Authenticator",
        email: Optional[str] = None
    ) -> tuple[str, str, List[str]]:
        """
        Enroll user for MFA
        
        Returns:
            (secret, qr_code_base64, backup_codes)
        """
        try:
            # Generate secret
            secret = pyotp.random_base32()
            
            # Generate device ID
            device_id = self._generate_device_id()
            
            # Generate backup codes
            backup_codes = self._generate_backup_codes()
            
            # Create device
            device = MFADevice(
                device_id=device_id,
                user_id=user_id,
                device_name=device_name,
                secret=secret,
                backup_codes=backup_codes
            )
            
            # Store device
            self.devices[device_id] = device
            if user_id not in self.user_devices:
                self.user_devices[user_id] = []
            self.user_devices[user_id].append(device_id)
            
            # Generate QR code
            account_name = email or user_id
            qr_code = self._generate_qr_code(secret, account_name)
            
            logger.info(f"User enrolled: user_id={user_id}, device={device_name}")
            
            return secret, qr_code, backup_codes
            
        except Exception as e:
            logger.error(f"Enrollment failed: {e}")
            raise
    
    def _generate_device_id(self) -> str:
        """Generate unique device ID"""
        return secrets.token_urlsafe(16)
    
    def _generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes"""
        codes = []
        for _ in range(count):
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            codes.append(f"{code[:4]}-{code[4:]}")
        return codes
    
    def _generate_qr_code(self, secret: str, account_name: str) -> str:
        """
        Generate QR code for TOTP setup
        
        Returns:
            Base64-encoded PNG image
        """
        try:
            # Create TOTP URI
            totp = pyotp.TOTP(secret)
            uri = totp.provisioning_uri(
                name=account_name,
                issuer_name=self.issuer_name
            )
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(uri)
            qr.make(fit=True)
            
            # Convert to image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            qr_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            
            return qr_base64
            
        except Exception as e:
            logger.error(f"QR code generation failed: {e}")
            raise
    
    # ========================================================================
    # VERIFICATION
    # ========================================================================
    
    def verify_totp(
        self,
        user_id: str,
        code: str,
        device_id: Optional[str] = None
    ) -> bool:
        """
        Verify TOTP code
        
        Args:
            user_id: User ID
            code: 6-digit TOTP code
            device_id: Specific device to verify (optional)
        
        Returns:
            True if valid
        """
        try:
            # Get user devices
            if user_id not in self.user_devices:
                logger.warning(f"User not enrolled: {user_id}")
                return False
            
            device_ids = self.user_devices[user_id]
            if device_id:
                device_ids = [device_id] if device_id in device_ids else []
            
            # Try each device
            for dev_id in device_ids:
                device = self.devices.get(dev_id)
                if not device:
                    continue
                
                # Verify TOTP
                totp = pyotp.TOTP(device.secret)
                if totp.verify(code, valid_window=1):  # Allow 30s window
                    device.last_used = datetime.now(UTC)
                    device.is_verified = True
                    logger.info(f"TOTP verified: user={user_id}, device={device.device_name}")
                    return True
            
            logger.warning(f"TOTP verification failed: user={user_id}")
            return False
            
        except Exception as e:
            logger.error(f"TOTP verification error: {e}")
            return False
    
    def verify_backup_code(self, user_id: str, code: str) -> bool:
        """
        Verify backup code
        
        Backup codes are single-use only
        """
        try:
            # Get user devices
            if user_id not in self.user_devices:
                return False
            
            # Check each device
            for device_id in self.user_devices[user_id]:
                device = self.devices.get(device_id)
                if not device:
                    continue
                
                # Check if code exists and not used
                if code in device.backup_codes:
                    # Check if already used
                    if user_id in self.used_backup_codes and code in self.used_backup_codes[user_id]:
                        logger.warning(f"Backup code already used: user={user_id}")
                        return False
                    
                    # Mark as used
                    if user_id not in self.used_backup_codes:
                        self.used_backup_codes[user_id] = []
                    self.used_backup_codes[user_id].append(code)
                    
                    device.last_used = datetime.now(UTC)
                    logger.info(f"Backup code verified: user={user_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Backup code verification error: {e}")
            return False
    
    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================
    
    def create_session(
        self,
        user_id: str,
        device_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        duration_hours: int = 24
    ) -> str:
        """
        Create MFA-verified session
        
        Returns:
            session_id
        """
        try:
            session_id = secrets.token_urlsafe(32)
            
            session = MFASession(
                session_id=session_id,
                user_id=user_id,
                device_id=device_id,
                created_at=datetime.now(UTC),
                expires_at=datetime.now(UTC) + timedelta(hours=duration_hours),
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            self.sessions[session_id] = session
            
            logger.info(f"MFA session created: user={user_id}, expires_in={duration_hours}h")
            
            return session_id
            
        except Exception as e:
            logger.error(f"Session creation error: {e}")
            raise
    
    def validate_session(self, session_id: str) -> bool:
        """Validate MFA session"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            # Check expiration
            if datetime.now(UTC) > session.expires_at:
                logger.info(f"Session expired: {session_id}")
                del self.sessions[session_id]
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return False
    
    def revoke_session(self, session_id: str) -> bool:
        """Revoke MFA session"""
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Session revoked: {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Session revocation error: {e}")
            return False
    
    # ========================================================================
    # DEVICE MANAGEMENT
    # ========================================================================
    
    def list_user_devices(self, user_id: str) -> List[Dict[str, Any]]:
        """List all devices for user"""
        try:
            if user_id not in self.user_devices:
                return []
            
            devices = []
            for device_id in self.user_devices[user_id]:
                device = self.devices.get(device_id)
                if device:
                    devices.append({
                        'device_id': device.device_id,
                        'device_name': device.device_name,
                        'created_at': device.created_at.isoformat(),
                        'last_used': device.last_used.isoformat() if device.last_used else None,
                        'is_verified': device.is_verified
                    })
            
            return devices
            
        except Exception as e:
            logger.error(f"Device listing error: {e}")
            return []
    
    def remove_device(self, user_id: str, device_id: str) -> bool:
        """Remove MFA device"""
        try:
            if user_id in self.user_devices and device_id in self.user_devices[user_id]:
                self.user_devices[user_id].remove(device_id)
                if device_id in self.devices:
                    del self.devices[device_id]
                logger.info(f"Device removed: user={user_id}, device={device_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Device removal error: {e}")
            return False
    
    def regenerate_backup_codes(self, user_id: str, device_id: str) -> List[str]:
        """Regenerate backup codes for device"""
        try:
            device = self.devices.get(device_id)
            if not device or device.user_id != user_id:
                raise ValueError("Invalid device")
            
            # Generate new codes
            new_codes = self._generate_backup_codes()
            device.backup_codes = new_codes
            
            # Clear used codes for this user
            if user_id in self.used_backup_codes:
                self.used_backup_codes[user_id] = []
            
            logger.info(f"Backup codes regenerated: user={user_id}")
            
            return new_codes
            
        except Exception as e:
            logger.error(f"Backup code regeneration error: {e}")
            raise
    
    # ========================================================================
    # STATISTICS
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get MFA statistics"""
        try:
            total_users = len(self.user_devices)
            total_devices = len(self.devices)
            active_sessions = len([s for s in self.sessions.values() if datetime.now(UTC) <= s.expires_at])
            verified_devices = len([d for d in self.devices.values() if d.is_verified])
            
            return {
                'total_users': total_users,
                'total_devices': total_devices,
                'verified_devices': verified_devices,
                'active_sessions': active_sessions,
                'devices_per_user': total_devices / total_users if total_users > 0 else 0
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {}


# ============================================================================
# SINGLETON
# ============================================================================

_mfa_manager: Optional[MFAManager] = None


def get_mfa_manager(issuer_name: str = "MirrorBot") -> MFAManager:
    """Get MFA manager singleton"""
    global _mfa_manager
    if _mfa_manager is None:
        _mfa_manager = MFAManager(issuer_name=issuer_name)
    return _mfa_manager
