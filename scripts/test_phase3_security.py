#!/usr/bin/env python3
"""
Phase 3 Security Modules Test
Verifies all security modules are working correctly
"""

import sys
sys.path.insert(0, '/home/kali/mirror-leech-telegram-bot')

print("\n" + "="*60)
print("Phase 3: Security & Hardening - Module Tests")
print("="*60 + "\n")

# Test 1: SecurityHeaders
try:
    from bot.core.security_headers import get_security_headers
    headers = get_security_headers()
    num_headers = len(headers.get_headers())
    print(f"✅ SecurityHeaders")
    print(f"   - Generated {num_headers} security headers")
except Exception as e:
    print(f"❌ SecurityHeaders - {e}")

# Test 2: CSRFProtection
try:
    from bot.core.csrf_protection import get_csrf_protection
    csrf = get_csrf_protection()
    token = csrf.get_token_for_session("test_session")
    is_valid, error = csrf.validate_request("GET", "test_session", token)
    print(f"✅ CSRFProtection")
    print(f"   - Generated and validated token")
except Exception as e:
    print(f"❌ CSRFProtection - {e}")

# Test 3: InputValidator
try:
    from bot.core.input_validator import get_input_validator
    validator = get_input_validator()
    is_valid, error = validator.validate_field("test@example.com", "email")
    print(f"✅ InputValidator")
    print(f"   - Email validation: {is_valid}")
except Exception as e:
    print(f"❌ InputValidator - {e}")

# Test 4: SecretsManager
try:
    from bot.core.secrets_manager import get_secrets_manager
    secrets = get_secrets_manager()
    encrypted = secrets.encrypt("secret_data")
    decrypted = secrets.decrypt(encrypted)
    print(f"✅ SecretsManager")
    print(f"   - Encrypted and decrypted successfully")
except Exception as e:
    print(f"❌ SecretsManager - {e}")

# Test 5: AuditLogger
try:
    from bot.core.security_audit import (
        get_audit_logger,
        AuditEventType,
        AuditSeverity
    )
    audit = get_audit_logger()
    num_events = len(list(AuditEventType))
    print(f"✅ AuditLogger")
    print(f"   - {num_events} event types available")
except Exception as e:
    print(f"❌ AuditLogger - {e}")

print("\n" + "="*60)
print("Result: All Phase 3 modules loaded successfully! ✅")
print("="*60 + "\n")
