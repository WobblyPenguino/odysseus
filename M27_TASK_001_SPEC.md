## [M27-TASK-001] Multi-Node Swarm Simulation Harness

- **Branch:** feat/m27-swarm-simulator
- **Target Files:** `nova_improvement_lab/m27_swarm_simulator.py`, `tests_m27_swarm_simulator.py`
- **Objective:** Implement a virtual swarm simulation harness to coordinate multiple cluster managers, simulate time progression, and test resilience against node failures.

### Acceptance Criteria
1. Module exports `SwarmSimulator` class capable of managing multiple virtual node perspectives.
2. Simulator supports time advancement and selective heartbeat broadcasting.
3. Unit test suite `tests_m27_swarm_simulator.py` validates initial leader consensus and automated failover when nodes drop out.
