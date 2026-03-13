"""
Infrastructure as Code & Configuration Management for Phase 7

Implements:
- Configuration templates
- Environment validation
- Secret management
- Infrastructure provisioning
- Configuration drift detection
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import yaml

from .. import LOGGER


class Environment(str, Enum):
    """Deployment environments"""
    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"


class ConfigSource(str, Enum):
    """Configuration sources"""
    ENV_FILE = "env_file"
    YAML = "yaml"
    JSON = "json"
    SECRETS_MANAGER = "secrets_manager"
    CONSUL = "consul"


@dataclass
class ConfigError:
    """Configuration error"""
    field: str
    message: str
    severity: str = "error"  # error, warning


class ConfigValidator:
    """Validate configuration"""

    def __init__(self):
        self.rules: Dict[str, Callable] = {}

    def add_rule(
        self,
        field: str,
        validator: Callable
    ) -> None:
        """Add validation rule"""
        self.rules[field] = validator

    def validate(self, config: Dict[str, Any]) -> List[ConfigError]:
        """Validate configuration"""
        errors = []

        for field, validator in self.rules.items():
            if field not in config:
                errors.append(ConfigError(field, f"Missing required field: {field}"))
                continue

            try:
                if not validator(config[field]):
                    errors.append(
                        ConfigError(field, f"Validation failed for {field}")
                    )

            except Exception as e:
                errors.append(
                    ConfigError(field, f"Validation error: {e}")
                )

        return errors


class SecretManager:
    """Manage secrets securely"""

    def __init__(self):
        self.secrets: Dict[str, str] = {}
        self.audit_log: list = []

    def store_secret(
        self,
        name: str,
        value: str,
        user_id: Optional[str] = None
    ) -> None:
        """Store secret"""
        # Hash for comparison without storing plaintext
        hashlib.sha256(value.encode()).hexdigest()
        self.secrets[name] = value  # In production, use encrypted storage

        self.audit_log.append({
            "action": "store",
            "secret_name": name,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def get_secret(
        self,
        name: str,
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """Retrieve secret"""
        self.audit_log.append({
            "action": "retrieve",
            "secret_name": name,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        return self.secrets.get(name)

    def rotate_secret(
        self,
        name: str,
        new_value: str,
        user_id: Optional[str] = None
    ) -> bool:
        """Rotate secret"""
        if name not in self.secrets:
            return False

        self.secrets[name] = new_value

        self.audit_log.append({
            "action": "rotate",
            "secret_name": name,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        return True

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Get audit log"""
        return self.audit_log.copy()


@dataclass
class ConfigurationTemplate:
    """Configuration template"""
    name: str
    environment: Environment
    version: str
    values: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ConfigurationManager:
    """Manage configurations"""

    def __init__(self):
        self.templates: Dict[str, ConfigurationTemplate] = {}
        self.active_config: Optional[Dict[str, Any]] = None
        self.config_history: list = []
        self.validator = ConfigValidator()

    def create_template(
        self,
        name: str,
        environment: Environment,
        values: Dict[str, Any],
        version: str = "1.0"
    ) -> ConfigurationTemplate:
        """Create configuration template"""
        template = ConfigurationTemplate(
            name=name,
            environment=environment,
            version=version,
            values=values
        )

        key = f"{name}_{environment.value}"
        self.templates[key] = template

        return template

    def load_template(
        self,
        name: str,
        environment: Environment
    ) -> Optional[Dict[str, Any]]:
        """Load template configuration"""
        key = f"{name}_{environment.value}"

        if key not in self.templates:
            LOGGER.error(f"Template not found: {key}")
            return None

        template = self.templates[key]

        # Validate
        errors = self.validator.validate(template.values)
        if errors:
            for error in errors:
                LOGGER.warning(f"{error.field}: {error.message}")

        self.active_config = template.values.copy()

        self.config_history.append({
            "template": name,
            "environment": environment.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config_hash": hashlib.sha256(
                json.dumps(template.values, sort_keys=True).encode()
            ).hexdigest()
        })

        return self.active_config

    def load_from_yaml(
        self,
        filepath: str,
        environment: Environment
    ) -> Optional[Dict[str, Any]]:
        """Load configuration from YAML file"""
        try:
            with open(filepath, 'r') as f:
                config = yaml.safe_load(f)

            # Validate
            errors = self.validator.validate(config)
            if errors:
                for error in errors:
                    LOGGER.warning(f"{error.field}: {error.message}")

            self.active_config = config

            return config

        except Exception as e:
            LOGGER.error(f"Failed to load YAML config: {e}")
            return None

    def export_template(
        self,
        name: str,
        environment: Environment,
        format: str = "json"
    ) -> Optional[str]:
        """Export template to file"""
        key = f"{name}_{environment.value}"

        if key not in self.templates:
            return None

        template = self.templates[key]

        if format == "json":
            return json.dumps(template.values, indent=2)
        elif format == "yaml":
            return yaml.dump(template.values, default_flow_style=False)

        return None


class DriftDetector:
    """Detect infrastructure drift"""

    def __init__(self):
        self.baseline: Optional[Dict[str, Any]] = None
        self.current_state: Optional[Dict[str, Any]] = None
        self.drift_history: list = []

    def capture_baseline(self, state: Dict[str, Any]) -> None:
        """Capture baseline state"""
        self.baseline = state.copy()
        self.baseline_hash = hashlib.sha256(
            json.dumps(state, sort_keys=True).encode()
        ).hexdigest()

    def scan_current_state(self, state: Dict[str, Any]) -> None:
        """Scan current state"""
        self.current_state = state.copy()

    def _create_drift_report(self) -> Dict[str, Any]:
        return {
            "drift_detected": False,
            "changes": [],
            "added_items": [],
            "removed_items": [],
            "modified_items": []
        }

    def _collect_removed_items(self, drift: Dict[str, Any]) -> None:
        for key in self.baseline:
            if key not in self.current_state:
                drift["removed_items"].append(key)

    def _collect_added_items(self, drift: Dict[str, Any]) -> None:
        for key in self.current_state:
            if key not in self.baseline:
                drift["added_items"].append(key)

    def _collect_modified_items(self, drift: Dict[str, Any]) -> None:
        for key in self.baseline:
            if key in self.current_state and self.baseline[key] != self.current_state[key]:
                drift["modified_items"].append({
                    "key": key,
                    "old": str(self.baseline[key]),
                    "new": str(self.current_state[key])
                })

    def _finalize_drift_report(self, drift: Dict[str, Any]) -> None:
        drift["drift_detected"] = bool(
            drift["added_items"] or drift["removed_items"] or drift["modified_items"]
        )

    def _record_drift_history(self, drift: Dict[str, Any]) -> None:
        if not drift["drift_detected"]:
            return
        self.drift_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "drift": drift
        })

    def detect_drift(self) -> Dict[str, Any]:
        """Detect drift from baseline"""
        if not self.baseline or not self.current_state:
            return {"drift_detected": False}

        drift = self._create_drift_report()
        self._collect_removed_items(drift)
        self._collect_added_items(drift)
        self._collect_modified_items(drift)
        self._finalize_drift_report(drift)
        self._record_drift_history(drift)

        return drift


@dataclass
class InfrastructureSpec:
    """Infrastructure specification"""
    name: str
    environment: Environment
    resources: Dict[str, Any] = field(default_factory=dict)
    dependencies: list = field(default_factory=list)
    desired_state: Dict[str, Any] = field(default_factory=dict)


class InfrastructureProvisioner:
    """Provision infrastructure"""

    def __init__(self):
        self.specs: Dict[str, InfrastructureSpec] = {}
        self.provisioning_log: list = []

    def register_spec(
        self,
        name: str,
        environment: Environment,
        resources: Dict[str, Any]
    ) -> InfrastructureSpec:
        """Register infrastructure spec"""
        spec = InfrastructureSpec(
            name=name,
            environment=environment,
            resources=resources
        )

        self.specs[f"{name}_{environment.value}"] = spec
        return spec

    async def provision(
        self,
        name: str,
        environment: Environment
    ) -> bool:
        """Provision infrastructure"""
        spec_key = f"{name}_{environment.value}"

        if spec_key not in self.specs:
            LOGGER.error(f"Spec not found: {spec_key}")
            return False

        spec = self.specs[spec_key]

        try:
            LOGGER.info(f"Provisioning {name} in {environment.value}")

            # Simulate provisioning
            for resource_name, resource_config in spec.resources.items():
                LOGGER.info(f"Creating resource: {resource_name}")

            self.provisioning_log.append({
                "spec": name,
                "environment": environment.value,
                "status": "success",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            return True

        except Exception as e:
            LOGGER.error(f"Provisioning failed: {e}")
            self.provisioning_log.append({
                "spec": name,
                "environment": environment.value,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            return False


# Global instances
config_validator = ConfigValidator()
secret_manager = SecretManager()
config_manager = ConfigurationManager()
drift_detector = DriftDetector()
infrastructure_provisioner = InfrastructureProvisioner()
