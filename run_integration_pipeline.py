import unittest
from nova_improvement_lab.m24_consensus_engine import MultiLaneConsensusEngine
from nova_improvement_lab.m25_telemetry_gate import TelemetryConsensusGate
from nova_improvement_lab.m26_leader_election import SwarmLeaderElection
from nova_improvement_lab.m29_epoch_persistence import EpochPersistenceManager

class TestOdysseusMainIntegrationPipeline(unittest.TestCase):
    def setUp(self):
        self.consensus = MultiLaneConsensusEngine(lane_count=4, quorum_threshold_ratio=0.67)
        self.telemetry = TelemetryConsensusGate(max_error_rate=0.05, max_latency_ms=500.0)
        self.persistence = EpochPersistenceManager("integration_audit_state.json")

    def test_end_to_end_pipeline_success(self):
        # 1. Simulate incoming MAIN telemetry check
        health_packet = {"error_rate": 0.01, "latency_ms": 120.0}
        gate_res = self.telemetry.evaluate_telemetry(health_packet)
        self.assertTrue(gate_res["allowed"], "Telemetry gate failed healthy packet.")

        # 2. Simulate MAIN transaction batches across 4 lanes reaching consensus
        batches = [["tx_main_1", "tx_main_2"], ["tx_main_1", "tx_main_2"], ["tx_main_1", "tx_main_2"], ["tx_main_3", "tx_main_4"]]
        consensus_res = self.consensus.evaluate_lanes(batches)
        self.assertTrue(consensus_res["consensus_verified"])
        global_root = consensus_res["global_merkle_root"]

        # 3. Simulate Leader Election & Fencing Token issuance
        nodes = [{"id": "sidecar_node_1", "priority": 50, "active": True}]
        election = SwarmLeaderElection(node_id="sidecar_node_1", cluster_nodes=nodes)
        fencing_info = election.get_fencing_token()
        self.assertTrue(fencing_info["is_current_node_leader"])

        # 4. Persist durable epoch state (M29)
        self.persistence.save_state(
            epoch=fencing_info["epoch"],
            fencing_token=fencing_info["fencing_token"],
            global_merkle_root=global_root
        )

        loaded_state = self.persistence.load_state()
        self.assertEqual(loaded_state["epoch"], fencing_info["epoch"])
        self.assertEqual(loaded_state["global_merkle_root"], global_root)

if __name__ == "__main__":
    unittest.main()
