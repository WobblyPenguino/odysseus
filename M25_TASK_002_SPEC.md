## [M25-TASK-002] Live Telemetry and Consensus Gating Integration

- **Branch:** feat/m25-telemetry-consensus
- **Target Files:** `nova_improvement_lab/m25_telemetry_gate.py`, `tests_m25_telemetry_gate.py`
- **Objective:** Integrate live telemetry metrics monitoring with consensus gating to throttle unhealthy candidate batches and prevent execution under degraded network or error conditions.

### Acceptance Criteria
1. Module exports `TelemetryConsensusGate` class with configurable error and latency thresholds.
2. Gate correctly evaluates live metrics dictionary (error rate and node latency).
3. Unit test suite `tests_m25_telemetry_gate.py` passes for healthy, high-error, and high-latency states.
