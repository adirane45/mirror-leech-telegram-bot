import logging
import statistics
from collections import deque
from typing import Any

from .types import PredictionResult

logger = logging.getLogger(__name__)


def predict_metric(
    metric_name: str,
    data: deque[float],
    horizon_minutes: int = 30,
) -> PredictionResult | None:
    try:
        data_list = list(data)
        if len(data_list) < 10:
            return None

        size = len(data_list)
        x = list(range(size))
        y = data_list

        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(size))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(size))
        if denominator == 0:
            return None

        slope = numerator / denominator
        intercept = y_mean - (slope * x_mean)

        predicted_value = (slope * (size + horizon_minutes)) + intercept

        y_pred = [(slope * x[i]) + intercept for i in range(size)]
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(size))
        ss_tot = sum((y[i] - y_mean) ** 2 for i in range(size))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        confidence = max(0.0, min(1.0, r_squared))

        return PredictionResult(
            metric_name=metric_name,
            current_value=data_list[-1],
            predicted_value=predicted_value,
            confidence=confidence,
            horizon_minutes=horizon_minutes,
        )
    except Exception as error:
        logger.error(f"Prediction error: {error}")
        return None


def recommend_scaling(
    metric_name: str,
    prediction: PredictionResult,
    threshold: float,
    horizon_minutes: int,
) -> dict[str, Any]:
    current_usage_pct = (prediction.current_value / threshold) * 100
    predicted_usage_pct = (prediction.predicted_value / threshold) * 100

    recommendation: dict[str, Any] = {
        "metric": metric_name,
        "current_usage_pct": current_usage_pct,
        "predicted_usage_pct": predicted_usage_pct,
        "horizon_minutes": horizon_minutes,
        "confidence": prediction.confidence,
        "action": "none",
    }

    if predicted_usage_pct > 80:
        recommendation["action"] = "scale_up"
        recommendation["urgency"] = "high" if predicted_usage_pct > 90 else "medium"
        recommendation["reason"] = (
            f"Predicted to reach {predicted_usage_pct:.1f}% in {horizon_minutes}min"
        )
    elif predicted_usage_pct < 30 and current_usage_pct < 40:
        recommendation["action"] = "scale_down"
        recommendation["urgency"] = "low"
        recommendation["reason"] = f"Low utilization: {predicted_usage_pct:.1f}%"

    return recommendation
