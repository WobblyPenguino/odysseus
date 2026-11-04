import unittest
from nova_improvement_lab.m24_consensus_engine import MultiLaneConsensusEngine
from nova_improvement_lab.m25_telemetry_gate import TelemetryConsensusGate
from nova_improvement_lab.m26_leader_election import SwarmLeaderElection

class TestSwarmPartitionAndFailoverSimulation(unittest.TestCase):
    def setUp(self):
        self.consensus_engine = MultiLaneConsensusEngine(lane_count=4, quorum_threshold_ratio=0.67)
        self.telemetry_gate = TelemetryConsensusGate(max_error_rate=0.05, max_latency_ms=500.0)

    def test_partition_split_brain_rejection(self):
        # Simulate a network split: 4 nodes divided. Minority partition cannot reach quorum ratio >= 0.67
        minority_batches = [
            ["tx_partition_A"],
            ["tx_partition_B"]
        ]
        result = self.consensus_engine.evaluate_lanes(minority_batches)
        self.assertFalse(result["consensus_verified"])
        self.assertIsNone(result["global_merkle_root"])

    def test_telemetry_spike_fail_closed_under_partition(self):
        # Under network degradation, telemetry spikes error rate and latency
        degraded_telemetry = {"error_rate": 0.15, "latency_ms": 1200.0}
        gate_result = self.telemetry_gate.evaluate_telemetry(degraded_telemetry)
        self.assertFalse(gate_result["allowed"])

    def test_epoch_fenced_failover(self):
        nodes = [
            {"id": "node_alpha", "priority": 10, "active": False},
            {"id": "node_beta", "priority": 30, "active": True}
        ]
        election = SwarmLeaderElection(node_id="node_beta", cluster_nodes=nodes)
        token_info = election.get_fencing_token()
        self.assertTrue(token_info["is_current_node_leader"])
        self.assertEqual(token_info["leader_id"], "node_beta")
        self.assertIsNotNone(token_info["fencing_token"])

if __name__ == "__main__":
    unittest.main()
