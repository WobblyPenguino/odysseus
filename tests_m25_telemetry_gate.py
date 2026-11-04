import unittest
import math
from nova_improvement_lab.m25_telemetry_gate import TelemetryConsensusGate

class TestTelemetryConsensusGate(unittest.TestCase):
    def setUp(self):
        self.gate = TelemetryConsensusGate(max_error_rate=0.05, max_latency_ms=500.0)

    def test_valid_telemetry(self):
        telemetry = {"error_rate": 0.02, "latency_ms": 150.0}
        result = self.gate.evaluate_telemetry(telemetry)
        self.assertTrue(result["allowed"])

    def test_missing_telemetry_fails_closed(self):
        result = self.gate.evaluate_telemetry(None)
        self.assertFalse(result["allowed"])

        result_missing_field = self.gate.evaluate_telemetry({"error_rate": 0.01})
        self.assertFalse(result_missing_field["allowed"])

    def test_non_finite_metrics_fail_closed(self):
        # NaN error rate
        result_nan = self.gate.evaluate_telemetry({"error_rate": float('nan'), "latency_ms": 100.0})
        self.assertFalse(result_nan["allowed"])

        # Inf latency
        result_inf = self.gate.evaluate_telemetry({"error_rate": 0.01, "latency_ms": float('inf')})
        self.assertFalse(result_inf["allowed"])

    def test_threshold_exceeded_fails(self):
        result_high_err = self.gate.evaluate_telemetry({"error_rate": 0.10, "latency_ms": 100.0})
        self.assertFalse(result_high_err["allowed"])

        result_high_lat = self.gate.evaluate_telemetry({"error_rate": 0.01, "latency_ms": 600.0})
        self.assertFalse(result_high_lat["allowed"])

if __name__ == "__main__":
    unittest.main()
