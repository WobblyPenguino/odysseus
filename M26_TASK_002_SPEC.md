## [M26-TASK-002] Swarm Heartbeat and Node Health Synchronization

- **Branch:** feat/m26-swarm-heartbeat
- **Target Files:** `nova_improvement_lab/m26_heartbeat_sync.py`, `tests_m26_heartbeat_sync.py`
- **Objective:** Implement heartbeat tracking and health synchronization to automatically detect stale nodes and maintain cluster liveness.

### Acceptance Criteria
1. Module exports `SwarmHeartbeatSynchronizer` class with configurable timeout thresholds.
2. Synchronizer records node heartbeats and evaluates liveness based on elapsed time.
3. Unit test suite `tests_m26_heartbeat_sync.py` validates active and expired node states.
