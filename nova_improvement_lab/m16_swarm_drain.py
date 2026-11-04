import time
from typing import Dict, Any, List

class SwarmDrainManager:
    """Manages graceful node draining, lease handoffs, and pending transaction flushing."""
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.is_draining = False
        self.pending_transactions: List[str] = []

    def initiate_drain(self) -> Dict[str, Any]:
        """Marks the node as draining, refusing new transaction intake while flushing active queues."""
        self.is_draining = True
        return {
            "node_id": self.node_id,
            "status": "DRAINING",
            "pending_count": len(self.pending_transactions),
            "timestamp": time.time()
        }

    def flush_and_handoff(self) -> Dict[str, Any]:
        """Flushes remaining pending transactions and releases leadership lease."""
        if not self.is_draining:
            return {"success": False, "reason": "Node is not in drain mode."}
        
        flushed = list(self.pending_transactions)
        self.pending_transactions.clear()
        return {
            "success": True,
            "node_id": self.node_id,
            "flushed_transactions": flushed,
            "status": "DRAINED_AND_OFFLINE"
        }
