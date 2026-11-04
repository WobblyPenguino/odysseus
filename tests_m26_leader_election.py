import unittest
from nova_improvement_lab.m26_leader_election import SwarmLeaderElection

class TestSwarmLeaderElection(unittest.TestCase):
    def setUp(self):
        self.nodes = [
            {"id": "node_alpha", "priority": 10, "active": True},
            {"id": "node_beta", "priority": 20, "active": True},
            {"id": "node_gamma", "priority": 15, "active": True}
        ]
        self.election = SwarmLeaderElection(node_id="node_alpha", cluster_nodes=self.nodes)

    def test_highest_priority_elected(self):
        leader = self.election.elect_leader()
        # node_beta has priority 20 (highest)
        self.assertEqual(leader, "node_beta")

    def test_failover_promotion(self):
        self.election.elect_leader()
        # Simulate failure of node_beta
        new_leader = self.election.handle_heartbeat_failure("node_beta")
        # node_gamma has priority 15 (next highest active node)
        self.assertEqual(new_leader, "node_gamma")

if __name__ == "__main__":
    unittest.main()
