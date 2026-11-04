import unittest
from nova_improvement_lab.m27_swarm_simulator import SwarmSimulator

class TestSwarmSimulator(unittest.TestCase):
    def setUp(self):
        self.node_configs = [
            {"id": "node_alpha", "priority": 10, "active": True},
            {"id": "node_beta", "priority": 30, "active": True},
            {"id": "node_gamma", "priority": 20, "active": True}
        ]
        self.sim = SwarmSimulator(self.node_configs, timeout_seconds=2.0)

    def test_simulation_initial_leader(self):
        # Broadcast initial heartbeats for all nodes at t=0
        for n in self.node_configs:
            self.sim.send_heartbeat(n["id"])
        
        # node_beta has highest priority (30)
        leader = self.sim.get_leader_view("node_alpha")
        self.assertEqual(leader, "node_beta")

    def test_simulation_failover_after_node_dropout(self):
        # Broadcast initial heartbeats at t=0
        for n in self.node_configs:
            self.sim.send_heartbeat(n["id"])

        # Advance time by 3 seconds (exceeding 2.0s timeout), but ONLY refresh alpha and gamma
        self.sim.advance_time(3.0)
        self.sim.send_heartbeat("node_alpha")
        self.sim.send_heartbeat("node_gamma")
        # node_beta is now stale (no heartbeat at t=3.0)

        # From alpha's perspective, active nodes are alpha (p=10) and gamma (p=20)
        # node_gamma should now win leadership (p=20)
        leader = self.sim.get_leader_view("node_alpha")
        self.assertEqual(leader, "node_gamma")

if __name__ == "__main__":
    unittest.main()
