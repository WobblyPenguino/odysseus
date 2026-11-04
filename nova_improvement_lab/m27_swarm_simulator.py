import time
from typing import List, Dict, Any
from nova_improvement_lab.m26_cluster_manager import SwarmClusterManager

class SwarmSimulator:
    """Simulates a multi-node swarm cluster to test leader election and heartbeat resilience."""
    def __init__(self, node_configs: List[Dict[str, Any]], timeout_seconds: float = 2.0):
        self.timeout_seconds = timeout_seconds
        self.node_configs = node_configs
        # Initialize a manager instance for each node perspective in the swarm
        self.managers = {
            n["id"]: SwarmClusterManager(node_id=n["id"], initial_nodes=node_configs, timeout_seconds=timeout_seconds)
            for n in node_configs
        }
        self.sim_time = time.time()

    def advance_time(self, seconds: float) -> None:
        self.sim_time += seconds

    def send_heartbeat(self, node_id: str) -> None:
        """Broadcasts a heartbeat from a specific node to all swarm perspectives."""
        if node_id in self.managers:
            for mgr in self.managers.values():
                mgr.heartbeat(node_id, timestamp=self.sim_time)

    def get_leader_view(self, observer_node_id: str) -> str:
        """Returns the elected leader ID from the perspective of an observer node."""
        if observer_node_id in self.managers:
            return self.managers[observer_node_id].get_leader(current_time=self.sim_time)
        raise ValueError(f"Observer node {observer_node_id} not found in simulation.")
