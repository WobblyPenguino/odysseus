from typing import Dict, Any

class TelemetryConsensusGate:
    """Monitors live telemetry and gates consensus execution based on health thresholds."""
    def __init__(self, error_threshold: float = 0.05, max_latency_ms: float = 2000.0):
        self.error_threshold = error_threshold
        self.max_latency_ms = max_latency_ms

    def evaluate_telemetry(self, metrics: Dict[str, Any]) -> bool:
        error_rate = metrics.get("error_rate", 0.0)
        node_latency_ms = metrics.get("node_latency_ms", 0.0)
        
        if error_rate > self.error_threshold:
            return False
        if node_latency_ms > self.max_latency_ms:
            return False
        return True
