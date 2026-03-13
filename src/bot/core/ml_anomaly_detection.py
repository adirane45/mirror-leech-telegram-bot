"""Backward-compatible imports for anomaly detection APIs."""

from .anomaly import (
    Anomaly,
    AnomalyDetectionConfig,
    MLAnomalyDetector,
    PredictionResult,
    get_anomaly_detector,
)

__all__ = [
    "Anomaly",
    "AnomalyDetectionConfig",
    "PredictionResult",
    "MLAnomalyDetector",
    "get_anomaly_detector",
]
