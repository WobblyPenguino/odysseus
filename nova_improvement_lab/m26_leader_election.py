import os
from nova_improvement_lab.m29_epoch_persistence import EpochPersistenceManager

class SwarmLeaderElection:
    def __init__(self, node_id: str, cluster_nodes: list[dict], persistence_path: str = "cluster_state_epoch.json"):
        self.node_id = node_id
        self.cluster_nodes = cluster_nodes
        self.persistence = EpochPersistenceManager(persistence_path)
        self.epoch = 1

    def evaluate_leadership(self) -> bool:
        active_nodes = [n for n in self.cluster_nodes if n.get("active", True)]
        if not active_nodes:
            return False
        leader = max(active_nodes, key=lambda n: (n.get("priority", 0), n.get("id", "")))
        return leader.get("id") == self.node_id

    def get_fencing_token(self) -> dict:
        is_leader = self.evaluate_leadership()
        
        existing = self.persistence.load_state()
        if existing:
            self.epoch = existing.get("epoch", 1)
            current_token = existing.get("fencing_token", 0)
        else:
            current_token = 0

        if not is_leader:
            return {
                "node_id": self.node_id,
                "is_current_node_leader": False,
                "epoch": self.epoch,
                "fencing_token": current_token
            }

        next_token = current_token + 1
        current_root = existing.get("global_merkle_root", "0" * 64) if existing else "0" * 64
        
        self.persistence.save_state(
            epoch=self.epoch,
            fencing_token=next_token,
            global_merkle_root=current_root
        )

        return {
            "node_id": self.node_id,
            "is_current_node_leader": True,
            "epoch": self.epoch,
            "fencing_token": next_token
        }
