from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class AnomalyDetectionConfig:
    metric_name: str
    sensitivity: float = 2.0
    window_size: int = 100
    min_samples: int = 10
    cooldown_seconds: int = 300


@dataclass
class Anomaly:
    anomaly_id: str
    metric_name: str
    value: float
    expected_range: tuple[float, float]
    severity: str
    deviation: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PredictionResult:
    metric_name: str
    current_value: float
    predicted_value: float
    confidence: float
    horizon_minutes: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
