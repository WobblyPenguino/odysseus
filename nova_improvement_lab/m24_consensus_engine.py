import hashlib
import json
from typing import List, Dict, Any, Counter

class MultiLaneConsensusEngine:
    """Evaluates multi-lane candidate outputs, computes lane roots, and enforces strict quorum agreement."""
    def __init__(self, lane_count: int = 4, quorum_threshold_ratio: float = 0.67):
        self.lane_count = lane_count
        self.quorum_threshold_ratio = quorum_threshold_ratio

    def evaluate_lanes(self, candidate_batches: List[Any]) -> Dict[str, Any]:
        """
        Evaluates independent candidate batches from each lane, computes their respective roots,
        and enforces strict quorum agreement. Completely divergent batches will fail consensus.
        """
        if not candidate_batches:
            return {
                "consensus_verified": False,
                "verified": False,
                "global_merkle_root": None,
                "merkle_root": None,
                "consensus_ratio": 0.0,
                "participating_lanes": 0,
                "lane_results": [],
                "reason": "No candidate batches provided."
            }

        normalized_lanes = []
        roots = []

        for lane in candidate_batches:
            root = None
            verified = True
            if isinstance(lane, dict):
                root = lane.get("merkle_root") or lane.get("lane_root") or lane.get("root")
                verified = lane.get("verified", True)
            elif isinstance(lane, (list, tuple)):
                serialized = json.dumps(lane, sort_keys=True)
                root = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
            elif lane is not None:
                serialized = str(lane)
                root = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

            if root is not None:
                roots.append(root)
                normalized_lanes.append({"lane_root": root, "verified": verified})
            else:
                normalized_lanes.append({"lane_root": None, "verified": False})

        if not roots or len(roots) != len(candidate_batches):
            return {
                "consensus_verified": False,
                "verified": False,
                "global_merkle_root": None,
                "merkle_root": None,
                "consensus_ratio": 0.0,
                "participating_lanes": len(candidate_batches),
                "lane_results": normalized_lanes,
                "reason": "Malformed lane results or missing valid roots."
            }

        # Count frequencies of each root to determine quorum
        counts = Counter(roots)
        top_root, top_count = counts.most_common(1)[0]
        consensus_ratio = top_count / len(candidate_batches)

        is_verified = consensus_ratio >= self.quorum_threshold_ratio

        return {
            "consensus_verified": is_verified,
            "verified": is_verified,
            "global_merkle_root": top_root if is_verified else None,
            "merkle_root": top_root if is_verified else None,
            "consensus_ratio": consensus_ratio,
            "participating_lanes": len(candidate_batches),
            "lane_results": normalized_lanes,
            "reason": "" if is_verified else f"Quorum not met. Consensus ratio {consensus_ratio:.2f} below required {self.quorum_threshold_ratio}."
        }

    def verify_consensus(self, lane_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verifies pre-computed lane result dictionaries against quorum requirements."""
        return self.evaluate_lanes(lane_results)
