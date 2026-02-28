# Kubernetes Secrets Migration Guide

This document provides step-by-step instructions for migrating from Docker Compose `.env` files to Kubernetes native secrets management.

## Table of Contents

1. [Pre-Migration Assessment](#pre-migration-assessment)
2. [Phase 1: Setup & Preparation](#phase-1-setup--preparation)
3. [Phase 2: Secrets Migration](#phase-2-secrets-migration)
4. [Phase 3: Validation & Verification](#phase-3-validation--verification)
5. [Phase 4: Cutover & Monitoring](#phase-4-cutover--monitoring)
6. [Rollback Procedure](#rollback-procedure)

## Pre-Migration Assessment

### Current State Inventory

List all current secrets in your Docker Compose environment:

```bash
# Check .env files
cat config/.env.production | grep -E "^[A-Z_]+=" | wc -l

# Categorize secrets
grep -E "TOKEN|PASSWORD|KEY|URL" config/.env.production | sort

# Output example:
# BOT_TOKEN=...
# TELEGRAM_API=...
# DATABASE_PASSWORD=...
# REDIS_PASSWORD=...
# RCLONE_CONFIG_PATH=...
# API_SECRET_KEY=...
```

### Migration Readiness Checklist

- [ ] Kubernetes cluster accessible and running 1.19+
- [ ] `kubectl` configured and authenticated
- [ ] Backup of all `.env` files (stored securely offline)
- [ ] Target namespace reviewed (`mltb`)
- [ ] RBAC policies reviewed and approved
- [ ] Team informed of migration schedule
- [ ] Maintenance window scheduled (off-peak hours)
- [ ] Rollback plan documented and rehearsed

## Phase 1: Setup & Preparation

### 1.1 Create Kubernetes Namespace

```bash
# Apply namespace configuration
kubectl apply -f kubernetes/namespace.yaml

# Verify namespace created
kubectl get namespace mltb
```

### 1.2 Review RBAC Configuration

```bash
# Check existing roles
kubectl get roles -n mltb

# Apply deployment with service account
kubectl apply -f kubernetes/deployment.yaml

# Verify service account created
kubectl get serviceaccount -n mltb mltb-app
```

### 1.3 Prepare Secret Values

Extract secrets from Docker Compose and prepare for Kubernetes:

```bash
#!/bin/bash
# export-secrets.sh - Extract secrets for migration

set -e

# Read .env file and create Kubernetes-compatible format
echo "Extracting secrets from .env file..."

# Create temporary directory for secrets
SECRETS_DIR=$(mktemp -d)
trap "rm -rf $SECRETS_DIR" EXIT

# Extract each secret category
grep "^BOT_TOKEN=" config/.env.production > "$SECRETS_DIR/bot.env"
grep "^TELEGRAM_" config/.env.production > "$SECRETS_DIR/telegram.env"
grep "^DATABASE_" config/.env.production > "$SECRETS_DIR/database.env"
grep "^REDIS_" config/.env.production > "$SECRETS_DIR/redis.env"
grep "^RCLONE_" config/.env.production > "$SECRETS_DIR/rclone.env"
grep "^API_" config/.env.production > "$SECRETS_DIR/api.env"

# Backup original environment
cp config/.env.production "config/.env.production.backup.$(date +%s)"
chmod 600 "config/.env.production.backup.$(date +%s)"

echo "Secrets prepared in: $SECRETS_DIR"
echo "Backup created: config/.env.production.backup.$(date +%s)"
```

## Phase 2: Secrets Migration

### 2.1 Create Secrets in Kubernetes

```bash
#!/bin/bash
# create-k8s-secrets.sh

set -e

NAMESPACE="mltb"

echo "Creating Kubernetes secrets from .env files..."

# Function to safely extract and create secret
create_secret() {
    local secret_name=$1
    local patterns=$2
    
    echo "Creating secret: $secret_name"
    
    # Extract matching lines, convert to key=value format for kubectl
    local args=""
    while IFS='=' read -r key value; do
        if [ -n "$value" ]; then
            args="$args --from-literal=$key=$value"
        fi
    done < <(grep -E "$patterns" config/.env.production)
    
    kubectl create secret generic "$secret_name" \
        $args \
        -n "$NAMESPACE" \
        --dry-run=client \
        -o yaml | kubectl apply -f -
}

# Create each secret category
create_secret mltb-telegram-secrets "^(BOT_TOKEN|TELEGRAM_API|TELEGRAM_HASH|OWNER_ID)"
create_secret mltb-database-secrets "^DATABASE_"
create_secret mltb-redis-secrets "^REDIS_"
create_secret mltb-rclone-secrets "^RCLONE_"
create_secret mltb-api-secrets "^API_"

# Verify secrets created
echo ""
echo "Verifying secrets..."
kubectl get secrets -n "$NAMESPACE" | grep mltb

echo "✓ All secrets created successfully"
```

### 2.2 Verify Secret Values

```bash
# Verify each secret was created with correct values
kubectl get secret mltb-telegram-secrets -n mltb -o jsonpath='{.data.BOT_TOKEN}' | base64 -d

# Compare with original (first 10 chars)
echo "Original:" $(grep "^BOT_TOKEN=" config/.env.production | cut -d= -f2- | cut -c1-10)...
echo "K8s:      " $(kubectl get secret mltb-telegram-secrets -n mltb -o jsonpath='{.data.BOT_TOKEN}' | base64 -d | cut -c1-10)...
```

### 2.3 Configure Secret Reader Integration

Update application code to use SecretReader:

```bash
# Verify SecretReader is integrated in config manager
grep -n "SecretReader" src/bot/core/config_manager.py

# Update any hardcoded os.environ access to use SecretReader
```

## Phase 3: Validation & Verification

### 3.1 Dry-Run Deployment

```bash
# Test deployment without actually changing anything
kubectl apply -f kubernetes/deployment.yaml --dry-run=client -o yaml

# Check generated manifest
kubectl get deployment -n mltb mltb-app -o yaml | head -100
```

### 3.2 Health Check Validation

```bash
# Start with 1 replica in test mode
kubectl scale deployment/mltb-app --replicas=1 -n mltb

# Wait for pod startup
kubectl wait --for=condition=Ready pod -l app=mltb-app -n mltb --timeout=120s

# Check pod logs for errors
kubectl logs -n mltb -l app=mltb-app --tail=50

# Verify secrets are accessible
kubectl exec -it -n mltb <pod-name> -- env | grep BOT_TOKEN
```

### 3.3 Port Forwarding Test

```bash
# Forward local port to pod
kubectl port-forward -n mltb svc/mltb-app 8080:80 &

# Test health endpoint
curl http://localhost:8080/api/v1/health

# Test data access (should work with secrets)
curl http://localhost:8080/api/v1/status
```

## Phase 4: Cutover & Monitoring

### 4.1 Gradual Rollout

```bash
# Increase replicas gradually
kubectl scale deployment/mltb-app --replicas=3 -n mltb

# Monitor rollout
kubectl rollout status deployment/mltb-app -n mltb --watch

# Watch pods come up
kubectl get pods -n mltb -w
```

### 4.2 Verify All Pods Healthy

```bash
# Check all pods are ready
kubectl get pods -n mltb --no-headers | awk '{print $3}' | sort | uniq -c

# Expected output: 3 pods in "Running" state

# Check no restarts
kubectl get pods -n mltb --no-headers | awk '{print $4}' | sort | uniq -c

# Expected output: All restart counts should be low (< 5)
```

### 4.3 Load Testing

```bash
# Simple load test to verify performance
for i in {1..100}; do
    curl -s http://localhost:8080/api/v1/health | grep -q ok && echo "✓ $i" || echo "✗ $i"
done
```

### 4.4 Monitor Logs

```bash
# Stream logs from all pods
kubectl logs -n mltb -f -l app=mltb-app --all-containers=true

# Watch for errors
kubectl logs -n mltb -f -l app=mltb-app --all-containers=true | grep -i error
```

## Secrets Rotation Integration

### Automated Daily Rclone Token Rotation

```bash
#!/bin/bash
# rotate-rclone-daily.sh - Cron job for daily rclone token refresh

# Run daily at 2 AM UTC
# 0 2 * * * /path/to/rotate-rclone-daily.sh

set -e

NAMESPACE="mltb"
SECRET_NAME="mltb-rclone-secrets"

# Refresh rclone token from auth service
RCLONE_TOKEN=$(curl -s "https://auth.service/rclone/refresh-token" \
    -H "Authorization: Bearer $ADMIN_API_KEY")

if [ -z "$RCLONE_TOKEN" ]; then
    echo "ERROR: Failed to refresh rclone token"
    exit 1
fi

# Rotate with rolling strategy
./kubernetes/rotate-secret.sh \
    "$SECRET_NAME" \
    RCLONE_CONFIG_PATH \
    "$RCLONE_TOKEN" \
    --strategy rolling \
    --namespace "$NAMESPACE"

# Send notification
curl -X POST https://alerts.service/notify \
    -d "Secret '$SECRET_NAME' rotated successfully"
```

### Quarterly Database Password Rotation

```bash
#!/bin/bash
# rotate-db-password-quarterly.sh

NAMESPACE="mltb"
SECRET_NAME="mltb-database-secrets"
NEW_PASSWORD=$(openssl rand -base64 32)

# 1. Update database with new password
# (database must accept both old and new for grace period)

# 2. Rotate in Kubernetes
./kubernetes/rotate-secret.sh \
    "$SECRET_NAME" \
    DATABASE_PASSWORD \
    "$NEW_PASSWORD" \
    --strategy rolling

# 3. Update external monitoring/backups with new credentials
# (run in background after rotation completes)
```

## Monitoring & Alerting

### Prometheus Metrics for Secret Age

```yaml
# Add to Prometheus scrape config in deployment
- alert: SecretRotationOverdue
  expr: |
    (time() - secret_last_rotated_timestamp) > (90 * 24 * 3600)
  for: 10m
  annotations:
    summary: "Secret {{ $labels.secret_name }} not rotated in 90 days"
```

### Audit Logging Setup

```bash
# Enable Kubernetes audit logging
# In etcd configuration, enable API server audit:

--audit-log-path=/var/log/kubernetes/audit.log \
--audit-log-maxage=7 \
--audit-log-maxbackup=10

# View secret access logs
grep "mltb-telegram-secrets" /var/log/kubernetes/audit.log
```

## Rollback Procedure

### Emergency Rollback to Docker Compose

If Kubernetes deployment experiences issues:

```bash
#!/bin/bash
# emergency-rollback.sh

set -e

echo "WARNING: Rolling back to Docker Compose..."

# 1. Scale down Kubernetes deployment
kubectl scale deployment/mltb-app --replicas=0 -n mltb

# 2. Restore from Docker Compose backup
docker-compose -f deployment/docker-compose.yml up -d

# 3. Verify service is healthy
sleep 10
docker-compose -f deployment/docker-compose.yml ps

# 4. Check logs
docker-compose -f deployment/docker-compose.yml logs --tail=50 app

echo "Rollback complete. Running on Docker Compose."
echo "Investigate Kubernetes issues before re-attempting migration."
```

### Gradual Kubernetes Rollback

If specific pod is failing:

```bash
# Restore backup of failed secret
kubectl apply -f /var/log/secret-rotations/backups/mltb-telegram-secrets_20240301_143022.yaml

# Force pod restart with old secret
kubectl rollout restart deployment/mltb-app -n mltb

# Monitor new pods coming up
kubectl get pods -n mltb -w
```

## Troubleshooting Common Issues

### Issue: Pods stuck in CrashLoopBackOff

```bash
# Check failure reason
kubectl describe pod -n mltb <pod-name>

# Common causes:
# 1. Secret not mounted
kubectl get secrets -n mltb | grep mltb-

# 2. Secret permissions issue
kubectl get secret <secret-name> -n mltb -o yaml | grep -A5 "data:"

# 3. Application can't read mounted secret
kubectl exec -it -n mltb <pod-name> -- cat /run/secrets/BOT_TOKEN
```

### Issue: Service unreachable after migration

```bash
# Check service endpoints
kubectl get endpoints mltb-app -n mltb

# Port-forward and test directly
kubectl port-forward -n mltb svc/mltb-app 8080:80

# Check service selector matches pods
kubectl get pods -n mltb --show-labels | grep mltb-app
kubectl get service mltb-app -n mltb -o yaml | grep -A10 "selector:"
```

### Issue: Secret rotation fails

```bash
# Enable debug mode
DRY_RUN=true ./kubernetes/rotate-secret.sh ...

# Check permissions
kubectl auth can-i patch secrets -n mltb
kubectl auth can-i patch deployments -n mltb

# Check script logs
tail -f /var/log/secret-rotations/rotation-history.log
```

## Post-Migration Tasks

- [ ] Archive Docker Compose `.env` files (encrypted, offline backup)
- [ ] Update CI/CD pipelines to use Kubernetes deployment
- [ ] Train team on new secret rotation procedures
- [ ] Document new runbook for common operations
- [ ] Schedule regular security audit of RBAC policies
- [ ] Monitor Kubernetes audit logs for secret access patterns
- [ ] Update disaster recovery procedures

## Success Criteria

Migration is considered successful when:

1. ✅ All 3 application pods running and healthy
2. ✅ Health checks passing consistently (< 1% failure)
3. ✅ Secret access working across all pods
4. ✅ Secret rotation completing without service interruption
5. ✅ Monitoring and alerting functioning
6. ✅ Team confident in operational procedures
7. ✅ Rollback procedure tested and documented

## Support & Questions

- Review [kubernetes/README.md](README.md) for deployment details
- Check [../SECRETS_MANAGEMENT.md](../SECRETS_MANAGEMENT.md) for strategy overview
- Contact platform team for Kubernetes cluster issues
