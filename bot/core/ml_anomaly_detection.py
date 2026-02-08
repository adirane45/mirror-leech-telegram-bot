"""
Phase 5: ML-Based Anomaly Detection
Machine learning for anomaly detection, predictive scaling, and pattern recognition
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta, UTC
from dataclasses import dataclass, field
from collections import deque
import statistics
import logging
import math

logger = logging.getLogger(__name__)


@dataclass
class AnomalyDetectionConfig:
    """Anomaly detection configuration"""
    metric_name: str
    sensitivity: float = 2.0  # Standard deviations for anomaly threshold
    window_size: int = 100  # Number of points for baseline
    min_samples: int = 10  # Minimum samples before detection
    cooldown_seconds: int = 300  # Cooldown between alerts


@dataclass
class Anomaly:
    """Detected anomaly"""
    anomaly_id: str
    metric_name: str
    value: float
    expected_range: Tuple[float, float]
    severity: str  # "low", "medium", "high", "critical"
    deviation: float  # Standard deviations from mean
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PredictionResult:
    """Prediction result"""
    metric_name: str
    current_value: float
    predicted_value: float
    confidence: float  # 0.0 - 1.0
    horizon_minutes: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class MLAnomalyDetector:
    """
    ML-Based Anomaly Detection System
    
    Features:
    - Statistical anomaly detection (Z-score, IQR)
    - Trend-based anomaly detection
    - Predictive resource scaling
    - Pattern recognition for recurring issues
    - Auto-learning baseline from historical data
    - Configurable sensitivity and thresholds
    
    Algorithms:
    - Z-Score: Detects statistical outliers
    - Moving Average: Detects trend anomalies
    - Simple Linear Regression: Predictive analysis
    
    Usage:
        detector = MLAnomalyDetector()
        
        # Configure detection
        detector.add_metric("response_time", sensitivity=2.5)
        
        # Track data points
        for value in data_stream:
            anomalies = detector.detect(metric_name="response_time", value=value)
            if anomalies:
                print(f"Anomaly detected: {anomalies}")
        
        # Predict future values
        prediction = detector.predict("cpu_usage", horizon_minutes=30)
    """
    
    def __init__(self):
        # Metric configurations
        self.configs: Dict[str, AnomalyDetectionConfig] = {}
        
        # Historical data (ring buffers)
        self.data: Dict[str, deque] = {}  # metric_name -> deque of values
        
        # Detected anomalies
        self.anomalies: List[Anomaly] = []
        
        # Last alert time (for cooldown)
        self.last_alert: Dict[str, datetime] = {}
        
        # Statistics cache
        self.stats_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info("MLAnomalyDetector initialized")
    
    # ========================================================================
    # CONFIGURATION
    # ========================================================================
    
    def add_metric(
        self,
        metric_name: str,
        sensitivity: float = 2.0,
        window_size: int = 100,
        min_samples: int = 10
    ) -> None:
        """
        Add metric for anomaly detection
        
        Args:
            metric_name: Metric identifier
            sensitivity: Detection sensitivity (std devs)
            window_size: Historical window size
            min_samples: Minimum samples before detection
        """
        try:
            config = AnomalyDetectionConfig(
                metric_name=metric_name,
                sensitivity=sensitivity,
                window_size=window_size,
                min_samples=min_samples
            )
            
            self.configs[metric_name] = config
            self.data[metric_name] = deque(maxlen=window_size)
            
            logger.info(f"Metric added for detection: {metric_name} (sensitivity={sensitivity})")
            
        except Exception as e:
            logger.error(f"Failed to add metric: {e}")
            raise
    
    def remove_metric(self, metric_name: str) -> bool:
        """Remove metric from detection"""
        try:
            if metric_name in self.configs:
                del self.configs[metric_name]
                if metric_name in self.data:
                    del self.data[metric_name]
                logger.info(f"Metric removed: {metric_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove metric: {e}")
            return False
    
    # ========================================================================
    # ANOMALY DETECTION
    # ========================================================================
    
    def detect(
        self,
        metric_name: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Anomaly]:
        """
        Detect anomalies in metric value
        
        Returns:
            List of detected anomalies
        """
        try:
            # Check if metric is configured
            if metric_name not in self.configs:
                return []
            
            config = self.configs[metric_name]
            
            # Add value to history
            self.data[metric_name].append(value)
            
            # Need minimum samples
            if len(self.data[metric_name]) < config.min_samples:
                return []
            
            # Check cooldown
            if not self._check_cooldown(metric_name, config):
                return []
            
            # Run detection algorithms
            anomalies = []
            
            # 1. Z-Score Detection
            z_score_anomaly = self._detect_zscore(metric_name, value, config)
            if z_score_anomaly:
                anomalies.append(z_score_anomaly)
            
            # 2. IQR Detection (Interquartile Range)
            iqr_anomaly = self._detect_iqr(metric_name, value, config)
            if iqr_anomaly:
                anomalies.append(iqr_anomaly)
            
            # 3. Trend Anomaly Detection
            trend_anomaly = self._detect_trend_anomaly(metric_name, value, config)
            if trend_anomaly:
                anomalies.append(trend_anomaly)
            
            # Store anomalies
            if anomalies:
                self.anomalies.extend(anomalies)
                self.last_alert[metric_name] = datetime.now(UTC)
                logger.warning(
                    f"Anomaly detected in {metric_name}: value={value}, "
                    f"count={len(anomalies)}"
                )
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")
            return []
    
    def _detect_zscore(
        self,
        metric_name: str,
        value: float,
        config: AnomalyDetectionConfig
    ) -> Optional[Anomaly]:
        """Detect anomaly using Z-score method"""
        try:
            data = list(self.data[metric_name])
            mean = statistics.mean(data)
            stdev = statistics.stdev(data) if len(data) > 1 else 0
            
            if stdev == 0:
                return None
            
            # Calculate Z-score
            z_score = abs((value - mean) / stdev)
            
            # Check threshold
            if z_score > config.sensitivity:
                import secrets
                
                # Determine severity
                severity = self._calculate_severity(z_score, config.sensitivity)
                
                return Anomaly(
                    anomaly_id=secrets.token_urlsafe(8),
                    metric_name=metric_name,
                    value=value,
                    expected_range=(
                        mean - (config.sensitivity * stdev),
                        mean + (config.sensitivity * stdev)
                    ),
                    severity=severity,
                    deviation=z_score,
                    metadata={'method': 'z-score', 'mean': mean, 'stdev': stdev}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Z-score detection error: {e}")
            return None
    
    def _detect_iqr(
        self,
        metric_name: str,
        value: float,
        config: AnomalyDetectionConfig
    ) -> Optional[Anomaly]:
        """Detect anomaly using IQR (Interquartile Range) method"""
        try:
            data = sorted(list(self.data[metric_name]))
            
            if len(data) < 4:
                return None
            
            # Calculate quartiles
            q1_idx = len(data) // 4
            q3_idx = 3 * len(data) // 4
            q1 = data[q1_idx]
            q3 = data[q3_idx]
            iqr = q3 - q1
            
            # Calculate bounds
            lower_bound = q1 - (1.5 * iqr)
            upper_bound = q3 + (1.5 * iqr)
            
            # Check if outlier
            if value < lower_bound or value > upper_bound:
                import secrets
                
                median = statistics.median(data)
                deviation = abs(value - median) / (iqr if iqr > 0 else 1)
                severity = self._calculate_severity(deviation, 1.5)
                
                return Anomaly(
                    anomaly_id=secrets.token_urlsafe(8),
                    metric_name=metric_name,
                    value=value,
                    expected_range=(lower_bound, upper_bound),
                    severity=severity,
                    deviation=deviation,
                    metadata={'method': 'iqr', 'q1': q1, 'q3': q3, 'iqr': iqr}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"IQR detection error: {e}")
            return None
    
    def _detect_trend_anomaly(
        self,
        metric_name: str,
        value: float,
        config: AnomalyDetectionConfig
    ) -> Optional[Anomaly]:
        """Detect anomaly based on trend deviation"""
        try:
            data = list(self.data[metric_name])
            
            if len(data) < 10:
                return None
            
            # Calculate moving average
            window = min(10, len(data) // 2)
            moving_avg = statistics.mean(data[-window:])
            
            # Calculate deviation from trend
            deviation_pct = abs((value - moving_avg) / moving_avg * 100) if moving_avg != 0 else 0
            
            # Threshold: 20% deviation from moving average
            if deviation_pct > 20:
                import secrets
                
                severity = "medium" if deviation_pct < 50 else "high"
                
                return Anomaly(
                    anomaly_id=secrets.token_urlsafe(8),
                    metric_name=metric_name,
                    value=value,
                    expected_range=(moving_avg * 0.8, moving_avg * 1.2),
                    severity=severity,
                    deviation=deviation_pct / 10,  # Normalize
                    metadata={'method': 'trend', 'moving_avg': moving_avg, 'deviation_pct': deviation_pct}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Trend detection error: {e}")
            return None
    
    def _calculate_severity(self, deviation: float, threshold: float) -> str:
        """Calculate anomaly severity"""
        ratio = deviation / threshold
        
        if ratio < 1.5:
            return "low"
        elif ratio < 2.5:
            return "medium"
        elif ratio < 4.0:
            return "high"
        else:
            return "critical"
    
    def _check_cooldown(self, metric_name: str, config: AnomalyDetectionConfig) -> bool:
        """Check if cooldown period has passed"""
        if metric_name not in self.last_alert:
            return True
        
        last_alert = self.last_alert[metric_name]
        elapsed = (datetime.now(UTC) - last_alert).total_seconds()
        
        return elapsed >= config.cooldown_seconds
    
    # ========================================================================
    # PREDICTIVE ANALYSIS
    # ========================================================================
    
    def predict(
        self,
        metric_name: str,
        horizon_minutes: int = 30
    ) -> Optional[PredictionResult]:
        """
        Predict future metric value using simple linear regression
        
        Args:
            metric_name: Metric to predict
            horizon_minutes: Prediction horizon in minutes
        
        Returns:
            PredictionResult or None
        """
        try:
            if metric_name not in self.data or len(self.data[metric_name]) < 10:
                return None
            
            data = list(self.data[metric_name])
            n = len(data)
            
            # Simple linear regression: y = mx + b
            x = list(range(n))
            y = data
            
            # Calculate slope (m) and intercept (b)
            x_mean = statistics.mean(x)
            y_mean = statistics.mean(y)
            
            numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
            
            if denominator == 0:
                return None
            
            slope = numerator / denominator
            intercept = y_mean - (slope * x_mean)
            
            # Predict future value
            future_x = n + horizon_minutes
            predicted_value = (slope * future_x) + intercept
            
            # Calculate confidence (R-squared)
            y_pred = [(slope * x[i]) + intercept for i in range(n)]
            ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
            ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            confidence = max(0, min(1, r_squared))  # Clamp to [0, 1]
            
            return PredictionResult(
                metric_name=metric_name,
                current_value=data[-1],
                predicted_value=predicted_value,
                confidence=confidence,
                horizon_minutes=horizon_minutes
            )
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return None
    
    def recommend_scaling(
        self,
        metric_name: str,
        threshold: float,
        horizon_minutes: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Recommend scaling action based on prediction
        
        Returns:
            Scaling recommendation or None
        """
        try:
            prediction = self.predict(metric_name, horizon_minutes)
            
            if not prediction:
                return None
            
            # Calculate if scaling is needed
            current_usage_pct = (prediction.current_value / threshold) * 100
            predicted_usage_pct = (prediction.predicted_value / threshold) * 100
            
            recommendation = {
                'metric': metric_name,
                'current_usage_pct': current_usage_pct,
                'predicted_usage_pct': predicted_usage_pct,
                'horizon_minutes': horizon_minutes,
                'confidence': prediction.confidence,
                'action': 'none'
            }
            
            # Determine action
            if predicted_usage_pct > 80:
                recommendation['action'] = 'scale_up'
                recommendation['urgency'] = 'high' if predicted_usage_pct > 90 else 'medium'
                recommendation['reason'] = f'Predicted to reach {predicted_usage_pct:.1f}% in {horizon_minutes}min'
            elif predicted_usage_pct < 30 and current_usage_pct < 40:
                recommendation['action'] = 'scale_down'
                recommendation['urgency'] = 'low'
                recommendation['reason'] = f'Low utilization: {predicted_usage_pct:.1f}%'
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Scaling recommendation error: {e}")
            return None
    
    # ========================================================================
    # PATTERN RECOGNITION
    # ========================================================================
    
    def detect_recurring_patterns(self, metric_name: str) -> List[Dict[str, Any]]:
        """
        Detect recurring failure patterns
        
        Returns:
            List of detected patterns
        """
        try:
            # Get anomalies for this metric
            metric_anomalies = [a for a in self.anomalies if a.metric_name == metric_name]
            
            if len(metric_anomalies) < 3:
                return []
            
            patterns = []
            
            # Detect time-based patterns (e.g., daily spikes)
            time_pattern = self._detect_time_pattern(metric_anomalies)
            if time_pattern:
                patterns.append(time_pattern)
            
            # Detect value-based patterns (e.g., always fails at same value)
            value_pattern = self._detect_value_pattern(metric_anomalies)
            if value_pattern:
                patterns.append(value_pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Pattern detection error: {e}")
            return []
    
    def _detect_time_pattern(self, anomalies: List[Anomaly]) -> Optional[Dict[str, Any]]:
        """Detect time-based recurring patterns"""
        try:
            if len(anomalies) < 3:
                return None
            
            # Extract hours from timestamps
            hours = [a.timestamp.hour for a in anomalies]
            
            # Find most common hour
            hour_counts = {}
            for hour in hours:
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            most_common_hour = max(hour_counts, key=hour_counts.get)
            frequency = hour_counts[most_common_hour]
            
            # Pattern if appears 3+ times
            if frequency >= 3:
                return {
                    'type': 'time_based',
                    'pattern': f'Recurring around {most_common_hour}:00',
                    'frequency': frequency,
                    'confidence': min(1.0, frequency / len(anomalies))
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Time pattern detection error: {e}")
            return None
    
    def _detect_value_pattern(self, anomalies: List[Anomaly]) -> Optional[Dict[str, Any]]:
        """Detect value-based patterns"""
        try:
            values = [a.value for a in anomalies]
            
            if len(values) < 3:
                return None
            
            # Check if values cluster around similar range
            mean_value = statistics.mean(values)
            stdev_value = statistics.stdev(values) if len(values) > 1 else 0
            
            # If low variance, values are clustered
            if stdev_value < mean_value * 0.1:  # 10% variation
                return {
                    'type': 'value_based',
                    'pattern': f'Anomalies cluster around {mean_value:.2f}',
                    'mean': mean_value,
                    'stdev': stdev_value,
                    'confidence': 0.7
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Value pattern detection error: {e}")
            return None
    
    # ========================================================================
    # STATISTICS & REPORTING
    # ========================================================================
    
    def get_anomaly_stats(self) -> Dict[str, Any]:
        """Get anomaly statistics"""
        try:
            total = len(self.anomalies)
            
            by_metric = {}
            by_severity = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
            
            for anomaly in self.anomalies:
                by_metric[anomaly.metric_name] = by_metric.get(anomaly.metric_name, 0) + 1
                by_severity[anomaly.severity] += 1
            
            return {
                'total_anomalies': total,
                'by_metric': by_metric,
                'by_severity': by_severity,
                'configured_metrics': len(self.configs)
            }
            
        except Exception as e:
            logger.error(f"Anomaly stats error: {e}")
            return {}
    
    def get_recent_anomalies(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent anomalies"""
        recent = self.anomalies[-limit:]
        recent.reverse()
        
        return [
            {
                'anomaly_id': a.anomaly_id,
                'metric': a.metric_name,
                'value': a.value,
                'expected_range': a.expected_range,
                'severity': a.severity,
                'deviation': a.deviation,
                'timestamp': a.timestamp.isoformat(),
                'metadata': a.metadata
            }
            for a in recent
        ]


# ============================================================================
# SINGLETON
# ============================================================================

_anomaly_detector: Optional[MLAnomalyDetector] = None


def get_anomaly_detector() -> MLAnomalyDetector:
    """Get anomaly detector singleton"""
    global _anomaly_detector
    if _anomaly_detector is None:
        _anomaly_detector = MLAnomalyDetector()
    return _anomaly_detector
