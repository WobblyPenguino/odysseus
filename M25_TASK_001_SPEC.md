## [M25-TASK-001] Autonomous Candidate Factory and Reliability Gate Integration

- **Branch:** feat/m25-candidate-factory-verification
- **Target Files:** `nova_improvement_lab/autonomous_candidate_factory.py`, `tests_autonomous_candidate_factory.py`
- **Objective:** Connect the autonomous candidate generation pipeline with strict reliability gating to filter candidate code patches prior to sandbox execution.

### Acceptance Criteria
1. Candidate factory generates valid patch proposals with metadata tags.
2. Reliability gate evaluates candidate complexity and security boundaries.
3. Unit test suite `tests_autonomous_candidate_factory.py` validates passing and failing candidate submissions.
