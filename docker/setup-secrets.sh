#!/bin/bash
# Docker Secrets Management Script
#
# Usage:
#   ./docker/setup-secrets.sh create <secret_name> <secret_value>
#   ./docker/setup-secrets.sh rotate <secret_name> <new_value>
#   ./docker/setup-secrets.sh list
#   ./docker/setup-secrets.sh validate <config_file>
#   ./docker/setup-secrets.sh backup <output_file>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

log_info() {
    echo -e "${BLUE}ℹ️  $*${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $*${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $*${NC}"
}

log_error() {
    echo -e "${RED}❌ $*${NC}"
}

# ============================================================================
# CREATE SECRET
# ============================================================================

create_secret() {
    local name="$1"
    local value="$2"

    log_info "Creating Docker secret: $name"

    # Check if secret already exists
    if docker secret ls --filter "name=$name" --quiet | grep -q "$name"; then
        log_warning "Secret '$name' already exists. Use 'rotate' to update it."
        return 1
    fi

    # Create the secret
    echo "$value" | docker secret create "$name" - 2>/dev/null
    log_success "Secret '$name' created"
    return 0
}

# ============================================================================
# ROTATE SECRET
# ============================================================================

rotate_secret() {
    local name="$1"
    local value="$2"
    local services="${3:-}"

    log_info "Rotating Docker secret: $name"

    # Create new secret with timestamp suffix
    local new_name="${name}_$(date +%s)"
    echo "$value" | docker secret create "$new_name" - 2>/dev/null
    log_success "New secret created: $new_name"

    # If services specified, update them
    if [ -n "$services" ]; then
        log_info "Updating services: $services"
        for service in $services; do
            if docker service ls --filter "name=$service" --quiet | grep -q "$service"; then
                docker service update \
                    --secret-rm "$name" \
                    --secret-add "source=$new_name,target=$name" \
                    --force \
                    "$service" 2>/dev/null
                log_success "Service '$service' updated"
            else
                log_warning "Service '$service' not found"
            fi
        done

        # Wait for rollout
        log_info "Waiting for service rollout..."
        for service in $services; do
            docker service ps "$service" --format "table {{.ID}}\t{{.CurrentState}}" | tail -5
        done

        # Clean up old secret (after 5 seconds to ensure rollout complete)
        sleep 5
        log_info "Removing old secret: $name"
        docker secret rm "$name" 2>/dev/null || log_warning "Could not remove old secret"

        # Rename new secret to original name
        docker secret create "$name" /dev/null 2>/dev/null || true
        log_success "Rotation complete"
    else
        log_warning "No services specified. Run 'docker service update' manually to apply."
    fi
}

# ============================================================================
# LIST SECRETS
# ============================================================================

list_secrets() {
    log_info "Docker Secrets:"
    docker secret ls --format "table {{.ID}}\t{{.Name}}\t{{.CreatedAt}}\t{{.UpdatedAt}}"
}

# ============================================================================
# VALIDATE SECRETS
# ============================================================================

validate_secrets() {
    local config_file="$1"
    local missing=()

    if [ ! -f "$config_file" ]; then
        log_error "Config file not found: $config_file"
        return 1
    fi

    log_info "Validating secrets from: $config_file"

    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue

        # Check if secret exists
        if docker secret ls --filter "name=$key" --quiet | grep -q "$key"; then
            log_success "Secret exists: $key"
        else
            missing+=("$key")
            log_warning "Secret missing: $key"
        fi
    done < "$config_file"

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing secrets: ${missing[*]}"
        return 1
    else
        log_success "All secrets validated"
        return 0
    fi
}

# ============================================================================
# BACKUP SECRETS
# ============================================================================

backup_secrets() {
    local output_file="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="backups/secrets_${timestamp}"

    log_info "Backing up Docker secrets to: $backup_dir"

    mkdir -p "$backup_dir"

    # Get list of secrets
    local secrets=$(docker secret ls --format "{{.Name}}")

    if [ -z "$secrets" ]; then
        log_warning "No secrets found to backup"
        return 0
    fi

    # Note: We cannot directly export secret values (Docker restriction)
    # Instead, backup the list and structure
    echo "# Docker Secrets Backup - $timestamp" > "$backup_dir/manifest.txt"
    echo "# These are secret names only (values are not exported for security)" >> "$backup_dir/manifest.txt"
    echo "$secrets" >> "$backup_dir/manifest.txt"

    log_success "Backup manifest created: $backup_dir/manifest.txt"

    # Create docker-compose template
    cat > "$backup_dir/docker-compose.backup.yml" << 'EOF'
version: '3.1'

secrets:
EOF

    for secret in $secrets; do
        cat >> "$backup_dir/docker-compose.backup.yml" << EOF
  $secret:
    external: true
EOF
    done

    log_success "Docker Compose template created: $backup_dir/docker-compose.backup.yml"
    log_info "Backup complete in: $backup_dir"
}

# ============================================================================
# BATCH CREATE FROM ENV FILE
# ============================================================================

create_from_env() {
    local env_file="$1"

    if [ ! -f "$env_file" ]; then
        log_error "Environment file not found: $env_file"
        return 1
    fi

    log_info "Creating secrets from: $env_file"

    local count=0
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue

        # Skip if already exists
        if docker secret ls --filter "name=$key" --quiet | grep -q "$key"; then
            log_warning "Secret already exists: $key"
            continue
        fi

        # Create secret (value will be prompted)
        log_info "Enter value for '$key' (press Enter to skip):"
        read -rs -p "  > " secret_value
        echo ""

        if [ -n "$secret_value" ]; then
            create_secret "$key" "$secret_value"
            ((count++))
        fi
    done < "$env_file"

    log_success "Created $count secrets"
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    if [ $# -lt 1 ]; then
        cat << EOF
Docker Secrets Manager

USAGE:
    $(basename "$0") <command> [args]

COMMANDS:
    create <name> <value>      Create a new Docker secret
    rotate <name> <value> [services]
                                Rotate a secret and update services
    list                         List all Docker secrets
    validate <config>            Validate secrets from config file
    backup <output>              Backup secrets manifest
    create-from-env <env_file>   Create secrets from .env file (interactive)

EXAMPLES:
    # Create a single secret
    $(basename "$0") create bot_token "your-token-here"

    # Rotate a secret and update services
    $(basename "$0") rotate redis_password "new-password" "mltb-app mltb-worker"

    # Validate all secrets exist
    $(basename "$0") validate config/.env.production

    # Backup secret structure
    $(basename "$0") backup secrets_backup.tar.gz

EOF
        return 1
    fi

    local command="$1"
    shift

    case "$command" in
        create)
            if [ $# -lt 2 ]; then
                log_error "Usage: $0 create <name> <value>"
                return 1
            fi
            create_secret "$1" "$2"
            ;;
        rotate)
            if [ $# -lt 2 ]; then
                log_error "Usage: $0 rotate <name> <value> [services...]"
                return 1
            fi
            rotate_secret "$1" "$2" "${3:-}"
            ;;
        list)
            list_secrets
            ;;
        validate)
            if [ $# -lt 1 ]; then
                log_error "Usage: $0 validate <config_file>"
                return 1
            fi
            validate_secrets "$1"
            ;;
        backup)
            if [ $# -lt 1 ]; then
                log_error "Usage: $0 backup <output_file>"
                return 1
            fi
            backup_secrets "$1"
            ;;
        create-from-env)
            if [ $# -lt 1 ]; then
                log_error "Usage: $0 create-from-env <env_file>"
                return 1
            fi
            create_from_env "$1"
            ;;
        *)
            log_error "Unknown command: $command"
            return 1
            ;;
    esac
}

main "$@"
