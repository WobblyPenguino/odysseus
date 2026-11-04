import unittest
import time
from nova_improvement_lab.m26_heartbeat_sync import SwarmHeartbeatSynchronizer

class TestSwarmHeartbeatSynchronizer(unittest.TestCase):
    def setUp(self):
        self.sync = SwarmHeartbeatSynchronizer(timeout_seconds=2.0)

    def test_active_node_health(self):
        now = time.time()
        self.sync.record_heartbeat("node_alpha", timestamp=now)
        self.assertTrue(self.sync.check_node_health("node_alpha", current_time=now + 1.0))

    def test_expired_node_health(self):
        now = time.time()
        self.sync.record_heartbeat("node_beta", timestamp=now)
        self.assertFalse(self.sync.check_node_health("node_beta", current_time=now + 3.0))

    def test_get_active_nodes(self):
        now = time.time()
        self.sync.record_heartbeat("node_1", timestamp=now)
        self.sync.record_heartbeat("node_2", timestamp=now - 3.0)  # Expired
        active = self.sync.get_active_nodes(current_time=now)
        self.assertIn("node_1", active)
        self.assertNotIn("node_2", active)

if __name__ == "__main__":
    unittest.main()
