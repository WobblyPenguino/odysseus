import unittest
from nova_improvement_lab.m24_consensus_engine import MultiLaneConsensusEngine

class TestMultiLaneConsensusEngine(unittest.TestCase):
    def setUp(self):
        self.engine = MultiLaneConsensusEngine(lane_count=4, quorum_threshold_ratio=0.67)

    def test_default_lane_count(self):
        engine = MultiLaneConsensusEngine()
        self.assertEqual(engine.lane_count, 4)

    def test_uniform_consensus_convergence(self):
        # All lanes produce identical output batches to satisfy quorum ratio >= 0.67
        shared_batch = ["tx1", "tx2"]
        batches = [shared_batch, shared_batch, shared_batch, ["tx3", "tx4"]]
        result = self.engine.evaluate_lanes(batches)
        self.assertTrue(result["consensus_verified"])
        self.assertIsNotNone(result["global_merkle_root"])
        self.assertEqual(len(result["lane_results"]), 4)

    def test_divergent_lanes_fail_consensus(self):
        # All 4 lanes produce completely different batches (divergence / split-brain)
        batches = [
            ["tx1", "tx2"],
            ["tx3", "tx4"],
            ["tx5", "tx6"],
            ["tx7", "tx8"]
        ]
        result = self.engine.evaluate_lanes(batches)
        self.assertFalse(result["consensus_verified"])
        self.assertIsNone(result["global_merkle_root"])

    def test_split_brain_simulation_zero_divergence(self):
        shared_state = ["state_alpha", "state_beta"]
        batches = [shared_state, shared_state, shared_state, shared_state]

        result = self.engine.evaluate_lanes(batches)
        lane_roots = [r["lane_root"] for r in result["lane_results"]]

        self.assertEqual(len(set(lane_roots)), 1)
        self.assertTrue(result["consensus_verified"])
        self.assertIsNotNone(result["global_merkle_root"])

if __name__ == "__main__":
    unittest.main()
