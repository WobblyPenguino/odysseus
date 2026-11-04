import unittest
from nova_improvement_lab.m25_telemetry_gate import TelemetryConsensusGate

class TestTelemetryConsensusGate(unittest.TestCase):
    def setUp(self):
        self.gate = TelemetryConsensusGate(error_threshold=0.05, max_latency_ms=2000.0)

    def test_healthy_telemetry_passes(self):
        metrics = {"error_rate": 0.01, "node_latency_ms": 120.0}
        self.assertTrue(self.gate.evaluate_telemetry(metrics))

    def test_high_error_rate_fails(self):
        metrics = {"error_rate": 0.10, "node_latency_ms": 100.0}
        self.assertFalse(self.gate.evaluate_telemetry(metrics))

    def test_high_latency_fails(self):
        metrics = {"error_rate": 0.01, "node_latency_ms": 2500.0}
        self.assertFalse(self.gate.evaluate_telemetry(metrics))

if __name__ == "__main__":
    unittest.main()
