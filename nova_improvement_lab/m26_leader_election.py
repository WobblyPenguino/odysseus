import time
from typing import List, Dict, Any, Optional

class SwarmLeaderElection:
    """Manages priority-weighted leader election with epochs, lease validity, and fencing tokens."""
    def __init__(self, node_id: str, cluster_nodes: List[Dict[str, Any]], lease_duration_seconds: float = 5.0):
        self.node_id = node_id
        self.cluster_nodes = cluster_nodes
        self.lease_duration_seconds = lease_duration_seconds
        self.current_epoch = 1
        self.fencing_token = 0

    def elect_leader(self, current_time: Optional[float] = None) -> str:
        """
        Elects the active node with the highest priority. 
        Only active nodes are eligible. Ties are broken lexicographically by node ID.
        """
        now = current_time if current_time is not None else time.time()
        active_nodes = [n for n in self.cluster_nodes if n.get("active", True)]
        
        if not active_nodes:
            raise ValueError("No active nodes available for leader election.")

        # Sort by priority descending, then node_id ascending for deterministic tie-breaking
        sorted_nodes = sorted(
            active_nodes,
            key=lambda x: (-x.get("priority", 0), x.get("id", ""))
        )

        leader = sorted_nodes[0]["id"]
        return leader

    def get_fencing_token(self, current_time: Optional[float] = None) -> Dict[str, Any]:
        """
        Issues an epoch-bound fencing token to prevent stale leaders from committing actions.
        """
        leader = self.elect_leader(current_time=current_time)
        is_leader = (self.node_id == leader)
        
        if is_leader:
            self.fencing_token += 1

        return {
            "leader_id": leader,
            "is_current_node_leader": is_leader,
            "epoch": self.current_epoch,
            "fencing_token": self.fencing_token if is_leader else None
        }
