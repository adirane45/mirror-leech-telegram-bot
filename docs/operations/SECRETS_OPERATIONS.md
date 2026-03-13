# MLTB Secrets Management Operations Guide

Complete operational runbook for secrets management across all deployment scenarios and lifecycle positions (creation, rotation, emergency recovery).

## Quick Start (Choose Your Path)

### 🚀 Path 1: Simple Kubernetes Deployment (5 minutes)

Use for development or simple single-cluster deployments.

```bash
# 1. Create namespace
kubectl apply -f kubernetes/namespace.yaml

# 2. Create secrets
kubectl create secret generic mltb-telegram-secrets \
  --from-literal=BOT_TOKEN="$BOT_TOKEN" \
  -n mltb

# 3. Deploy
kubectl apply -f kubernetes/deployment.yaml
```

No additional setup needed. Secrets stored as base64 in etcd.

### 🔐 Path 2: Encrypted Secrets (GitOps) (15 minutes)

Use for production with git-based deployment.

```bash
# 1. Install sealed-secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# 2. Follow: docs/operations/SEALED_SECRETS_SETUP.md

# 3. Create sealed secrets
kubeseal -f secret.yaml -w sealedsecret.yaml

# 4. Commit to git (safe - encrypted)
git add kubernetes/sealedsecrets/
git commit -m "secrets: add encrypted secrets"
```

Encrypted with RSA-4096 key. Safe to commit to git.

### 🔄 Path 3: Automated Rotation (30 minutes)

Use for production requiring automatic credential refresh.

```bash
# 1. Deploy base infrastructure (Paths 1 or 2)

# 2. Deploy CronJobs for scheduled rotation
kubectl apply -f kubernetes/cronjobs.yaml

# 3. Configure rotation scripts
./kubernetes/rotate-secret.sh --help

# 4. (Optional) Deploy monitoring
kubectl apply -f kubernetes/monitoring/secret-alerts.yaml
```

Enables:
- Daily Rclone token refresh
- Quarterly database password rotation
- Weekly health checks
- Prometheus alerts

### 🏢 Path 4: Enterprise with Vault (1-2 hours)

Use for multi-team, multi-environment, audit-heavy deployments.

```bash
# 1. Install External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets

# 2. Configure Vault
# Create AppRole: vault write auth/approle/role/mltb-app ...

# 3. Deploy ExternalSecrets
kubectl apply -f kubernetes/external-secrets/examples.yaml

# 4. (Optional) Deploy monitoring
kubectl apply -f kubernetes/monitoring/secret-alerts.yaml
```

Enables:
- Auto-rotation with HSM encryption
- Multi-environment management
- Audit logging
- Time-based password policies

---

## Secrets Inventory

### Telegram Bot Configuration

**Secret Name**: `mltb-telegram-secrets`
**Rotation**: Daily (optional, recommended if token expires)
**Impact**: High - Affects all user interactions
**Recovery**: Switch to backup bot token

Keys:
- `BOT_TOKEN` - Telegram bot token from @BotFather
- `TELEGRAM_API` - Telegram API ID
- `TELEGRAM_HASH` - Telegram API hash
- `OWNER_ID` - Telegram user ID of bot owner
- `AUTHORIZED_CHATS` - Comma-separated chat IDs

### Database Credentials

**Secret Name**: `mltb-database-secrets`
**Rotation**: Quarterly (90-day intervals)
**Impact**: Critical - All data access blocked if wrong
**Recovery**: Use read-only replica, update from backup

Keys:
- `DATABASE_URL` - Connection string (mongodb://user:pass@host:port/db)
- `DATABASE_USERNAME` - Username
- `DATABASE_PASSWORD` - Password

### Redis Cache

**Secret Name**: `mltb-redis-secrets`
**Rotation**: Quarterly (90-day intervals)
**Impact**: Medium - Cache misses but no data loss
**Recovery**: Clear cache, restart pods

Keys:
- `REDIS_URL` - Connection string (redis://:password@host:port/0)
- `REDIS_PASSWORD` - Password

### Rclone Cloud Storage

**Secret Name**: `mltb-rclone-secrets`
**Rotation**: Daily (tokens expire regularly)
**Impact**: High - Cloud uploads fail without valid token
**Recovery**: Use alternative cloud provider or offline storage

Keys:
- `RCLONE_CONFIG_PATH` - Path to rclone.conf
- Individual provider tokens (DROPBOX, GDRIVE, ONEDRIVE, etc.)

### API Keys

**Secret Name**: `mltb-api-secrets`
**Rotation**: Quarterly or on security incident
**Impact**: Medium - External integrations fail
**Recovery**: Generate new key, update clients

Keys:
- `API_SECRET_KEY` - HMAC signing key for API tokens
- `ADMIN_API_KEY` - Admin operations access

### SSL/TLS Certificates

**Secret Name**: `mltb-ssl-secrets`
**Rotation**: Before expiry (yearly or per cert validity)
**Impact**: High - HTTPS connections fail
**Recovery**: Use self-signed cert temporarily, get real cert ASAP

Keys:
- `tls.crt` - Certificate file
- `tls.key` - Private key

---

## Daily Operations

### Checking Secret Status

```bash
# List all secrets in mltb namespace
kubectl get secrets -n mltb

# View secret details (redacted)
kubectl describe secret mltb-telegram-secrets -n mltb

# Check secret age (if using monitoring)
kubectl get event -n mltb | grep secret

# View recent secret access logs
kubectl logs -n kube-system -l app=kubernetes-audit | grep secret | tail -20
```

### Manual Secret Rotation

#### Standard Rotation (No Service Interruption)

```bash
# Rotate Rclone token (example)
NEW_TOKEN="new-rclone-token-value"

./kubernetes/rotate-secret.sh \
  mltb-rclone-secrets \
  RCLONE_CONFIG_PATH \
  "$NEW_TOKEN" \
  --strategy rolling

# Process:
# 1. Secret updated in Kubernetes
# 2. Pods restart one at a time
# 3. Service stays up throughout
# 4. Backup created automatically
```

#### Emergency Rotation (Blue-Green)

```bash
# For critical secrets requiring maximum safety
./kubernetes/rotate-secret.sh \
  mltb-telegram-secrets \
  BOT_TOKEN \
  "emergency-token" \
  --strategy blue-green

# Process:
# 1. Secret updated
# 2. New pods start with new secret
# 3. Health checks verify new version
# 4. Traffic switches to new pods
# 5. Old pods terminated
# 6. Can rollback instantly if needed
```

#### Immediate Rotation (Non-Critical)

```bash
# For non-critical secrets or low-impact changes
./kubernetes/rotate-secret.sh \
  mltb-api-secrets \
  API_KEY \
  "new-api-key" \
  --strategy immediate

# Process:
# 1. Secret updated immediately
# 2. Pods pick up new value at next restart
# 3. No forced restart
# 4. Less disruptive
```

### Verifying Secret Values

```bash
# Decode a secret value (be careful - not for sensitive viewing)
kubectl get secret mltb-telegram-secrets -n mltb \
  -o jsonpath='{.data.BOT_TOKEN}' | base64 -d

# Or use SecretReader from app container
kubectl exec -it <pod-name> -n mltb -- python3 << 'EOF'
from src.bot.core.secret_reader import SecretReader
print(SecretReader.get_secret("BOT_TOKEN"))
EOF

# Compare old vs new value (hash only for security)
echo "Old: $(echo 'old-value' | sha256sum)"
echo "New: $(echo 'new-value' | sha256sum)"
```

---

## Monitoring & Alerting

### Prometheus Metrics

Available metrics (deployed with `kubernetes/monitoring/secret-alerts.yaml`):

```promql
# Secret age in days
mltb:secret:age_in_days

# Rotation success rate
secret_rotation:success_rate

# Average rotation time
secret_rotation:avg_time_seconds

# Access patterns
secret_read_total
secret_access_denied_total

# Storage capacity
secret_storage_bytes_used
secret_storage_bytes_limit
```

### Alert Examples

```bash
# Setup Grafana dashboard
kubectl port-forward -n mltb svc/prometheus 9090:9090
# http://localhost:9090 > Alerts tab

# View active alerts
kubectl get alertring -n mltb

# Check alert rules
kubectl logs -n monitoring prometheus-<pod>
```

### Common Alerts

| Alert | Severity | Threshold | Action |
|-------|----------|-----------|--------|
| Secret > 30 days | Warning | 720 hours | Check rotation schedule |
| Secret > 60 days | Critical | 1440 hours | Manual rotation required |
| Rotation failed | High | > 5 attempts/hour | Check job logs |
| Backend unreachable | High | 5 min | Verify network/Vault |
| RBAC denied | Warning | > 5 attempts/hour | Review permissions |

---

## Troubleshooting

### Pod CrashLoopBackOff Due to Missing Secrets

```bash
# Check pod logs
kubectl logs -n mltb <pod-name> --tail=100

# Expected error: "ERROR: BOT_TOKEN not set"

# Solutions:
# 1. Verify secret exists
kubectl get secret mltb-telegram-secrets -n mltb

# 2. Verify pod can access secret
kubectl exec <pod-name> -n mltb -- env | grep BOT_TOKEN_FILE

# 3. Check RBAC permissions
kubectl get rolebinding -n mltb
kubectl get clusterrolebinding | grep mltb

# 4. Manually mount secret to test
kubectl run -it debug --image=alpine -n mltb -- sh
```

### Secret Rotation Failed

```bash
# Check rotation history
tail -f /var/log/secret-rotations/rotation-history.log

# Run rotation in dry-run mode to debug
DRY_RUN=true ./kubernetes/rotate-secret.sh \
  mltb-telegram-secrets \
  BOT_TOKEN \
  "test-value"

# Check rotation job status
kubectl get cronjob -n mltb
kubectl describe cronjob mltb-secret-rotation-rclone-daily -n mltb

# View job output
kubectl logs -n mltb -l cronjob-name=mltb-secret-rotation-rclone-daily
```

### Authentication Failures After Rotation

```bash
# Check if pods are using new secret
kubectl exec <pod-name> -n mltb -- cat /run/secrets/bot_token

# Verify value matches current secret
kubectl get secret mltb-telegram-secrets -n mltb \
  -o jsonpath='{.data.BOT_TOKEN}' | base64 -d

# If mismatch, force pod restart
kubectl rollout restart deployment/mltb-app -n mltb

# Wait for new pods
kubectl get pods -n mltb -w
```

### Secrets Not Being Rotated Automatically

```bash
# Check CronJob status
kubectl get cronjob -n mltb

# View CronJob details
kubectl describe cronjob mltb-secret-rotation-rclone-daily -n mltb

# Check last execution
kubectl get jobs -n mltb --sort-by=.metadata.creationTimestamp

# View job logs
kubectl logs -n mltb job/mltb-secret-rotation-rclone-daily-<timestamp>

# Manually trigger rotation
kubectl create job --from=cronjob/mltb-secret-rotation-rclone-daily \
  manual-rotation-test -n mltb
```

---

## Advanced Operations

### Sealing a Secret for Git Storage

See [docs/operations/SEALED_SECRETS_SETUP.md](./SEALED_SECRETS_SETUP.md) for detailed guide.

```bash
# Quick seal
kubectl create secret generic mltb-secrets \
  --from-literal=BOT_TOKEN="$BOT_TOKEN" \
  -n mltb --dry-run=client -o yaml | kubeseal -f - > sealedsecret.yaml

# Apply sealed secret (controller decrypts)
kubectl apply -f sealedsecret.yaml

# Commit to git (safe - encrypted)
git add kubernetes/sealedsecrets/
```

### Integrating with HashiCorp Vault

See [kubernetes/external-secrets/examples.yaml](../external-secrets/examples.yaml) for detailed configuration.

```bash
# Install External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets

# Create AppRole in Vault
vault write auth/approle/role/mltb-app ...

# Deploy ExternalSecret (pulls from Vault automatically)
kubectl apply -f kubernetes/external-secrets/examples.yaml
```

### Resealing All Secrets After Key Rotation

```bash
#!/bin/bash
# For sealed-secrets key rotation (security incident)

# 1. Back up old key
kubectl get secret -n kube-system sealed-secrets-key -o yaml > \
  sealed-secrets-key-backup-$(date +%s).yaml

# 2. Delete old key (controller generates new one)
kubectl delete secret -n kube-system sealed-secrets-key

# 3. Restart controller
kubectl rollout restart deployment -n kube-system sealed-secrets

# 4. Wait for new key
sleep 30
kubeseal --fetch-sealing-key > new-sealing-key.crt

# 5. Re-seal all secrets
for secret in sealedsecret-*.yaml; do
  kubectl get secret ${secret%-sealedsecret.yaml} -n mltb -o yaml | \
    kubeseal -f - > $secret
done

# 6. Apply re-sealed secrets
kubectl apply -f sealedsecret-*.yaml
```

---

## Security Best Practices

1. **Principle of Least Privilege**
   - Pods only read their required secrets
   - ServiceAccounts have minimal RBAC roles
   - External backends (Vault) require authentication

2. **Encryption at Rest**
   - Use sealed-secrets or HashiCorp Vault in production
   - Enable etcd encryption: `--encryption-provider-config`
   - Audit all secret access: `--audit-log-path`

3. **Rotation Schedule**
   - Bot tokens: Daily (if expiry) or quarterly
   - Database passwords: Quarterly (90 days)
   - API keys: Quarterly or per incident
   - Certificates: Before expiry (annually)

4. **Audit Logging**
   - Track all secret access (who, when, what)
   - Monitor for suspicious patterns
   - Alert on unauthorized access attempts

5. **Disaster Recovery**
   - Backup sealing keys offline (Vault) or HSM
   - Test restore procedure quarterly
   - Keep backup credentials separate from production

6. **Workspace Hygiene**
   - Never log secrets in stdout/files
   - Clear bash history after secret operations
   - Use `set +x` in scripts to hide commands

---

## Runbooks

### Runbook 1: Regular Secret Rotation

**Objective**: Rotate secrets on schedule
**Frequency**: Automated via CronJobs
**Manual Trigger**: When needed

Steps:
1. CronJob runs daily at 2 AM UTC
2. Pulls new token from auth service
3. Calls rotate-secret.sh with rolling strategy
4. Pods restart gradually
5. Service continues uninterrupted

Manual execution:
```bash
./kubernetes/rotate-secret.sh mltb-rclone-secrets RCLONE_CONFIG_PATH "$NEW_TOKEN"
```

### Runbook 2: Emergency Secret Rotation

**Objective**: Rotate compromised secret with maximum safety
**Trigger**: Security incident, suspected compromise
**Duration**: 5-10 minutes

Steps:
1. Immediately disable affected service (if critical)
2. Rotate secret with blue-green strategy
3. Verify new version is healthy
4. Monitor for any issues
5. Keep old version for 5 minutes for rollback
6. Document incident

```bash
./kubernetes/rotate-secret.sh mltb-telegram-secrets BOT_TOKEN \
  "emergency-token" --strategy blue-green
```

### Runbook 3: Restore from Backup

**Objective**: Recover from accidental secret deletion
**Trigger**: Deletion error, data corruption

Steps:
1. Identify affected secret (check rotation history)
2. Locate backup file
3. Apply backup (creates old secret)
4. Verify pods can now communicate
5. Plan re-rotation with new value

```bash
# List backups
ls -lh /var/log/secret-rotations/backups/

# Restore specific backup
kubectl apply -f /var/log/secret-rotations/backups/mltb-telegram-secrets_20260301_020000.yaml

# Verify secret restored
kubectl get secret mltb-telegram-secrets -n mltb -o yaml
```

---

## Performance Tuning

### Secret Sync Frequency

```yaml
# In kubernetes/cronjobs.yaml - Adjust refresh intervals

spec:
  refreshInterval: 1h    # Check Vault every hour
  - For frequently rotating tokens: 30m
  - For stable secrets: 24h
```

### Reducing Pod Restart Time

```yaml
# In kubernetes/deployment.yaml - Optimize readiness probe

readinessProbe:
  initialDelaySeconds: 5     # Start checking early
  periodSeconds: 3           # Check frequently
  timeoutSeconds: 2          # Fail fast
  failureThreshold: 2        # Take pod down quickly
```

---

## Related Documentation

- [kubernetes/README.md](../kubernetes/README.md) - Deployment guide
- [SECRETS_MANAGEMENT.md](../SECRETS_MANAGEMENT.md) - Strategy overview
- [docs/operations/SEALED_SECRETS_SETUP.md](./SEALED_SECRETS_SETUP.md) - Encryption at rest
- [docs/operations/KUBERNETES_MIGRATION.md](./KUBERNETES_MIGRATION.md) - Migration from .env files
- [kubernetes/rotate-secret.sh](../kubernetes/rotate-secret.sh) - Rotation script guide
- [kubernetes/cronjobs.yaml](../kubernetes/cronjobs.yaml) - Scheduled rotation configuration

---

## Support & Escalation

**Tier 1 - Monitoring Alerts**: Automatically sent to Slack/PagerDuty
**Tier 2 - Operational Issues**: Check troubleshooting section above
**Tier 3 - Secrets Compromise**: Execute Emergency Secret Rotation runbook
**Tier 4 - Infrastructure Issues**: Contact platform/SRE team

---

## Appendix: Configuration Reference

### Environment Variables for rotate-secret.sh

```bash
NAMESPACE="mltb"              # K8s namespace
KUBECTL="/usr/local/bin/kubectl"  # kubectl path
DRY_RUN="false"               # Preview mode (true = no changes)
STRATEGY="rolling"            # rotating|blue-green|immediate
```

### CronJob Schedule Reference

```
# Format: minute hour day month weekday
# Ranges: 0-59   0-23  1-31  1-12   0-7
# Common patterns:

0 2 * * *       # Daily at 2 AM
0 3 1 1,4,7,10  # Quarterly (1st of Jan, Apr, Jul, Oct)
0 1 * * 1       # Weekly on Monday at 1 AM
0 */6 * * *     # Every 6 hours
```

---

Last updated: March 1, 2026
