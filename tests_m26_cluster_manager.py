import unittest
import time
from nova_improvement_lab.m26_cluster_manager import SwarmClusterManager

class TestSwarmClusterManager(unittest.TestCase):
    def setUp(self):
        self.nodes = [
            {"id": "node_alpha", "priority": 10, "active": True},
            {"id": "node_beta", "priority": 20, "active": True}
        ]
        self.manager = SwarmClusterManager(node_id="node_alpha", initial_nodes=self.nodes, timeout_seconds=2.0)

    def test_initial_leader(self):
        now = time.time()
        self.manager.heartbeat("node_alpha", timestamp=now)
        self.manager.heartbeat("node_beta", timestamp=now)
        leader = self.manager.get_leader(current_time=now)
        self.assertEqual(leader, "node_beta")  # node_beta has priority 20

    def test_failover_on_heartbeat_timeout(self):
        now = time.time()
        # Initial heartbeats at t=0
        self.manager.heartbeat("node_alpha", timestamp=now)
        self.manager.heartbeat("node_beta", timestamp=now)
        
        # Refresh node_alpha's heartbeat at t=2.5 (node_beta remains stale since t=0, exceeding timeout of 2.0)
        self.manager.heartbeat("node_alpha", timestamp=now + 2.5)
        
        leader = self.manager.get_leader(current_time=now + 3.0)
        # node_beta has expired, so node_alpha takes over leadership
        self.assertEqual(leader, "node_alpha")

if __name__ == "__main__":
    unittest.main()
