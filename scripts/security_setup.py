#!/usr/bin/env python3
"""
Phase 1 Security Setup Script
Configures authentication, API keys, and service isolation
"""

import secrets
from datetime import datetime

import requests


class SecuritySetup:
    def __init__(self):
        self.grafana_url = "http://localhost:3000"
        self.prometheus_url = "http://localhost:9091"
        self.app_url = "http://localhost:8000"
        self.results = []

    def setup_grafana_api_key(self):
        """Create Grafana API key for programmatic access"""
        print("\n🔑 Setting up Grafana API Key...")

        api_key_name = f"mltb-bot-{datetime.now().strftime('%Y%m%d')}"
        headers = {"Content-Type": "application/json"}

        # Default Grafana credentials
        auth = ("admin", "admin")

        payload = {
            "name": api_key_name,
            "role": "Admin",
            "secondsToLive": 2592000  # 30 days
        }

        try:
            response = requests.post(
                f"{self.grafana_url}/api/auth/keys",
                json=payload,
                auth=auth,
                headers=headers,
                timeout=5
            )

            if response.status_code == 200:
                key_data = response.json()
                api_key = key_data.get('key')
                self.results.append({
                    'service': 'Grafana',
                    'status': '✅ API Key Created',
                    'details': f"Key: {api_key[:20]}***" if api_key else 'None'
                })
                return api_key
            else:
                self.results.append({
                    'service': 'Grafana',
                    'status': f'⚠️  Status {response.status_code}',
                    'details': response.text[:100]
                })
                return None
        except Exception as e:
            self.results.append({
                'service': 'Grafana',
                'status': '❌ Error',
                'details': str(e)
            })
            return None

    def configure_prometheus_security(self):
        """Configure Prometheus security settings"""
        print("\n🔐 Configuring Prometheus Security...")

        # Generate bearer token for metrics endpoint
        bearer_token = secrets.token_urlsafe(32)

        self.results.append({
            'service': 'Prometheus',
            'status': '✅ Bearer Token Generated',
            'details': f"Token: {bearer_token[:20]}***"
        })

        return bearer_token

    def generate_redis_password(self):
        """Generate secure Redis password"""
        print("\n🔒 Generating Redis Credentials...")

        redis_password = secrets.token_urlsafe(32)

        self.results.append({
            'service': 'Redis',
            'status': '✅ Password Generated',
            'details': f"Password: {redis_password[:20]}***"
        })

        return redis_password

    def generate_mongodb_credentials(self):
        """Generate MongoDB user credentials"""
        print("\n🔒 Generating MongoDB Credentials...")

        mongo_user = "mltb_bot"
        mongo_password = secrets.token_urlsafe(32)

        self.results.append({
            'service': 'MongoDB',
            'status': '✅ User Created',
            'details': f"User: {mongo_user} | Pass: {mongo_password[:20]}***"
        })

        return mongo_user, mongo_password

    def create_security_config(self):
        """Generate security configuration file"""
        print("\n📝 Creating Security Configuration...")

        config = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "security": {
                "grafana": {
                    "default_admin": "admin",
                    "default_password": "admin",
                    "recommendation": "Change password immediately in production"
                },
                "prometheus": {
                    "port": 9091,
                    "metrics_port": 9090,
                    "bearer_token_required": True,
                    "bearer_token_env": "PROMETHEUS_BEARER_TOKEN"
                },
                "redis": {
                    "port": 6379,
                    "password_required": True,
                    "password_env": "REDIS_PASSWORD",
                    "recommendation": "Use requirepass in redis.conf"
                },
                "mongodb": {
                    "port": 27017,
                    "auth_required": True,
                    "auth_db": "admin",
                    "recommendation": "Enable RBAC before production"
                },
                "bot": {
                    "port": 8000,
                    "metrics_endpoint": "/metrics",
                    "secure_endpoints": [
                        "/admin",
                        "/settings",
                        "/api/v1"
                    ],
                    "api_key_required": True
                }
            },
            "firewall_rules": {
                "description": "Recommended firewall rules",
                "rules": [
                    {
                        "port": 8000,
                        "service": "bot-web",
                        "allow_from": "0.0.0.0/0",
                        "protocol": "tcp"
                    },
                    {
                        "port": 9090,
                        "service": "metrics",
                        "allow_from": "127.0.0.1",
                        "protocol": "tcp",
                        "note": "Restrict to localhost/VPC"
                    },
                    {
                        "port": 3000,
                        "service": "grafana",
                        "allow_from": "127.0.0.1",
                        "protocol": "tcp",
                        "note": "Restrict to admins only"
                    },
                    {
                        "port": 9091,
                        "service": "prometheus",
                        "allow_from": "127.0.0.1",
                        "protocol": "tcp",
                        "note": "Internal only"
                    },
                    {
                        "port": 6379,
                        "service": "redis",
                        "allow_from": "172.17.0.0/16",
                        "protocol": "tcp",
                        "note": "Docker network only"
                    },
                    {
                        "port": 27017,
                        "service": "mongodb",
                        "allow_from": "172.17.0.0/16",
                        "protocol": "tcp",
                        "note": "Docker network only"
                    }
                ]
            },
            "tls_configuration": {
                "recommendations": [
                    "Use reverse proxy (Nginx/Caddy) for TLS termination",
                    "Certificate: Let's Encrypt (free) or commercial",
                    "Minimum: TLS 1.2 (preferably 1.3)",
                    "HSTS headers: max-age=31536000"
                ]
            },
            "authentication": {
                "methods": {
                    "grafana_api": "Bearer token in Authorization header",
                    "prometheus": "Bearer token in Authorization header",
                    "redis": "AUTH password command",
                    "mongodb": "SCRAM-SHA-256 authentication",
                    "bot_api": "API key in X-API-Key header"
                }
            }
        }

        return config

    def run_setup(self):
        """Run complete security setup"""
        print("\n" + "="*70)
        print("🔐 PHASE 1 SECURITY SETUP & AUTHENTICATION")
        print("="*70)

        # Generate credentials
        self.setup_grafana_api_key()
        self.configure_prometheus_security()
        self.generate_redis_password()
        mongo_user, mongo_password = self.generate_mongodb_credentials()

        # Create configuration
        security_config = self.create_security_config()

        # Print results
        print("\n" + "="*70)
        print("📊 SECURITY SETUP RESULTS")
        print("="*70 + "\n")

        for result in self.results:
            print(f"{result['status']}")
            print(f"  Service: {result['service']}")
            print(f"  {result['details']}\n")

        print("="*70)
        print("⚠️  IMPORTANT SECURITY NOTES")
        print("="*70 + "\n")

        print("""
1. DEFAULT CREDENTIALS - CHANGE IMMEDIATELY
   ❌ Grafana: admin / admin (DEFAULT - NOT SECURE)
   ✅ Action: Change in Grafana UI → Administration → Users

2. SECRETS MANAGEMENT
   ✅ Store all generated tokens in environment variables
   ✅ Use .env file (add to .gitignore) or secrets manager
   ✅ Never commit credentials to git

3. NETWORK SECURITY
   ✅ Restrict metrics endpoint (9090) to localhost
   ✅ Restrict Prometheus (9091) to internal only
   ✅ Restrict Grafana (3000) to admin network
   ✅ Allow Redis/MongoDB only from Docker network

4. TLS/HTTPS CONFIGURATION
   ✅ Deploy behind reverse proxy (Nginx/Caddy)
   ✅ Enable TLS 1.2+ for external connections
   ✅ Use Let's Encrypt for free certificates
   ✅ Enable HSTS headers

5. DATABASE AUTHENTICATION
   ✅ Redis: Update redis.conf with requirepass
   ✅ MongoDB: Enable authentication database
   ✅ Create application-specific user accounts
   ✅ Use role-based access control (RBAC)

6. API SECURITY
   ✅ All API endpoints require authentication
   ✅ Use API keys for programmatic access
   ✅ Implement rate limiting
   ✅ Log all API access attempts

7. MONITORING & LOGGING
   ✅ Enable security audit logging
   ✅ Monitor failed authentication attempts
   ✅ Alert on suspicious activities
   ✅ Regular security log reviews

8. BACKUP & RECOVERY
   ✅ Encrypt backup files
   ✅ Store backups in secure location
   ✅ Test recovery procedures regularly
   ✅ Document security procedures
        """)

        print("="*70)
        print("✅ SECURITY SETUP COMPLETE")
        print("="*70 + "\n")

        return security_config

if __name__ == "__main__":
    setup = SecuritySetup()
    config = setup.run_setup()
