from typing import Dict, Any, List

class AutonomousCandidateFactory:
    """Factory for generating and validating autonomous code improvement candidates."""
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode

    def create_candidate(self, candidate_id: str, code_diff: str, author: str = "NOVA-Agent") -> Dict[str, Any]:
        return {
            "candidate_id": candidate_id,
            "code_diff": code_diff,
            "author": author,
            "status": "pending_validation"
        }

    def evaluate_candidate(self, candidate: Dict[str, Any]) -> bool:
        # Perform basic structural and security validation
        diff = candidate.get("code_diff", "")
        if not diff or "rm -rf" in diff:
            return False
        if self.strict_mode and len(diff) < 5:
            return False
        return True
