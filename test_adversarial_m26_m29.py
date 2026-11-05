import unittest
import os
import json
from nova_improvement_lab.m26_leader_election import SwarmLeaderElection
from nova_improvement_lab.m29_epoch_persistence import EpochPersistenceManager

class TestAdversarialM26M29(unittest.TestCase):
    def setUp(self):
        self.state_file = "adversarial_audit_state.json"
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

    def tearDown(self):
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

    def test_partitioned_nodes_split_brain_rejection(self):
        nodes = [
            {"id": "node_1", "priority": 100, "active": True},
            {"id": "node_2", "priority": 50, "active": True}
        ]
        e1 = SwarmLeaderElection("node_1", nodes, self.state_file)
        e2 = SwarmLeaderElection("node_2", nodes, self.state_file)

        t1 = e1.get_fencing_token()
        t2 = e2.get_fencing_token()

        self.assertTrue(t1["is_current_node_leader"])
        self.assertFalse(t2["is_current_node_leader"])

    def test_same_epoch_lower_token_rollback_rejection(self):
        p = EpochPersistenceManager(self.state_file)
        p.save_state(epoch=1, fencing_token=5, global_merkle_root="0"*64)
        
        with self.assertRaises(ValueError):
            p.save_state(epoch=1, fencing_token=4, global_merkle_root="0"*64)

    def test_independent_sequential_clients_monotonicity(self):
        nodes = [{"id": "node_1", "priority": 100, "active": True}]
        
        client_a = SwarmLeaderElection("node_1", nodes, self.state_file)
        token_a = client_a.get_fencing_token()
        self.assertEqual(token_a["fencing_token"], 1)

        client_b = SwarmLeaderElection("node_1", nodes, self.state_file)
        token_b = client_b.get_fencing_token()
        self.assertEqual(token_b["fencing_token"], 2)

if __name__ == "__main__":
    unittest.main()
