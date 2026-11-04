import unittest
import time
from nova_improvement_lab.m26_leader_election import SwarmLeaderElection

class TestSwarmLeaderElection(unittest.TestCase):
    def setUp(self):
        self.nodes = [
            {"id": "node_alpha", "priority": 10, "active": True},
            {"id": "node_beta", "priority": 30, "active": True},
            {"id": "node_gamma", "priority": 20, "active": True}
        ]

    def test_highest_priority_wins(self):
        election = SwarmLeaderElection(node_id="node_alpha", cluster_nodes=self.nodes)
        leader = election.elect_leader()
        self.assertEqual(leader, "node_beta")  # node_beta has priority 30

    def test_failover_when_leader_inactive(self):
        # Deactivate node_beta
        nodes_modified = [
            {"id": "node_alpha", "priority": 10, "active": True},
            {"id": "node_beta", "priority": 30, "active": False},
            {"id": "node_gamma", "priority": 20, "active": True}
        ]
        election = SwarmLeaderElection(node_id="node_alpha", cluster_nodes=nodes_modified)
        leader = election.elect_leader()
        self.assertEqual(leader, "node_gamma")  # node_gamma now highest active (priority 20)

    def test_fencing_token_issuance(self):
        election_beta = SwarmLeaderElection(node_id="node_beta", cluster_nodes=self.nodes)
        token_info = election_beta.get_fencing_token()
        self.assertTrue(token_info["is_current_node_leader"])
        self.assertEqual(token_info["leader_id"], "node_beta")
        self.assertIsNotNone(token_info["fencing_token"])

        election_alpha = SwarmLeaderElection(node_id="node_alpha", cluster_nodes=self.nodes)
        token_info_alpha = election_alpha.get_fencing_token()
        self.assertFalse(token_info_alpha["is_current_node_leader"])
        self.assertIsNone(token_info_alpha["fencing_token"])

if __name__ == "__main__":
    unittest.main()
