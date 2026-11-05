import json
import os
import tempfile
import time

class EpochPersistenceManager:
    def __init__(self, filepath="cluster_state_epoch.json"):
        self.filepath = filepath

    def save_state(self, epoch: int, fencing_token: int, global_merkle_root: str) -> None:
        existing = self.load_state()
        if existing:
            stored_epoch = existing.get("epoch", 0)
            stored_token = existing.get("fencing_token", 0)
            
            if epoch < stored_epoch:
                raise ValueError(f"Monotonic epoch violation: epoch {epoch} < stored epoch {stored_epoch}")
            
            if epoch == stored_epoch and fencing_token <= stored_token:
                raise ValueError(f"Monotonic token rollback violation: token {fencing_token} <= stored token {stored_token}")

        payload = {
            "epoch": int(epoch),
            "fencing_token": int(fencing_token),
            "global_merkle_root": str(global_merkle_root)
        }

        dir_name = os.path.dirname(os.path.abspath(self.filepath)) or "."
        os.makedirs(dir_name, exist_ok=True)

        max_retries = 10
        for attempt in range(max_retries):
            fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)
                os.replace(tmp_path, self.filepath)
                break
            except (PermissionError, OSError) as e:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass
                if attempt == max_retries - 1:
                    raise IOError(f"Failed to atomically persist epoch state after {max_retries} attempts: {e}")
                time.sleep(0.005 * (2 ** attempt))

    def load_state(self) -> dict | None:
        if not os.path.exists(self.filepath):
            return None
        max_retries = 5
        for attempt in range(max_retries):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict) or "epoch" not in data:
                    return None
                return data
            except (PermissionError, json.JSONDecodeError, IOError):
                if attempt == max_retries - 1:
                    return None
                time.sleep(0.002 * (2 ** attempt))
        return None
