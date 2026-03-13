# Sealed Secrets Setup Guide

This guide walks through implementing [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) for Kubernetes to encrypt secrets at rest and enable gitops-friendly secret management.

## Overview

**Problem**: Kubernetes secrets are base64-encoded by default, not encrypted. Storing them in git is insecure.

**Solution**: Sealed Secrets encrypts secrets with an asymmetric key so they can be safely committed to git.

The workflow:
1. Generate sealing key (asymmetric) - keep private key secret
2. Create regular Kubernetes secret
3. Seal it with public key → produces SealedSecret
4. Commit SealedSecret to git (safe - encrypted)
5. Cluster controller decrypts with private key and creates Secret

## Installation

### 1. Install Controller

```bash
# Check your Kubernetes version
kubectl version --short

# Install sealed-secrets controller (replace v0.24.0 with latest)
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Verify installation
kubectl get pods -n kube-system | grep sealed-secrets
kubectl logs -n kube-system -l app.kubernetes.io/name=sealed-secrets
```

### 2. Install & Configure kubeseal Client

```bash
# Download kubeseal CLI
wget https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/kubeseal-0.24.0-linux-amd64.tar.gz
tar xfz kubeseal-0.24.0-linux-amd64.tar.gz
sudo mv kubeseal /usr/local/bin/

# Verify installation
kubeseal --version

# Configure kubeseal for mltb namespace (optional - for multi-namespace setup)
kubeseal --fetch-sealing-key -n kube-system > sealing-key-$(date +%s).crt
chmod 600 sealing-key-*.crt
```

## Workflow: Creating Sealed Secrets

### Approach 1: From Environment Variables (Recommended)

```bash
#!/bin/bash
# create-sealed-secrets.sh

NAMESPACE="mltb"
SEALING_KEY="sealing-key.crt"

# Function to seal a secret
seal_secret() {
    local secret_name=$1
    local key=$2
    local value=$3

    # Create unsealed secret locally
    kubectl create secret generic "$secret_name" \
        --from-literal="$key=$value" \
        -n "$NAMESPACE" \
        --dry-run=client \
        -o yaml > /tmp/secret-$secret_name.yaml

    # Seal it
    kubeseal -f /tmp/secret-$secret_name.yaml \
        -w /tmp/sealedsecret-$secret_name.yaml

    # Show sealed secret (safe to commit)
    echo "Sealed secret for $secret_name:"
    cat /tmp/sealedsecret-$secret_name.yaml
    echo ""
}

# Create sealed secrets from environment
seal_secret "mltb-telegram-secrets" "BOT_TOKEN" "$BOT_TOKEN"
seal_secret "mltb-telegram-secrets" "TELEGRAM_API" "$TELEGRAM_API"
seal_secret "mltb-database-secrets" "DATABASE_URL" "$DATABASE_URL"
seal_secret "mltb-redis-secrets" "REDIS_URL" "$REDIS_URL"
```

### Approach 2: From Existing Secret

```bash
# Get existing secret
kubectl get secret mltb-telegram-secrets -n mltb -o yaml

# Seal it
kubectl get secret mltb-telegram-secrets -n mltb -o yaml | \
    kubeseal -f - | \
    tee kubernetes/sealedsecret-mltb-telegram-secrets.yaml

# Apply sealed secret (controller automatically unencrypts)
kubectl apply -f kubernetes/sealedsecret-mltb-telegram-secrets.yaml
```

### Approach 3: Interactive (One Secret at a Time)

```bash
#!/bin/bash
# Create secret interactively

NAMESPACE="mltb"
SECRET_NAME="mltb-telegram-secrets"

echo "Enter secret name: (e.g., mltb-telegram-secrets)"
read SECRET_NAME

echo "Enter key name: (e.g., BOT_TOKEN)"
read KEY

echo "Enter value (will be hidden):"
read -s VALUE

# Create temporary secret
kubectl create secret generic "$SECRET_NAME" \
    --from-literal="$KEY=$VALUE" \
    -n "$NAMESPACE" \
    --dry-run=client \
    -o yaml | kubeseal -f - | \
    tee "sealedsecret-$SECRET_NAME.yaml"

# Cleanup
unset VALUE
```

## Example Sealed Secret Manifests

### Single-Key Sealed Secret

```yaml
# kubernetes/sealedsecret-mltb-telegram-secrets.yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  creationTimestamp: null
  name: mltb-telegram-secrets
  namespace: mltb
spec:
  encryptedData:
    BOT_TOKEN: AgBvL3z8a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5t6u7...
    TELEGRAM_API: AgBxM4z9e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x...
    TELEGRAM_HASH: AgC2N5a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v...
  template:
    metadata:
      creationTimestamp: null
      name: mltb-telegram-secrets
      namespace: mltb
    type: Opaque
```

When applied, sealed-secrets controller automatically creates:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mltb-telegram-secrets
  namespace: mltb
type: Opaque
data:
  BOT_TOKEN: <base64 encoded actual value>
  TELEGRAM_API: <base64 encoded actual value>
  TELEGRAM_HASH: <base64 encoded actual value>
```

### Multi-Key Sealed Secret Setup

```yaml
# kubernetes/sealedsecret-mltb-database-secrets.yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: mltb-database-secrets
  namespace: mltb
spec:
  encryptedData:
    DATABASE_URL: AgBxM4z9e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x...
    DATABASE_USERNAME: AgBvL3z8a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5t6u7...
    DATABASE_PASSWORD: AgC2N5a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v...
  template:
    metadata:
      name: mltb-database-secrets
      namespace: mltb
    type: Opaque
```

## GitOps Integration

### Structure for Git Repository

```
deployment/
├── kubernetes/
│   ├── namespace.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── sealedsecrets/
│       ├── sealedsecret-mltb-telegram-secrets.yaml
│       ├── sealedsecret-mltb-database-secrets.yaml
│       ├── sealedsecret-mltb-redis-secrets.yaml
│       └── sealedsecret-mltb-rclone-secrets.yaml
└── kustomization.yaml
```

### Kustomization with Sealed Secrets

```yaml
# kubernetes/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: mltb

resources:
- namespace.yaml
- deployment.yaml
- service.yaml
- sealedsecrets/sealedsecret-mltb-telegram-secrets.yaml
- sealedsecrets/sealedsecret-mltb-database-secrets.yaml
- sealedsecrets/sealedsecret-mltb-redis-secrets.yaml

commonLabels:
  app: mltb-app
  secrets-management: sealed-secrets
```

### Deploy with ArgoCD

```yaml
# argocd/mltb-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: mltb-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/mltb-deployment
    targetRevision: main
    path: kubernetes/
  destination:
    server: https://kubernetes.default.svc
    namespace: mltb
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    # Allow creating SealedSecret CRD if it doesn't exist
    - CreateNamespace=true
```

## Security Best Practices

### 1. Sealing Key Management

```bash
# Back up private sealing key (keep secure!)
kubectl get secret -n kube-system sealed-secrets-key -o yaml > \
    sealing-key-backup-$(date +%Y%m%d).yaml
chmod 600 sealing-key-backup-*.yaml

# Store safely (encrypted, offline, separate from repo)
# - AWS Secrets Manager
# - HashiCorp Vault
# - Offline encrypted USB

# Disaster recovery: Restore from backup
kubectl apply -f sealing-key-backup-20260301.yaml
```

### 2. RBAC for Sealed Secrets

```yaml
# kubernetes/sealedsecrets-rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: sealed-secrets-reader
rules:
- apiGroups:
  - bitnami.com
  resources:
  - sealedsecrets
  verbs:
  - get
  - list
  - watch

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: sealed-secrets-reader-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: sealed-secrets-reader
subjects:
- kind: ServiceAccount
  name: default
  namespace: mltb
```

### 3. Sensitive Sealing Key Rotation

```bash
#!/bin/bash
# rotate-sealing-key.sh - Advanced: Generate new sealing key

# Warning: This breaks all existing sealed secrets!
# Only do this in security incident or key compromise

NAMESPACE="kube-system"

# 1. Backup old key
kubectl get secret -n "$NAMESPACE" sealed-secrets-key -o yaml > \
    sealing-key-old-$(date +%s).yaml
chmod 600 sealing-key-old-*.yaml

# 2. Delete old key
kubectl delete secret sealed-secrets-key -n "$NAMESPACE"

# 3. Restart controller (generates new key)
kubectl delete pod -n "$NAMESPACE" -l app.kubernetes.io/name=sealed-secrets

# 4. Wait for new key generation
sleep 10
kubectl get secret -n "$NAMESPACE" sealed-secrets-key

# 5. Re-seal all secrets with new key
# Must re-encrypt all existing SealedSecrets
echo "⚠️  All existing SealedSecrets must be re-encrypted with new key"
```

## Multi-Namespace Setup

For organizations with multiple environments:

```bash
#!/bin/bash
# Use different sealing keys per namespace for isolation

# Production namespace
kubectl create secret generic sealed-secrets-key \
    -n kube-system-prod \
    --from-file=tls.crt=prod-sealing-key.crt \
    --from-file=tls.key=prod-sealing-key.key

# Staging namespace
kubectl create secret generic sealed-secrets-key \
    -n kube-system-staging \
    --from-file=tls.crt=staging-sealing-key.crt \
    --from-file=tls.key=staging-sealing-key.key

# Seal secrets with scope to namespace
kubeseal --scope namespace-wide -f secret.yaml -o yaml
```

## Troubleshooting

### Cannot unseal sealed secret

```bash
# 1. Verify controller is running
kubectl get pods -n kube-system | grep sealed-secrets

# 2. Check controller logs
kubectl logs -n kube-system -l app.kubernetes.io/name=sealed-secrets

# 3. Verify sealed secret format
kubectl get sealedsecret -n mltb

# 4. Check if using wrong sealing key
# If key was rotated, must re-seal secrets

# 5. Verify namespace matches
# Sealed secrets are namespace-scoped by default
```

### Sealed secret not creating underlying secret

```bash
# Check events
kubectl describe sealedsecret mltb-telegram-secrets -n mltb

# Check if controller has permission
kubectl get clusterrole | grep sealed-secrets

# Verify Secret wasn't created with different name
kubectl get secrets -n mltb | grep telegram
```

## Comparison: Sealed Secrets vs Alternatives

| Approach | Encryption | RBAC | GitOps | Complexity |
|---|---|---|---|---|
| **Sealed Secrets** | ✅ At rest | Limited | ✅ Yes | Low |
| **External Secrets Operator** | ✅ In Vault | ✅ Full | ✅ Yes | Medium |
| **Kyverno + Vault** | ✅ In Vault | ✅ Full | ✅ Yes | High |
| **Plain K8s Secrets** | ❌ Base64 only | ✅ Full | ⚠️ Unsafe | Very Low |

## Next Steps

1. ✅ Install sealed-secrets controller
2. ✅ Generate and backup sealing key
3. ✅ Seal existing secrets
4. ✅ Commit to git
5. ✅ Set up ArgoCD for automatic deployment
6. ⏳ Monitor secret rotation
7. ⏳ Plan key rotation schedule

## Related Documentation

- [Sealed Secrets GitHub](https://github.com/bitnami-labs/sealed-secrets)
- [Kubernetes Secrets Management](../SECRETS_MANAGEMENT.md)
- [Kubernetes Deployment Guide](./kubernetes/README.md)
- [Secret Rotation Guide](./kubernetes/rotate-secret.sh)
