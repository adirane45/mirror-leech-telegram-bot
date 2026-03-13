# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying the Mirror Leech Telegram Bot (MLTB) with centralized secrets management.

## Overview

MLTB uses **Kubernetes native secrets management** with support for multiple rotation strategies to prevent environment drift and enable zero-downtime credential updates.

### Key Features

- **Zero-Downtime Secret Rotation**: Update credentials without service interruption
- **RBAC-Based Access Control**: Pods only access required secrets
- **Audit Logging**: Track all secret changes with timestamps and user attribution
- **Backup & Restore**: Automatic backups before rotation with easy rollback
- **Multiple Strategies**: Rolling updates, blue-green deployments, or immediate (for non-critical secrets)
- **Health Checks**: Validate secrets on pod startup
- **Pod Anti-Affinity**: Spread pods across nodes for high availability

## Quick Start

### 1. Prerequisites

```bash
# Kubernetes cluster 1.19+
kubectl version --short

# kubectl configured for target cluster
kubectl cluster-info

# kustomize (optional, for templating)
kustomize version
```

### 2. Create Namespace and Secrets

```bash
# Create namespace
kubectl apply -f kubernetes/namespace.yaml

# Create secrets from environment variables or files
#
# Option A: From environment variables
export BOT_TOKEN="your-telegram-bot-token"
export TELEGRAM_API="your-api-id"
export TELEGRAM_HASH="your-api-hash"
# ... other secrets ...

kubectl create secret generic mltb-telegram-secrets \
  --from-literal=BOT_TOKEN="$BOT_TOKEN" \
  --from-literal=TELEGRAM_API="$TELEGRAM_API" \
  --from-literal=TELEGRAM_HASH="$TELEGRAM_HASH" \
  --from-literal=OWNER_ID="$OWNER_ID" \
  --namespace mltb

kubectl create secret generic mltb-database-secrets \
  --from-literal=DATABASE_URL="$DATABASE_URL" \
  --namespace mltb

kubectl create secret generic mltb-redis-secrets \
  --from-literal=REDIS_URL="$REDIS_URL" \
  --namespace mltb

kubectl create secret generic mltb-api-secrets \
  --from-literal=API_SECRET_KEY="$API_SECRET_KEY" \
  --namespace mltb

# Option B: From secure secret file
kubectl create secret generic mltb-telegram-secrets \
  --from-file=secrets.env \
  --namespace mltb
```

### 3. Configure Rclone Secret (Optional)

For cloud storage integration:

```bash
# Option A: Mount existing rclone config
kubectl create secret generic mltb-rclone-secrets \
  --from-file=rclone.conf=/path/to/rclone.conf \
  --namespace mltb

# Option B: Create from individual tokens
kubectl create secret generic mltb-rclone-secrets \
  --from-literal=RCLONE_CONFIG_PATH="/etc/rclone/rclone.conf" \
  --namespace mltb
```

### 4. Configure SSL Certificates (Optional)

```bash
# Create TLS secret for HTTPS
kubectl create secret tls mltb-ssl-secrets \
  --cert=/path/to/tls.crt \
  --key=/path/to/tls.key \
  --namespace mltb
```

### 5. Deploy Application

```bash
# Option A: Using kubectl directly
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/secrets.yaml
kubectl apply -f kubernetes/deployment.yaml

# Option B: Using kustomize (recommended for production)
kubectl apply -k kubernetes/

# Verify deployment
kubectl get deployments -n mltb
kubectl get pods -n mltb
kubectl logs -n mltb -f deployment/mltb-app
```

## Secret Files Reference

### `namespace.yaml`
Creates the `mltb` namespace with appropriate labels and annotations.

### `secrets.yaml`
Defines all secret resources:
- **mltb-telegram-secrets**: Bot token, API credentials, owner ID
- **mltb-database-secrets**: MongoDB connection string and credentials
- **mltb-redis-secrets**: Redis URL and password
- **mltb-rclone-secrets**: Cloud storage configuration
- **mltb-ssl-secrets**: TLS certificates
- **mltb-api-secrets**: API keys and tokens

**IMPORTANT**: Never commit `secrets.yaml` with actual values. Use one of these approaches:

#### Option 1: Sealed Secrets (Recommended)
```bash
# Install sealed-secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/...

# Create sealed secret
echo -n 'actual-token' | kubectl create secret generic mltb-telegram-secrets \
  --dry-run=client \
  --from-file=BOT_TOKEN=/dev/stdin \
  -o yaml | kubeseal -f - > secrets-sealed.yaml

kubectl apply -f secrets-sealed.yaml
```

#### Option 2: External Secrets Operator
```bash
# Configure external secret to pull from HashiCorp Vault, AWS Secrets Manager, etc.
# See SECRETS_MANAGEMENT.md for examples
```

#### Option 3: Manual Secret Creation (Development Only)
```bash
# Documented in Quick Start section above
```

### `deployment.yaml`
Kubernetes Deployment manifest with:
- 3 replicas spread across nodes
- Health checks (liveness + readiness probes)
- Secret injection as environment variables and volume mounts
- Resource quotas (requests & limits)
- Security context (read-only root, non-root user)
- HPA for auto-scaling based on metrics
- Pod disruption budget for controlled updates

### `kustomization.yaml`
Kustomize overlay combining all resources with:
- Common labels and annotations
- Image configuration
- Replica count override capability
- Namespace prefix injection

## Secret Rotation

### Zero-Downtime Rotation Using `rotate-secret.sh`

The `rotate-secret.sh` script enables zero-downtime secret rotation with multiple strategies.

#### Rolling Update Strategy (Default)

```bash
# Rotate a single secret immediately
./kubernetes/rotate-secret.sh \
  mltb-telegram-secrets \
  BOT_TOKEN \
  "new-token-value"

# Pods restart in rolling fashion:
# 1. Patch secret with new value
# 2. Trigger rolling restart (1 pod at a time)
# 3. Service remains available throughout
# 4. Backup created automatically
```

#### Blue-Green Strategy (Zero Downtime for Large Changes)

```bash
./kubernetes/rotate-secret.sh \
  mltb-telegram-secrets \
  BOT_TOKEN \
  "new-token-value" \
  --strategy blue-green

# Blue-green process:
# 1. Backup current secret
# 2. Patch secret with new value
# 3. Deploy green (new version) with updated config
# 4. Wait for green to be healthy
# 5. Switch service traffic to green
# 6. Delete old blue deployment
# 7. Keep traffic on green
```

#### Immediate Strategy (For Non-Critical Secrets)

```bash
./kubernetes/rotate-secret.sh \
  mltb-api-secrets \
  API_SECRET_KEY \
  "new-key-value" \
  --strategy immediate

# Immediate process:
# 1. Patch secret immediately
# 2. Pods pick up new value at next restart/probe
# 3. No forced restart - less disruptive for non-critical secrets
```

#### Dry-Run Mode

```bash
# Preview what rotation would do without making changes
DRY_RUN=true ./kubernetes/rotate-secret.sh \
  mltb-telegram-secrets \
  BOT_TOKEN \
  "test-value"
```

#### Rotation Monitoring

```bash
# Check rotation history
tail -f /var/log/secret-rotations/rotation-history.log

# Restore from backup
kubectl apply -f /var/log/secret-rotations/backups/mltb-telegram-secrets_20240301_143022.yaml
```

## Secrets Management Scenarios

### Scenario 1: Daily Rclone Token Refresh

Problem: Rclone token expires, uploads fail on nodes with stale tokens.

Solution: Automatic rotation with rolling strategy:

```bash
#!/bin/bash
# cron job: 0 2 * * * (runs daily at 2 AM)

RCLONE_TOKEN=$(curl -s https://api.refresh.service/rclone/token)

./kubernetes/rotate-secret.sh \
  mltb-rclone-secrets \
  RCLONE_CONFIG_PATH \
  "$RCLONE_TOKEN" \
  --strategy rolling

# Result:
# - All pods receive new token within 5 minutes
# - Service never goes down
# - All nodes synchronized
# - Token refresh visible in logs
```

### Scenario 2: Emergency Telegram Bot Token Rotation

Problem: Bot token compromised, need immediate rotation.

Solution: Blue-green deployment for safety:

```bash
./kubernetes/rotate-secret.sh \
  mltb-telegram-secrets \
  BOT_TOKEN \
  "new-emergency-token" \
  --strategy blue-green

# Result:
# - New deployment starts with new token
# - Once verified healthy, traffic switches
# - Can roll back instantly if issues
# - Original deployment kept for 5 min before cleanup
```

### Scenario 3: Database Credential Rotation (Quarterly)

Problem: Database password rotation required by security policy.

```bash
# Update database with new credentials first
# Ensure DB accepts both old and new for 60 seconds

./kubernetes/rotate-secret.sh \
  mltb-database-secrets \
  DATABASE_PASSWORD \
  "new-secure-password" \
  --strategy rolling

# Pods restart gradually, picking up new password
# Requests queue during pod restart
# No database connection failures due to staggered updates
```

## Health Checks & Validation

Kubernetes performs automatic health checks to ensure pods stay running:

### Startup Probe (Pod Initialization)
```bash
# Validates all required secrets are available
# Logs error if BOT_TOKEN, DATABASE_URL, REDIS_URL missing
# Pod won't start if secrets validation fails
```

### Liveness Probe
```bash
# Runs every 10 seconds after pod starts
# Checks `/api/v1/health` endpoint
# Restarts pod if endpoint returns error
# Prevents stuck pods from sitting in cluster
```

### Readiness Probe
```bash
# Runs every 5 seconds
# Checks `/api/v1/ready` endpoint
# Removes pod from service load balancer if not ready
# Prevents routing to unhealthy pods
```

## Troubleshooting

### Pod stuck in `CrashLoopBackOff`

```bash
# Check pod logs
kubectl logs -n mltb <pod-name>

# Check startup probe failures
kubectl describe pod -n mltb <pod-name>

# Common causes:
# 1. Secrets not created: "ERROR: BOT_TOKEN not set"
# 2. Invalid secret values
# 3. Database/Redis unreachable

# Fix:
kubectl get secrets -n mltb  # Verify all secrets exist
kubectl describe secret -n mltb mltb-telegram-secrets  # Check content
```

### Secret changes not picked up

```bash
# Force pod restart
kubectl rollout restart deployment/mltb-app -n mltb

# Verify new pods started
kubectl get pods -n mltb
kubectl logs -n mltb <new-pod-name>
```

### Rotation script permissions error

```bash
# Error: "Insufficient permissions to update secrets"

# Update RBAC to allow secret updates
kubectl apply -f - <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: secret-rotator
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "patch", "update"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "patch"]
- apiGroups: ["apps"]
  resources: ["deployments/rollout"]
  verbs: ["create"]
EOF
```

## Advanced Topics

### Using Sealed Secrets

```bash
# Install sealed-secrets-controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.18.0/controller.yaml

# Create sealing key
kubeseal --fetch-sealing-key > sealing-key.crt

# Seal secret
echo -n 'my-secret-value' | kubeseal -f - | kubectl apply -f -

# Sealed secret is safe to commit to git
```

### Using External Secrets Operator (ESO)

```bash
# Sync secrets from HashiCorp Vault, AWS Secrets Manager, etc.
# See ../docs/operations/VAULT_SETUP.md for configuration
```

### Implementing Custom Secret Validation

```bash
# Edit deployment.yaml startup probe:
livenessProbe:
  exec:
    command:
    - /bin/sh
    - -c
    - |
      python3 -c "
      from src.bot.core.secret_reader import SecretReader
      SecretReader.validate_secrets([
        'BOT_TOKEN', 'DATABASE_URL', 'REDIS_URL'
      ])
      print('All secrets valid')
      "
```

## Production Readiness Checklist

- [ ] All secrets created and verified
- [ ] RBAC configured for pod secret access
- [ ] Sealed Secrets or similar encryption enabled
- [ ] Backup procedure documented and tested
- [ ] Rotation schedule established (daily/weekly/monthly)
- [ ] Alert configured for secret rotation failures
- [ ] Monitoring dashboard displays secret age
- [ ] Runbook created for emergency secret rotation
- [ ] Rollback procedure tested
- [ ] Team trained on rotation procedures

## Related Documentation

- [SECRETS_MANAGEMENT.md](../SECRETS_MANAGEMENT.md) - Overall secrets strategy
- [DEPLOYMENT.md](../docs/operations/DEPLOYMENT.md) - General deployment guide
- [VAULT_SETUP.md](../docs/operations/VAULT_SETUP.md) - HashiCorp Vault integration
- [SECURITY.md](../SECURITY.md) - Security best practices

## Support & Troubleshooting

For issues with Kubernetes deployment:

1. Check pod logs: `kubectl logs -n mltb <pod-name>`
2. Check events: `kubectl describe pod -n mltb <pod-name>`
3. Check secrets: `kubectl get secrets -n mltb`
4. Test connectivity: `kubectl exec -it -n mltb <pod-name> -- bash`

For secret rotation issues:

1. Run with `--dry-run` to preview changes
2. Check rotation history: `/var/log/secret-rotations/rotation-history.log`
3. Review backup: `/var/log/secret-rotations/backups/`
4. Run validation: `./kubernetes/rotate-secret.sh --help`
