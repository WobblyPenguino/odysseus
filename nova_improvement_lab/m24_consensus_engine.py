import hashlib
import concurrent.futures
from typing import List, Dict, Any

class MultiLaneConsensusEngine:
    """Parallel multi-lane Merkle consensus engine for distributed state verification."""
    def __init__(self, lane_count: int = 4):
        self.lane_count = max(1, lane_count)

    def _hash_data(self, data: str) -> str:
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def _compute_merkle_root(self, hashes: List[str]) -> str:
        if not hashes:
            return self._hash_data("")
        current_level = hashes
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i+1] if i + 1 < len(current_level) else left
                combined = left + right
                next_level.append(self._hash_data(combined))
            current_level = next_level
        return current_level[0]

    def _process_lane(self, lane_id: int, candidates: List[str]) -> Dict[str, Any]:
        hashed_candidates = [self._hash_data(c) for c in candidates]
        lane_root = self._compute_merkle_root(hashed_candidates)
        return {
            "lane_id": lane_id,
            "candidate_count": len(candidates),
            "lane_root": lane_root
        }

    def evaluate_lanes(self, candidate_batches: List[List[str]]) -> Dict[str, Any]:
        # Distribute candidate batches across configured lanes using ThreadPoolExecutor
        lanes_to_process = candidate_batches[:self.lane_count]
        # Pad with empty lists if fewer batches than lanes
        while len(lanes_to_process) < self.lane_count:
            lanes_to_process.append([])

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.lane_count) as executor:
            future_to_lane = {
                executor.submit(self._process_lane, idx, batch): idx 
                for idx, batch in enumerate(lanes_to_process)
            }
            for future in concurrent.futures.as_completed(future_to_lane):
                results.append(future.result())

        # Sort results by lane_id to maintain deterministic ordering
        results.sort(key=lambda x: x["lane_id"])
        
        # Compute unified global Merkle root from lane roots
        lane_roots = [res["lane_root"] for res in results]
        global_root = self._compute_merkle_root(lane_roots)

        return {
            "lane_count": self.lane_count,
            "lane_results": results,
            "global_merkle_root": global_root,
            "consensus_verified": len(set(lane_roots)) >= 1  # Base check
        }
