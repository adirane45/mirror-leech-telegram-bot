#!/bin/bash

# Kubernetes Secret Rotation Script
#
# Manages zero-downtime secret rotation in Kubernetes
# Supports multiple rotation strategies:
# 1. In-place: Update secret, pods restart on new image pull
# 2. Rolling: Coordinate controlled pod restart
# 3. Blue-green: Deploy version B, switch traffic, retire version A
#
# Usage:
#   ./rotate-secret.sh <secret-name> <key> <new-value> [--strategy rolling|blue-green|immediate]

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${NAMESPACE:-mltb}"
ROTATION_LOG_DIR="/var/log/secret-rotations"
KUBECTL="${KUBECTL:-kubectl}"
DRY_RUN="${DRY_RUN:-false}"
STRATEGY="${STRATEGY:-rolling}"

# Function to print colored output
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Function to validate prerequisites
validate_prerequisites() {
    log_info "Validating prerequisites..."

    # Check kubectl is available
    if ! command -v "$KUBECTL" &> /dev/null; then
        log_error "kubectl not found"
        exit 1
    fi

    # Check namespace exists
    if ! $KUBECTL get namespace "$NAMESPACE" &> /dev/null; then
        log_error "Namespace '$NAMESPACE' does not exist"
        exit 1
    fi

    # Check if user has permissions
    if ! $KUBECTL auth can-i update secrets -n "$NAMESPACE" &> /dev/null; then
        log_error "Insufficient permissions to update secrets in namespace '$NAMESPACE'"
        exit 1
    fi

    log_success "Prerequisites validated"
}

# Function to validate secret exists
validate_secret() {
    local secret_name=$1
    local key=$2

    if ! $KUBECTL get secret "$secret_name" -n "$NAMESPACE" &> /dev/null; then
        log_error "Secret '$secret_name' not found in namespace '$NAMESPACE'"
        exit 1
    fi

    if ! $KUBECTL get secret "$secret_name" -n "$NAMESPACE" -o jsonpath="{.data.$key}" &> /dev/null; then
        log_error "Key '$key' not found in secret '$secret_name'"
        exit 1
    fi
}

# Function to get current secret value
get_secret_value() {
    local secret_name=$1
    local key=$2

    $KUBECTL get secret "$secret_name" -n "$NAMESPACE" \
        -o jsonpath="{.data.$key}" | base64 -d 2>/dev/null || echo ""
}

# Function to create backup of current secret
backup_secret() {
    local secret_name=$1
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="$ROTATION_LOG_DIR/backups"

    mkdir -p "$backup_dir"

    local backup_file="$backup_dir/${secret_name}_${timestamp}.yaml"

    log_info "Creating backup of secret to $backup_file..."

    $KUBECTL get secret "$secret_name" -n "$NAMESPACE" -o yaml > "$backup_file"
    chmod 600 "$backup_file"

    log_success "Backup created: $backup_file"
    echo "$backup_file"
}

# Function to patch secret with new value (dry-run or real)
patch_secret() {
    local secret_name=$1
    local key=$2
    local new_value=$3

    log_info "Patching secret '$secret_name' with new value for key '$key'..."

    # Encode new value to base64
    local encoded_value=$(echo -n "$new_value" | base64 -w0)

    local patch_cmd="$KUBECTL patch secret $secret_name -n $NAMESPACE -p '{\"data\":{\"$key\":\"$encoded_value\"}}'"

    if [ "$DRY_RUN" = "true" ]; then
        log_warn "DRY RUN: Would execute: $patch_cmd"
    else
        eval "$patch_cmd"
        log_success "Secret patched successfully"
    fi
}

# Function to get deployments using this secret
get_deployments_using_secret() {
    local secret_name=$1

    $KUBECTL get deployments -n "$NAMESPACE" -o json | \
        jq -r ".items[] | select(.spec.template.spec |
            (.containers[].env[]? | select(.valueFrom.secretKeyRef.name==\"$secret_name\") | .name) or
            (.containers[].volumeMounts[]? | .name) or
            (.volumes[]? | select(.secret.secretName==\"$secret_name\") | .name)) | .metadata.name" | \
        sort -u
}

# Function to trigger immediate pod restart (rolling update)
trigger_rolling_restart() {
    local secret_name=$1
    local timestamp=$(date +%s)

    log_info "Triggering rolling restart of pods using secret '$secret_name'..."

    local deployments=$(get_deployments_using_secret "$secret_name")

    if [ -z "$deployments" ]; then
        log_warn "No deployments found using secret '$secret_name'"
        return 0
    fi

    while IFS= read -r deployment; do
        log_info "Rolling restart of deployment: $deployment"

        if [ "$DRY_RUN" = "true" ]; then
            log_warn "DRY RUN: Would restart deployment '$deployment'"
        else
            # Trigger rollout using annotation update (forces pod restart)
            $KUBECTL rollout restart deployment/"$deployment" -n "$NAMESPACE"

            # Wait for rollout to complete
            $KUBECTL rollout status deployment/"$deployment" -n "$NAMESPACE" --timeout=5m
        fi
    done <<< "$deployments"

    log_success "Rolling restart completed"
}

# Function for blue-green deployment strategy
rotate_with_blue_green() {
    local secret_name=$1
    local key=$2
    local new_value=$3

    log_info "Executing blue-green rotation strategy..."

    local green_version=$(date +%s)
    local blue_label="rotation-blue"
    local green_label="rotation-green-$green_version"

    # Get current deployment selector
    local current_deployment=$($KUBECTL get deployment -n "$NAMESPACE" \
        -l "app=mltb-app,version=v1" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

    if [ -z "$current_deployment" ]; then
        log_error "Could not find deployment to rotate"
        exit 1
    fi

    # Create green environment with new secret
    log_info "Creating green environment with new secret..."

    if [ "$DRY_RUN" != "true" ]; then
        # Clone deployment as green
        $KUBECTL get deployment "$current_deployment" -n "$NAMESPACE" -o yaml | \
            sed "s/labels:.*/labels:\n        app: mltb-app\n        deployment-version: $green_label/" | \
            sed 's/name: .*/name: mltb-app-green-'"$green_version"'/' | \
            $KUBECTL apply -f -

        log_info "Waiting for green deployment to be ready..."
        $KUBECTL rollout status deployment/"mltb-app-green-$green_version" \
            -n "$NAMESPACE" --timeout=5m
    fi

    # Switch traffic to green (update service selector)
    log_info "Switching traffic from blue to green..."
    if [ "$DRY_RUN" != "true" ]; then
        $KUBECTL patch service mltb-app -n "$NAMESPACE" \
            -p '{"spec":{"selector":{"deployment-version":"'"$green_label"'"}}}'
    fi

    # Monitor green for health
    log_info "Monitoring green deployment health (30s)..."
    sleep 30

    # Check if green is healthy
    local green_status=$($KUBECTL get deployment "mltb-app-green-$green_version" -n "$NAMESPACE" \
        -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    local green_desired=$($KUBECTL get deployment "mltb-app-green-$green_version" -n "$NAMESPACE" \
        -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")

    if [ "$green_status" != "$green_desired" ]; then
        log_error "Green deployment failed health check. Rolling back to blue..."
        if [ "$DRY_RUN" != "true" ]; then
            $KUBECTL patch service mltb-app -n "$NAMESPACE" \
                -p '{"spec":{"selector":{"deployment-version":"'"$blue_label"'"}}}'
            $KUBECTL delete deployment "mltb-app-green-$green_version" -n "$NAMESPACE"
        fi
        exit 1
    fi

    # Clean up blue deployment
    log_info "Cleaning up old blue deployment..."
    if [ "$DRY_RUN" != "true" ]; then
        $KUBECTL delete deployment "$current_deployment" -n "$NAMESPACE"
    fi

    log_success "Blue-green rotation completed successfully"
}

# Function to validate new secret works
validate_secret_rotation() {
    local secret_name=$1
    local key=$2
    local expected_value=$3

    log_info "Validating secret rotation..."

    # Wait for pods to restart and pick up new secret
    sleep 5

    # Get updated value from secret
    local current_value=$(get_secret_value "$secret_name" "$key")

    if [ "$current_value" = "$expected_value" ]; then
        log_success "Secret validation passed"
        return 0
    else
        log_error "Secret validation failed: value mismatch"
        return 1
    fi
}

# Function to log rotation event
log_rotation_event() {
    local secret_name=$1
    local key=$2
    local old_value=$3
    local new_value=$4
    local strategy=$5
    local status=$6

    mkdir -p "$ROTATION_LOG_DIR"

    local log_file="$ROTATION_LOG_DIR/rotation-history.log"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    cat >> "$log_file" << EOF
{
  "timestamp": "$timestamp",
  "namespace": "$NAMESPACE",
  "secret": "$secret_name",
  "key": "$key",
  "old_value_hash": "$(echo -n "$old_value" | sha256sum | awk '{print $1}')",
  "new_value_hash": "$(echo -n "$new_value" | sha256sum | awk '{print $1}')",
  "strategy": "$strategy",
  "status": "$status",
  "user": "${USER:-unknown}",
  "hostname": "$(hostname)"
}
EOF

    chmod 600 "$log_file"
}

# Function to display help
show_help() {
    cat << EOF
Usage: $0 <secret-name> <key> <new-value> [OPTIONS]

Rotates a Kubernetes secret with zero-downtime restart capability.

Positional Arguments:
  secret-name     Name of the secret to rotate
  key             Key within the secret to rotate
  new-value       New value for the key

Options:
  --strategy      Rotation strategy (default: rolling)
                  - rolling: Controlled rolling restart of pods
                  - blue-green: Deploy new version, switch traffic, retire old
                  - immediate: Fast rotation, pods restart immediately
  --namespace     Kubernetes namespace (default: mltb)
  --dry-run       Show what would be done without making changes
  --help          Show this help message

Environment Variables:
  NAMESPACE       Override namespace (default: mltb)
  KUBECTL         Path to kubectl binary (default: kubectl)
  DRY_RUN         Set to 'true' for dry-run mode

Examples:
  # Rotate BOT_TOKEN in mltb namespace
  $0 mltb-telegram-secrets BOT_TOKEN "new-token-value"

  # Dry-run rotation with blue-green strategy
  DRY_RUN=true $0 mltb-telegram-secrets BOT_TOKEN "new-token" --strategy blue-green

  # Rotate RCLONE_TOKEN_DROPBOX and show what would happen
  NAMESPACE=production $0 mltb-rclone-secrets RCLONE_TOKEN_DROPBOX "new-token" --dry-run

EOF
}

# Parse arguments
if [ $# -lt 3 ]; then
    show_help
    exit 1
fi

SECRET_NAME=$1
KEY=$2
NEW_VALUE=$3
shift 3

while [[ $# -gt 0 ]]; do
    case $1 in
        --strategy)
            STRATEGY="$2"
            shift 2
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main rotation logic
main() {
    log_info "Starting secret rotation: $SECRET_NAME"
    log_info "Strategy: $STRATEGY"

    if [ "$DRY_RUN" = "true" ]; then
        log_warn "DRY RUN MODE - No changes will be made"
    fi

    # Validate prerequisites
    validate_prerequisites

    # Validate secret exists
    validate_secret "$SECRET_NAME" "$KEY"

    # Get current value for backup
    local old_value=$(get_secret_value "$SECRET_NAME" "$KEY")
    log_info "Current value (hash): $(echo -n "$old_value" | sha256sum | awk '{print $1}')"

    # Create backup
    backup_secret "$SECRET_NAME"

    # Patch secret with new value
    patch_secret "$SECRET_NAME" "$KEY" "$NEW_VALUE"

    # Execute rotation strategy
    case "$STRATEGY" in
        rolling)
            trigger_rolling_restart "$SECRET_NAME"
            ;;
        blue-green)
            rotate_with_blue_green "$SECRET_NAME" "$KEY" "$NEW_VALUE"
            ;;
        immediate)
            log_info "Using immediate rotation (pods will pick up changes at next restart)"
            ;;
        *)
            log_error "Unknown strategy: $STRATEGY"
            exit 1
            ;;
    esac

    # Validate rotation
    validate_secret_rotation "$SECRET_NAME" "$KEY" "$NEW_VALUE" || exit 1

    # Log rotation event
    log_rotation_event "$SECRET_NAME" "$KEY" "$old_value" "$NEW_VALUE" "$STRATEGY" "success"

    log_success "Secret rotation completed successfully"
    log_info "Backup saved at: $(backup_secret "$SECRET_NAME" 2>/dev/null || echo 'N/A')"
}

# Run main function
main
