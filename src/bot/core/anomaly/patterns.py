import logging
import statistics
from typing import Any

from .types import Anomaly

logger = logging.getLogger(__name__)


def detect_time_pattern(anomalies: list[Anomaly]) -> dict[str, Any] | None:
    try:
        if len(anomalies) < 3:
            return None

        hours = [anomaly.timestamp.hour for anomaly in anomalies]
        hour_counts: dict[int, int] = {}
        for hour in hours:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        most_common_hour = max(hour_counts, key=lambda hour: hour_counts[hour])
        frequency = hour_counts[most_common_hour]
        if frequency < 3:
            return None

        return {
            "type": "time_based",
            "pattern": f"Recurring around {most_common_hour}:00",
            "frequency": frequency,
            "confidence": min(1.0, frequency / len(anomalies)),
        }
    except Exception as error:
        logger.error(f"Time pattern detection error: {error}")
        return None


def detect_value_pattern(anomalies: list[Anomaly]) -> dict[str, Any] | None:
    try:
        values = [anomaly.value for anomaly in anomalies]
        if len(values) < 3:
            return None

        mean_value = statistics.mean(values)
        stdev_value = statistics.stdev(values) if len(values) > 1 else 0
        if stdev_value >= mean_value * 0.1:
            return None

        return {
            "type": "value_based",
            "pattern": f"Anomalies cluster around {mean_value:.2f}",
            "mean": mean_value,
            "stdev": stdev_value,
            "confidence": 0.7,
        }
    except Exception as error:
        logger.error(f"Value pattern detection error: {error}")
        return None
