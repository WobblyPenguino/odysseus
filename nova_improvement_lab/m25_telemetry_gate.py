import math
from typing import Dict, Any, Optional

class TelemetryConsensusGate:
    """Enforces fail-closed telemetry validation, rejecting missing, non-numeric, or non-finite metrics."""
    def __init__(self, max_error_rate: float = 0.05, max_latency_ms: float = 1000.0):
        self.max_error_rate = max_error_rate
        self.max_latency_ms = max_latency_ms

    def evaluate_telemetry(self, telemetry: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validates cluster health telemetry. Fails closed on missing fields,
        non-numeric types, non-finite values (NaN/inf), or threshold violations.
        """
        if telemetry is None or not isinstance(telemetry, dict):
            return {
                "allowed": False,
                "reason": "Fail-closed: Telemetry payload is missing or invalid type."
            }

        error_rate = telemetry.get("error_rate")
        latency_ms = telemetry.get("latency_ms")

        # Validate error_rate
        if error_rate is None:
            return {"allowed": False, "reason": "Fail-closed: Missing 'error_rate' metric."}
        if not isinstance(error_rate, (int, float)) or isinstance(error_rate, bool):
            return {"allowed": False, "reason": "Fail-closed: 'error_rate' is non-numeric."}
        if math.isnan(error_rate) or math.isinf(error_rate):
            return {"allowed": False, "reason": "Fail-closed: 'error_rate' is non-finite (NaN/inf)."}

        # Validate latency_ms
        if latency_ms is None:
            return {"allowed": False, "reason": "Fail-closed: Missing 'latency_ms' metric."}
        if not isinstance(latency_ms, (int, float)) or isinstance(latency_ms, bool):
            return {"allowed": False, "reason": "Fail-closed: 'latency_ms' is non-numeric."}
        if math.isnan(latency_ms) or math.isinf(latency_ms):
            return {"allowed": False, "reason": "Fail-closed: 'latency_ms' is non-finite (NaN/inf)."}

        # Check safety thresholds
        if error_rate > self.max_error_rate:
            return {
                "allowed": False,
                "reason": f"Error rate {error_rate} exceeds maximum threshold {self.max_error_rate}."
            }

        if latency_ms > self.max_latency_ms:
            return {
                "allowed": False,
                "reason": f"Latency {latency_ms}ms exceeds maximum threshold {self.max_latency_ms}ms."
            }

        return {
            "allowed": True,
            "reason": "Telemetry validation passed within safe thresholds."
        }
