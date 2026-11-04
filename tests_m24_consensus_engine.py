import unittest
from nova_improvement_lab.m24_consensus_engine import MultiLaneConsensusEngine

class TestMultiLaneConsensusEngine(unittest.TestCase):
    def setUp(self):
        self.engine = MultiLaneConsensusEngine(lane_count=4)

    def test_default_lane_count(self):
        engine = MultiLaneConsensusEngine()
        self.assertEqual(engine.lane_count, 4)

    def test_uniform_consensus_convergence(self):
        batches = [
            ["tx1", "tx2"],
            ["tx3", "tx4"],
            ["tx5", "tx6"],
            ["tx7", "tx8"]
        ]
        result = self.engine.evaluate_lanes(batches)
        self.assertTrue(result["consensus_verified"])
        self.assertIsNotNone(result["global_merkle_root"])
        self.assertEqual(len(result["lane_results"]), 4)

    def test_split_brain_simulation_zero_divergence(self):
        # Simulate identical split-brain state fed into multiple lanes
        shared_state = ["state_alpha", "state_beta"]
        batches = [shared_state, shared_state, shared_state, shared_state]
        
        result = self.engine.evaluate_lanes(batches)
        lane_roots = [r["lane_root"] for r in result["lane_results"]]
        
        # All lanes processing identical input must produce identical roots
        self.assertEqual(len(set(lane_roots)), 1)
        self.assertIsNotNone(result["global_merkle_root"])

if __name__ == "__main__":
    unittest.main()
