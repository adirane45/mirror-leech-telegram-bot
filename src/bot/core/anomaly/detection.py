import logging
import secrets
import statistics
from collections import deque

from .types import Anomaly, AnomalyDetectionConfig

logger = logging.getLogger(__name__)


def calculate_severity(deviation: float, threshold: float) -> str:
    ratio = deviation / threshold
    if ratio < 1.5:
        return "low"
    if ratio < 2.5:
        return "medium"
    if ratio < 4.0:
        return "high"
    return "critical"


def detect_zscore(
    metric_name: str,
    value: float,
    config: AnomalyDetectionConfig,
    data: deque[float],
) -> Anomaly | None:
    try:
        data_list = list(data)
        mean = statistics.mean(data_list)
        stdev = statistics.stdev(data_list) if len(data_list) > 1 else 0
        if stdev == 0:
            return None

        z_score = abs((value - mean) / stdev)
        if z_score <= config.sensitivity:
            return None

        severity = calculate_severity(z_score, config.sensitivity)
        return Anomaly(
            anomaly_id=secrets.token_urlsafe(8),
            metric_name=metric_name,
            value=value,
            expected_range=(
                mean - (config.sensitivity * stdev),
                mean + (config.sensitivity * stdev),
            ),
            severity=severity,
            deviation=z_score,
            metadata={"method": "z-score", "mean": mean, "stdev": stdev},
        )
    except Exception as error:
        logger.error(f"Z-score detection error: {error}")
        return None


def detect_iqr(
    metric_name: str,
    value: float,
    data: deque[float],
) -> Anomaly | None:
    try:
        sorted_data = sorted(list(data))
        if len(sorted_data) < 4:
            return None

        q1_index = len(sorted_data) // 4
        q3_index = 3 * len(sorted_data) // 4
        q1 = sorted_data[q1_index]
        q3 = sorted_data[q3_index]
        iqr = q3 - q1

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)
        if lower_bound <= value <= upper_bound:
            return None

        median = statistics.median(sorted_data)
        deviation = abs(value - median) / (iqr if iqr > 0 else 1)
        severity = calculate_severity(deviation, 1.5)
        return Anomaly(
            anomaly_id=secrets.token_urlsafe(8),
            metric_name=metric_name,
            value=value,
            expected_range=(lower_bound, upper_bound),
            severity=severity,
            deviation=deviation,
            metadata={"method": "iqr", "q1": q1, "q3": q3, "iqr": iqr},
        )
    except Exception as error:
        logger.error(f"IQR detection error: {error}")
        return None


def detect_trend_anomaly(
    metric_name: str,
    value: float,
    data: deque[float],
) -> Anomaly | None:
    try:
        data_list = list(data)
        if len(data_list) < 10:
            return None

        window = min(10, len(data_list) // 2)
        moving_average = statistics.mean(data_list[-window:])
        deviation_pct = (
            abs((value - moving_average) / moving_average * 100)
            if moving_average != 0
            else 0
        )
        if deviation_pct <= 20:
            return None

        severity = "medium" if deviation_pct < 50 else "high"
        return Anomaly(
            anomaly_id=secrets.token_urlsafe(8),
            metric_name=metric_name,
            value=value,
            expected_range=(moving_average * 0.8, moving_average * 1.2),
            severity=severity,
            deviation=deviation_pct / 10,
            metadata={
                "method": "trend",
                "moving_avg": moving_average,
                "deviation_pct": deviation_pct,
            },
        )
    except Exception as error:
        logger.error(f"Trend detection error: {error}")
        return None
