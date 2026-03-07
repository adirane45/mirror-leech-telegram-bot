# Secrets Management Strategy

**Objective**: Migrate from static `.env` files to centralized secrets management, enabling zero-downtime credential rotation and preventing environment drift in distributed deployments.

## Current State (🔴 Anti-Pattern)

The current setup has several problems:

```
Problem 1: Environment Drift
├─ Worker Node A has token_v1
├─ Worker Node B has token_v1  ← stale
├─ Worker Node C has token_v2  ← newest
└─ Result: Silent failures, inconsistent behavior

Problem 2: Credential Rotation is Manual
├─ Rclone token expires
├─ Update .env.production on each worker
├─ Require service restart
└─ Potential downtime

Problem 3: .env File Sprawl
├─ .env.example (template)
├─ .env.production.example (docs)
├─ .env.production (actual secrets)
└─ Risk of committing real secrets to git
```

### Files Involved
- `scripts/secrets.sh` - Ad-hoc credential generation
- `scripts/security_setup.py` - Manual Grafana/Prometheus setup
- `config/.env.*` - 3 files, 486 total lines
- No centralized credential management

## Recommended Solution

### For Docker Swarm → Docker Secrets ✅

**Advantages:**
- Built-in to Docker
- No additional infrastructure
- Credentials never appear in processes, only mounted as files
- Rotate secrets without restart
- Works with Docker Compose

**Implementation:**

```bash
# Create secrets once
echo "your-bot-token" | docker secret create bot_token -
echo "your-rclone-key" | docker secret create rclone_key -

# Reference in docker-compose.yml
services:
  mltb-app:
    secrets:
      - bot_token
      - rclone_key
```

Pros:
- ✅ No additional setup
- ✅ Native Docker support
- ✅ Simple rotate: update secret, redeploy
- ✅ Works with existing docker-compose

Cons:
- ❌ Limited to Docker Swarm
- ❌ No audit logging built-in
- ❌ Rotate requires service restart

### For Kubernetes → Kube Secrets + External Secrets ✅

**Advantages:**
- Declarative via YAML
- Support for rotation without pod restart
- Optional: sync with external vault

**Implementation:**

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: mltb-secrets
type: Opaque
stringData:
  BOT_TOKEN: "your-bot-token"
  REDIS_PASSWORD: "your-redis-password"
  RCLONE_CONFIG: |
    [gdrive]
    type = drive
    token = ...
---
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mltb-app
spec:
  template:
    spec:
      containers:
      - name: mltb-app
        envFrom:
        - secretRef:
            name: mltb-secrets
```

Pros:
- ✅ Native Kubernetes integration
- ✅ RBAC for secret access
- ✅ Optional vault sync for rotation
- ✅ Declarative, gitops-friendly

Cons:
- ❌ Secrets stored as base64 (not encrypted by default)
- ❌ Requires etcd encryption for production

### For Advanced Requirements → HashiCorp Vault ✅

**When to use:**
- Need audit logging
- Multiple teams/environments
- Automatic rotation
- Encryption at rest

**Implementation:**

```hcl
# vault/config.hcl
path "secret/data/mltb/*" {
  capabilities = ["read", "list"]
}

path "secret/metadata/mltb/*" {
  capabilities = ["read", "list"]
}
```

```python
# src/bot/core/secrets_manager.py (Python client)
import hvac

class VaultSecretsManager:
    def __init__(self, vault_url: str, role_id: str, secret_id: str):
        self.client = hvac.Client(url=vault_url)
        self.client.auth.approle.login(role_id=role_id, secret_id=secret_id)
    
    def get_secret(self, path: str):
        """Fetch secret from Vault"""
        response = self.client.secrets.kv.v2.read_secret_version(path=path)
        return response['data']['data']
    
    async def watch_secret(self, path: str, callback):
        """Watch for secret changes and trigger callback"""
        while True:
            secret = self.get_secret(path)
            await callback(secret)
            await asyncio.sleep(300)  # Check every 5 minutes
```

Pros:
- ✅ Enterprise-grade audit logging
- ✅ Automatic rotation support
- ✅ Multi-team RBAC
- ✅ Encryption at rest

Cons:
- ❌ Additional infrastructure
- ❌ Operational complexity
- ❌ Steeper learning curve

## Recommended Path (🟢 Best of Both)

**Phase 1: Short-term (Docker Swarm/Compose)**
→ Use Docker Secrets + environment variables hybrid
→ 30-minute implementation
→ Solves 80% of problems

**Phase 2: Medium-term (Kubernetes)**
→ Migrate to Kubernetes Secrets
→ Add ExternalSecrets operator for Vault sync
→ 2-3 hour implementation

**Phase 3: Long-term (Production)**
→ Deploy HashiCorp Vault
→ Automatic secret rotation
→ Audit logging
→ Multi-team governance

## Implementation: Phase 1 (Docker Secrets)

### Step 1: Create Docker Secrets

```bash
#!/bin/bash
# docker/create-secrets.sh

# Telegram
echo "$BOT_TOKEN" | docker secret create telegram_bot_token -
echo "$TELEGRAM_API" | docker secret create telegram_api_id -
echo "$TELEGRAM_HASH" | docker secret create telegram_api_hash -

# Database
echo "$DATABASE_URL" | docker secret create database_url -
echo "$REDIS_PASSWORD" | docker secret create redis_password -

# Rclone
base64 -i "$RCLONE_CONFIG_PATH" | docker secret create rclone_config -

# SSL Certificates (if needed)
cat "$SSL_CERT_PATH" | docker secret create ssl_cert -
cat "$SSL_KEY_PATH" | docker secret create ssl_key -
```

### Step 2: Update docker-compose.yml

```yaml
version: '3.1'

secrets:
  telegram_bot_token:
    external: true
  telegram_api_id:
    external: true
  telegram_api_hash:
    external: true
  database_url:
    external: true
  redis_password:
    external: true
  rclone_config:
    external: true

services:
  mltb-app:
    image: mltb-app:latest
    secrets:
      - telegram_bot_token
      - telegram_api_id
      - telegram_api_hash
      - database_url
      - redis_password
      - rclone_config
    environment:
      # Secrets are mounted at /run/secrets/SECRET_NAME
      BOT_TOKEN_FILE: /run/secrets/telegram_bot_token
      TELEGRAM_API_FILE: /run/secrets/telegram_api_id
      TELEGRAM_HASH_FILE: /run/secrets/telegram_api_hash
      DATABASE_URL_FILE: /run/secrets/database_url
      REDIS_PASSWORD_FILE: /run/secrets/redis_password
      RCLONE_CONFIG_PATH: /run/secrets/rclone_config
```

### Step 3: Update Application to Read from Files

```python
# src/bot/core/config_manager.py

import os
from pathlib import Path

class SecretReader:
    """Read secrets from environment or Docker Secret files"""
    
    @staticmethod
    def get_secret(env_var: str, file_var: str = None) -> str:
        """
        Get secret from environment or Docker Secret file.
        
        Priority:
        1. environment variable ending with _FILE (file path)
        2. environment variable directly
        3. Docker secret file at /run/secrets/{env_var}
        """
        # Check if _FILE variant exists (Docker Swarm pattern)
        file_path_env = f"{env_var}_FILE"
        if file_path_env in os.environ:
            file_path = os.environ[file_path_env]
            if Path(file_path).exists():
                with open(file_path) as f:
                    return f.read().strip()
        
        # Check direct environment variable
        if env_var in os.environ:
            return os.environ[env_var]
        
        # Check Docker secret mount
        secret_file = Path(f"/run/secrets/{env_var.lower()}")
        if secret_file.exists():
            with open(secret_file) as f:
                return f.read().strip()
        
        raise ValueError(f"Secret {env_var} not found")

# Usage
class Config:
    BOT_TOKEN = SecretReader.get_secret("BOT_TOKEN")
    TELEGRAM_API = SecretReader.get_secret("TELEGRAM_API")
    TELEGRAM_HASH = SecretReader.get_secret("TELEGRAM_HASH")
    DATABASE_URL = SecretReader.get_secret("DATABASE_URL")
    REDIS_PASSWORD = SecretReader.get_secret("REDIS_PASSWORD")
```

### Step 4: Secret Rotation Without Downtime

```bash
#!/bin/bash
# docker/rotate-secrets.sh

SERVICES=("mltb-app")
NEW_BOT_TOKEN="$1"

# Remove old secret
docker secret rm telegram_bot_token || true

# Create new secret
echo "$NEW_BOT_TOKEN" | docker secret create telegram_bot_token -

# Force service to redeploy and pick up new secret
for service in "${SERVICES[@]}"; do
    docker service update --force "$service"
done

echo "✅ Secrets rotated and services updated"
```

## Implementation: Phase 2 (Kubernetes)

**Full documentation** is available in [kubernetes/README.md](kubernetes/README.md) with quick start, production deployment, and troubleshooting guides.

**Estimated effort**: 1-2 hours for initial setup, then zero-downtime rotation on demand

### Files

- **[kubernetes/secrets.yaml](kubernetes/secrets.yaml)** - All secret definitions with RBAC
- **[kubernetes/deployment.yaml](kubernetes/deployment.yaml)** - Deployment manifest with health checks
- **[kubernetes/rotate-secret.sh](kubernetes/rotate-secret.sh)** - Production-grade rotation script
- **[kubernetes/namespace.yaml](kubernetes/namespace.yaml)** - Namespace and RBAC setup
- **[kubernetes/kustomization.yaml](kubernetes/kustomization.yaml)** - Kustomize overlay
- **[docs/operations/KUBERNETES_MIGRATION.md](docs/operations/KUBERNETES_MIGRATION.md)** - Step-by-step migration guide

### Quick Start

```bash
# 1. Create namespace and secrets
kubectl apply -f kubernetes/namespace.yaml

kubectl create secret generic mltb-telegram-secrets \
  --from-literal=BOT_TOKEN="$BOT_TOKEN" \
  --from-literal=TELEGRAM_API="$TELEGRAM_API" \
  -n mltb

kubectl create secret generic mltb-database-secrets \
  --from-literal=DATABASE_URL="$DATABASE_URL" \
  -n mltb

kubectl create secret generic mltb-redis-secrets \
  --from-literal=REDIS_URL="$REDIS_URL" \
  -n mltb

# 2. Deploy with secrets
kubectl apply -f kubernetes/deployment.yaml

# 3. Verify deployment
kubectl get deployment -n mltb
kubectl get pods -n mltb
```

### Zero-Downtime Secret Rotation

Kubernetes provides three rotation strategies via `rotate-secret.sh`:

#### Rolling Strategy (Default - Recommended)
```bash
# Update secret and roll pods one at a time (service stays up)
./kubernetes/rotate-secret.sh \
  mltb-telegram-secrets \
  BOT_TOKEN \
  "new-token-value"

# Result: Pods restart in rolling fashion, service never goes down
```

#### Blue-Green Strategy (Safest for Critical Changes)
```bash
# Deploy new version, switch traffic, retire old version
./kubernetes/rotate-secret.sh \
  mltb-telegram-secrets \
  BOT_TOKEN \
  "new-token-value" \
  --strategy blue-green

# Result: New pods verified healthy, traffic switched, can rollback instantly
```

#### Immediate Strategy (For Non-Critical Secrets)
```bash
# Update secret, pods pick up changes at next restart
./kubernetes/rotate-secret.sh \
  mltb-api-secrets \
  API_SECRET_KEY \
  "new-key-value" \
  --strategy immediate

# Result: Less disruptive, pods only restart on readiness probe failure
```

### Production Features

✅ **RBAC**: Pods can only read their required secrets  
✅ **Health Checks**: Validates secrets on pod startup  
✅ **Audit Logging**: All rotations logged with timestamp/user  
✅ **Automatic Backup**: Creates backup before each rotation  
✅ **Rollback**: Instant restore from backup if needed  
✅ **Pod Anti-Affinity**: Spreads pods across nodes  
✅ **HPA**: Auto-scales based on CPU/memory  
✅ **Monitoring**: Integrates with Prometheus, tracks rotation age  

### Key Differences from Docker Secrets

| Feature | Docker Secrets | K8s Secrets |
|---------|---|---|
| Setup time | 30 min | 1-2 hours |
| Rotation | Rolling restart | Rolling/Blue-green/Immediate |
| Scalability | 1-5 nodes | 10-1000+ nodes |
| RBAC | Pod-level access | Fine-grained RBAC + network policies |
| Encryption | None (mounted only) | etcd encryption (production) |
| Audit logging | Manual | Built-in with audit endpoints |
| Complex workflows | Limited | Full StatefulSets, DaemonSets, etc. |

See [kubernetes/README.md](kubernetes/README.md) for complete deployment guide and [docs/operations/KUBERNETES_MIGRATION.md](docs/operations/KUBERNETES_MIGRATION.md) for detailed migration steps.

## Implementation: Phase 3 (HashiCorp Vault)

See [VAULT_SETUP.md](./docs/operations/VAULT_SETUP.md) for detailed setup.

```python
# src/bot/core/vault_secrets_manager.py
import hvac
from typing import Dict, Any

class VaultSecretsManager:
    def __init__(self, vault_addr: str, role_id: str, secret_id: str):
        self.client = hvac.Client(url=vault_addr)
        self.client.auth.approle.login(
            role_id=role_id,
            secret_id=secret_id,
            mount_point='approle'
        )
    
    def get_secret(self, path: str) -> Dict[str, Any]:
        """Fetch secret from Vault"""
        response = self.client.secrets.kv.v2.read_secret_version(path=path)
        return response['data']['data']
    
    def list_secrets(self, path: str) -> list:
        """List secrets at path"""
        response = self.client.secrets.kv.v2.list_secrets(path=path)
        return response['data']['keys']

# Usage in app startup
vault_manager = VaultSecretsManager(
    vault_addr="https://vault.internal:8200",
    role_id=os.getenv("VAULT_ROLE_ID"),
    secret_id=os.getenv("VAULT_SECRET_ID")
)

config = {
    'BOT_TOKEN': vault_manager.get_secret('secret/data/mltb/telegram')['bot_token'],
    'DATABASE_URL': vault_manager.get_secret('secret/data/mltb/database')['url'],
    'REDIS_PASSWORD': vault_manager.get_secret('secret/data/mltb/redis')['password'],
}
```

## Migration Checklist

- [ ] **Audit current secrets**
  - [ ] List all environment variables
  - [ ] Identify sensitive values
  - [ ] Map to rotation schedule

- [ ] **Phase 1: Docker Secrets (if using Swarm/Compose)**
  - [ ] Create `docker/create-secrets.sh`
  - [ ] Update `docker-compose.yml`
  - [ ] Implement `SecretReader` class
  - [ ] Test secret mounting
  - [ ] Create `docker/rotate-secrets.sh`

- [ ] **Phase 2: Kubernetes Secrets (if using K8s)**
  - [ ] Create initial Kubernetes secrets
  - [ ] Update deployment YAML
  - [ ] Test secret injection
  - [ ] Create rotation script
  - [ ] Test zero-downtime rotation

- [ ] **Phase 3: Vault Integration (production)**
  - [ ] Deploy Vault cluster
  - [ ] Configure AppRole auth
  - [ ] Migrate secrets to Vault
  - [ ] Implement secret watcher
  - [ ] Enable audit logging
  - [ ] Test automatic rotation

- [ ] **Documentation**
  - [ ] Update DEPLOYMENT.md
  - [ ] Create ROTATION_SCHEDULE.md
  - [ ] Document secret naming conventions
  - [ ] Add to runbooks

## Security Best Practices

1. **Principle of Least Privilege**
   ```yaml
   # Only grant access to secrets needed
   capabilities: ["read"]  # Not list or delete
   ```

2. **Secret Naming Convention**
   ```
   mltb/telegram/bot_token
   mltb/database/connection_string
   mltb/rclone/config
   ```

3. **Rotation Schedule**
   ```
   Critical (30 days):
   - BOT_TOKEN (if compromised, can't control bot)
   - DATABASE credentials
   
   Important (90 days):
   - RCLONE keys
   - API keys
   
   Standard (180 days):
   - Internal service passwords
   ```

4. **Audit Logging**
   - Log all secret access
   - Alert on failed authentication
   - Track rotations

5. **Encryption at Rest**
   - K8s: Enable etcd encryption
   - Vault: Use encryption transit engine
   - Docker: Use secrets stored in encrypted filesystem

## Troubleshooting

### Kubernetes: Secret not appearing in pod
```bash
# Check secret exists
kubectl get secrets -n mltb

# Describe secret
kubectl describe secret mltb-secrets -n mltb

# Check pod environment
kubectl exec -it POD_NAME -- printenv | grep SECRET
```

### Docker Swarm: Secret permission denied
```bash
# Verify secret exists
docker secret ls

# Check service status
docker service ps SERVICE_NAME

# View service logs
docker service logs SERVICE_NAME
```

### Vault: Auth failed
```bash
# Check AppRole credentials
vault read auth/approle/role/mltb-role

# Test server connectivity
curl -k https://vault.internal:8200/v1/auth/approle/login
```

## Conclusion

| Approach | Setup | Maintenance | Scalability | Recommendation |
|----------|-------|-------------|-------------|-----------------|
| .env files | Easy | Manual | Poor | ❌ Current state |
| Docker Secrets | 30 min | Medium | Good | ✅ Phase 1 |
| K8s Secrets | 1 hour | Medium | Good | ✅ Phase 2 |
| HashiCorp Vault | 3-4 hours | Low | Excellent | ✅ Phase 3 |

**Immediate action**: Implement Docker Secrets (Phase 1) this week. This solves environment drift and enables zero-downtime rotation.

**Follow-up**: Plan Kubernetes migration (Phase 2) for next quarter if scaling beyond single Swarm cluster.

**Long-term**: Vault integration (Phase 3) when managing multiple teams or requiring audit compliance.
