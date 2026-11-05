import json
import os
import tempfile

class EpochPersistenceManager:
    def __init__(self, filepath="cluster_state_epoch.json"):
        self.filepath = filepath

    def save_state(self, epoch: int, fencing_token: int, global_merkle_root: str) -> None:
        existing = self.load_state()
        if existing and epoch < existing.get("epoch", 0):
            raise ValueError(f"Monotonic epoch violation: new epoch {epoch} < stored epoch {existing.get("epoch")}")

        payload = {
            "epoch": int(epoch),
            "fencing_token": int(fencing_token),
            "global_merkle_root": str(global_merkle_root)
        }

        dir_name = os.path.dirname(os.path.abspath(self.filepath)) or "."
        os.makedirs(dir_name, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            os.replace(tmp_path, self.filepath)
        except Exception as e:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise IOError(f"Failed to atomically persist epoch state: {e}")

    def load_state(self) -> dict | None:
        if not os.path.exists(self.filepath):
            return None
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict) or "epoch" not in data:
                return None
            return data
        except (json.JSONDecodeError, IOError):
            return None
