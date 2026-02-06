#!/usr/bin/env python3
"""
Configuration Verification Script for MLTB Bot
Validates that config.py has all required settings for deployment
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_required_settings():
    """Check if all required config settings exist"""
    try:
        from config import (
            BOT_TOKEN, OWNER_ID, TELEGRAM_API, TELEGRAM_HASH,
            MONGODB_URL, REDIS_HOST, REDIS_PORT,
            GRAPHQL_ENDPOINT, CELERY_BROKER_URL,
            API_HOST, API_PORT, ENVIRONMENT
        )
        
        checks = {
            "BOT_TOKEN": BOT_TOKEN and len(BOT_TOKEN) > 10,
            "OWNER_ID": OWNER_ID and OWNER_ID > 0,
            "TELEGRAM_API": TELEGRAM_API and TELEGRAM_API > 0,
            "TELEGRAM_HASH": TELEGRAM_HASH and len(TELEGRAM_HASH) > 0,
            "MONGODB_URL": MONGODB_URL and "mongodb" in MONGODB_URL,
            "REDIS_HOST": REDIS_HOST and len(REDIS_HOST) > 0,
            "REDIS_PORT": REDIS_PORT and REDIS_PORT > 0,
            "API_HOST": API_HOST,
            "API_PORT": API_PORT and API_PORT > 0,
            "CELERY_BROKER_URL": CELERY_BROKER_URL and "redis" in CELERY_BROKER_URL,
            "ENVIRONMENT": ENVIRONMENT in ["production", "development"],
        }
        
        return checks
        
    except ImportError as e:
        print(f"❌ Error importing config: {e}")
        return {}

def check_phase3_features():
    """Check if Phase 3 features are configured"""
    try:
        from config import (
            ENABLE_GRAPHQL_API, ENABLE_PLUGIN_SYSTEM,
            ENABLE_ADVANCED_DASHBOARD, ENABLE_CELERY
        )
        
        features = {
            "ENABLE_GRAPHQL_API": ENABLE_GRAPHQL_API,
            "ENABLE_PLUGIN_SYSTEM": ENABLE_PLUGIN_SYSTEM,
            "ENABLE_ADVANCED_DASHBOARD": ENABLE_ADVANCED_DASHBOARD,
            "ENABLE_CELERY": ENABLE_CELERY,
        }
        
        return features
        
    except ImportError:
        return {}

def check_env_file():
    """Check if .env.production exists"""
    env_path = Path(".env.production")
    return env_path.exists()

def print_results(checks, features, env_exists):
    """Print verification results"""
    print("\n" + "="*60)
    print("CONFIGURATION VERIFICATION REPORT")
    print("="*60 + "\n")
    
    # Required Settings
    print("📋 REQUIRED SETTINGS:")
    print("-" * 60)
    passed = 0
    failed = 0
    for setting, status in checks.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {setting}: {'PASS' if status else 'FAIL'}")
        if status:
            passed += 1
        else:
            failed += 1
    
    print(f"\n  Result: {passed}/{len(checks)} passed")
    
    # Phase 3 Features
    print("\n\n🚀 PHASE 3 FEATURES:")
    print("-" * 60)
    for feature, enabled in features.items():
        status_icon = "✅" if enabled else "ℹ️"
        status_text = "ENABLED" if enabled else "disabled (optional)"
        print(f"  {status_icon} {feature}: {status_text}")
    
    # Environment File
    print("\n\n📁 ENVIRONMENT FILE:")
    print("-" * 60)
    if env_exists:
        print("  ✅ .env.production exists")
    else:
        print("  ℹ️  .env.production not found (optional for Docker)")
    
    # Summary
    print("\n" + "="*60)
    if failed == 0:
        print("✅ CONFIGURATION COMPLETE AND READY FOR DEPLOYMENT")
        print("="*60)
        print("\nNext steps:")
        print("  1. Review .env.production settings (if using Docker)")
        print("  2. Update BOT_TOKEN if using real Telegram token")
        print("  3. Run: docker compose restart app celery-worker celery-beat")
        print("  4. Verify: curl http://localhost:8000/health")
        return 0
    else:
        print(f"❌ CONFIGURATION INCOMPLETE - {failed} required setting(s) missing")
        print("="*60)
        print("\nPlease update config.py with missing settings:")
        for setting, status in checks.items():
            if not status:
                print(f"  - {setting}")
        return 1

def main():
    """Run all verification checks"""
    print("\n🔍 Verifying configuration.py...")
    
    checks = check_required_settings()
    features = check_phase3_features()
    env_exists = check_env_file()
    
    if not checks:
        print("❌ Failed to load config module")
        return 1
    
    exit_code = print_results(checks, features, env_exists)
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
