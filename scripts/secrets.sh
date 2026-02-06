#!/bin/bash
# Generate secure random values for secrets

# 32-char hex key for encryption
generate_key() {
  openssl rand -hex 16
}

echo "=== SECURE CREDENTIALS GENERATOR ==="
echo ""
echo "Redis Password: $(generate_key)"
echo "Session Encryption: $(generate_key)"
echo "Backup Encryption: $(generate_key)"
echo "API Secret Key: $(openssl rand -base64 32)"
echo ""
echo "Update .env.production with these values"
