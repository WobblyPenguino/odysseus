import time
from typing import Dict, List, Optional

class SwarmHeartbeatSynchronizer:
    """Tracks node heartbeats and synchronizes cluster health status."""
    def __init__(self, timeout_seconds: float = 5.0):
        self.timeout_seconds = timeout_seconds
        self.node_heartbeats: Dict[str, float] = {}

    def record_heartbeat(self, node_id: str, timestamp: Optional[float] = None) -> None:
        self.node_heartbeats[node_id] = timestamp if timestamp is not None else time.time()

    def check_node_health(self, node_id: str, current_time: Optional[float] = None) -> bool:
        if node_id not in self.node_heartbeats:
            return False
        now = current_time if current_time is not None else time.time()
        return (now - self.node_heartbeats[node_id]) <= self.timeout_seconds

    def get_active_nodes(self, current_time: Optional[float] = None) -> List[str]:
        now = current_time if current_time is not None else time.time()
        return [nid for nid in self.node_heartbeats.items() if (now - nid[1]) <= self.timeout_seconds] and [nid for nid, ts in self.node_heartbeats.items() if (now - ts) <= self.timeout_seconds]
