from .service import MLAnomalyDetector
from .types import Anomaly, AnomalyDetectionConfig, PredictionResult

_anomaly_detector: MLAnomalyDetector | None = None


def get_anomaly_detector() -> MLAnomalyDetector:
    global _anomaly_detector
    if _anomaly_detector is None:
        _anomaly_detector = MLAnomalyDetector()
    return _anomaly_detector


__all__ = [
    "Anomaly",
    "AnomalyDetectionConfig",
    "PredictionResult",
    "MLAnomalyDetector",
    "get_anomaly_detector",
]
