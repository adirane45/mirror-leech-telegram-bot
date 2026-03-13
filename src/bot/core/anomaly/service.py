import logging
from collections import deque
from datetime import UTC, datetime
from typing import Any

from .detection import detect_iqr, detect_trend_anomaly, detect_zscore
from .patterns import detect_time_pattern, detect_value_pattern
from .prediction import predict_metric, recommend_scaling
from .types import Anomaly, AnomalyDetectionConfig, PredictionResult

logger = logging.getLogger(__name__)


class MLAnomalyDetector:
    def __init__(self) -> None:
        self.configs: dict[str, AnomalyDetectionConfig] = {}
        self.data: dict[str, deque[float]] = {}
        self.anomalies: list[Anomaly] = []
        self.last_alert: dict[str, datetime] = {}
        self.stats_cache: dict[str, dict[str, Any]] = {}
        logger.info("MLAnomalyDetector initialized")

    def add_metric(
        self,
        metric_name: str,
        sensitivity: float = 2.0,
        window_size: int = 100,
        min_samples: int = 10,
    ) -> None:
        config = AnomalyDetectionConfig(
            metric_name=metric_name,
            sensitivity=sensitivity,
            window_size=window_size,
            min_samples=min_samples,
        )
        self.configs[metric_name] = config
        self.data[metric_name] = deque(maxlen=window_size)
        logger.info(f"Metric added for detection: {metric_name} (sensitivity={sensitivity})")

    def remove_metric(self, metric_name: str) -> bool:
        if metric_name not in self.configs:
            return False

        del self.configs[metric_name]
        self.data.pop(metric_name, None)
        logger.info(f"Metric removed: {metric_name}")
        return True

    def detect(
        self,
        metric_name: str,
        value: float,
        metadata: dict[str, Any] | None = None,
    ) -> list[Anomaly]:
        try:
            if metric_name not in self.configs:
                return []

            config = self.configs[metric_name]
            self.data[metric_name].append(value)

            if len(self.data[metric_name]) < config.min_samples:
                return []

            if not self._check_cooldown(metric_name, config):
                return []

            anomalies: list[Anomaly] = []
            for anomaly in (
                detect_zscore(metric_name, value, config, self.data[metric_name]),
                detect_iqr(metric_name, value, self.data[metric_name]),
                detect_trend_anomaly(metric_name, value, self.data[metric_name]),
            ):
                if anomaly:
                    if metadata:
                        anomaly.metadata.update(metadata)
                    anomalies.append(anomaly)

            if anomalies:
                self.anomalies.extend(anomalies)
                self.last_alert[metric_name] = datetime.now(UTC)
                logger.warning(
                    f"Anomaly detected in {metric_name}: value={value}, count={len(anomalies)}"
                )

            return anomalies
        except Exception as error:
            logger.error(f"Anomaly detection error: {error}")
            return []

    def _check_cooldown(self, metric_name: str, config: AnomalyDetectionConfig) -> bool:
        if metric_name not in self.last_alert:
            return True
        elapsed = (datetime.now(UTC) - self.last_alert[metric_name]).total_seconds()
        return elapsed >= config.cooldown_seconds

    def predict(self, metric_name: str, horizon_minutes: int = 30) -> PredictionResult | None:
        if metric_name not in self.data:
            return None
        return predict_metric(metric_name, self.data[metric_name], horizon_minutes)

    def recommend_scaling(
        self,
        metric_name: str,
        threshold: float,
        horizon_minutes: int = 30,
    ) -> dict[str, Any] | None:
        prediction = self.predict(metric_name, horizon_minutes)
        if not prediction:
            return None
        return recommend_scaling(metric_name, prediction, threshold, horizon_minutes)

    def detect_recurring_patterns(self, metric_name: str) -> list[dict[str, Any]]:
        metric_anomalies = [item for item in self.anomalies if item.metric_name == metric_name]
        if len(metric_anomalies) < 3:
            return []

        patterns: list[dict[str, Any]] = []
        for pattern in (
            detect_time_pattern(metric_anomalies),
            detect_value_pattern(metric_anomalies),
        ):
            if pattern:
                patterns.append(pattern)
        return patterns

    def get_anomaly_stats(self) -> dict[str, Any]:
        total = len(self.anomalies)
        by_metric: dict[str, int] = {}
        by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0}

        for anomaly in self.anomalies:
            by_metric[anomaly.metric_name] = by_metric.get(anomaly.metric_name, 0) + 1
            by_severity[anomaly.severity] += 1

        return {
            "total_anomalies": total,
            "by_metric": by_metric,
            "by_severity": by_severity,
            "configured_metrics": len(self.configs),
        }

    def get_recent_anomalies(self, limit: int = 50) -> list[dict[str, Any]]:
        recent = self.anomalies[-limit:]
        recent.reverse()
        return [
            {
                "anomaly_id": anomaly.anomaly_id,
                "metric": anomaly.metric_name,
                "value": anomaly.value,
                "expected_range": anomaly.expected_range,
                "severity": anomaly.severity,
                "deviation": anomaly.deviation,
                "timestamp": anomaly.timestamp.isoformat(),
                "metadata": anomaly.metadata,
            }
            for anomaly in recent
        ]
