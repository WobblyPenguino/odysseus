from typing import List, Dict, Any, Optional

class SwarmLeaderElection:
    """Decentralized swarm leader election with priority weighting and heartbeat failover."""
    def __init__(self, node_id: str, cluster_nodes: List[Dict[str, Any]]):
        self.node_id = node_id
        self.cluster_nodes = {n["id"]: n for n in cluster_nodes}
        self.current_leader: Optional[str] = None
        self.is_leader = False

    def elect_leader(self) -> str:
        # Filter active nodes
        active = [n for n in self.cluster_nodes.values() if n.get("active", True)]
        if not active:
            raise ValueError("No active nodes available for election.")
        
        # Sort by priority descending, then by node ID ascending for determinism
        active.sort(key=lambda x: (-x.get("priority", 0), x["id"]))
        self.current_leader = active[0]["id"]
        self.is_leader = (self.current_leader == self.node_id)
        return self.current_leader

    def handle_heartbeat_failure(self, failed_node_id: str) -> str:
        if failed_node_id in self.cluster_nodes:
            self.cluster_nodes[failed_node_id]["active"] = False
        return self.elect_leader()
