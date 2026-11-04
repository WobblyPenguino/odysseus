from typing import List, Dict, Any, Optional
from nova_improvement_lab.m26_heartbeat_sync import SwarmHeartbeatSynchronizer
from nova_improvement_lab.m26_leader_election import SwarmLeaderElection

class SwarmClusterManager:
    """Manages cluster node heartbeats, health synchronization, and dynamic leader election."""
    def __init__(self, node_id: str, initial_nodes: List[Dict[str, Any]], timeout_seconds: float = 5.0):
        self.node_id = node_id
        self.heartbeat_sync = SwarmHeartbeatSynchronizer(timeout_seconds=timeout_seconds)
        self.nodes = initial_nodes
        # Register initial active nodes in heartbeat sync
        for n in initial_nodes:
            if n.get("active", True):
                self.heartbeat_sync.record_heartbeat(n["id"])

    def heartbeat(self, node_id: str, timestamp: Optional[float] = None) -> None:
        self.heartbeat_sync.record_heartbeat(node_id, timestamp=timestamp)

    def get_leader(self, current_time: Optional[float] = None) -> str:
        # Retrieve active node IDs based on heartbeat timeouts
        active_ids = self.heartbeat_sync.get_active_nodes(current_time=current_time)
        
        updated_nodes = []
        for n in self.nodes:
            node_copy = n.copy()
            # If node is tracked in heartbeats, update its active status based on liveness
            if node_copy["id"] in self.heartbeat_sync.node_heartbeats:
                node_copy["active"] = node_copy["id"] in active_ids
            updated_nodes.append(node_copy)

        election = SwarmLeaderElection(node_id=self.node_id, cluster_nodes=updated_nodes)
        return election.elect_leader()
