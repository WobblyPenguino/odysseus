import json
import os
from typing import Dict, Any

class EpochPersistenceManager:
    """Provides durable storage for cluster epochs, fencing tokens, and Merkle audit trails."""
    def __init__(self, storage_path: str = "cluster_state_epoch.json"):
        self.storage_path = storage_path

    def save_state(self, epoch: int, fencing_token: int, global_merkle_root: str) -> None:
        state = {
            "epoch": epoch,
            "fencing_token": fencing_token,
            "global_merkle_root": global_merkle_root
        }
        with open(self.storage_path, "w", encoding="UTF-8") as f:
            json.dump(state, f, indent=2)

    def load_state(self) -> Dict[str, Any]:
        if not os.path.exists(self.storage_path):
            return {"epoch": 1, "fencing_token": 0, "global_merkle_root": None}
        with open(self.storage_path, "r", encoding="UTF-8") as f:
            return json.load(f)
