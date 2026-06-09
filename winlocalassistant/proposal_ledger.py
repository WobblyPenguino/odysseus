"""
Proposal Ledger System
Tracks improvement proposals, their implementation status, validation results, and impact.
Enables anti-repeat prevention and audit trails for autonomous improvements.
"""

import logging
import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from datetime import datetime
from typing import Optional, Any, Literal
from enum import Enum

from .config import APP_DIR
from .safe_io import read_json_file, atomic_write_json, append_jsonl

LOGGER = logging.getLogger(__name__)

PROPOSALS_DIR = Path(APP_DIR) / "proposals"
PROPOSALS_DIR.mkdir(exist_ok=True, parents=True)

LEDGER_FILE = PROPOSALS_DIR / "proposal_ledger.jsonl"
IMPACT_MATRIX_FILE = PROPOSALS_DIR / "impact_matrix.json"


class ProposalStatus(Enum):
    PROPOSED = "proposed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    REVERTED = "reverted"


class ProposalRiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ProposalEntry:
    id: str
    title: str
    description: str
    proposed_at: str
    proposed_by: str  # "autonomous", "user", "analyst"
    status: str  # ProposalStatus
    value_score: int  # 0-100
    risk_level: str  # ProposalRiskLevel
    affected_subsystems: list[str] = field(default_factory=list)
    implementation_notes: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    validation_gates: list[str] = field(default_factory=list)
    validation_results: dict[str, bool] = field(default_factory=dict)
    linked_pr: Optional[str] = None
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def is_complete(self) -> bool:
        return self.status == ProposalStatus.COMPLETED.value

    def is_safe(self) -> bool:
        """Check if all validation gates passed"""
        if not self.validation_results:
            return False
        return all(self.validation_results.values())


class ProposalLedger:
    """Manages proposal tracking and audit trail"""

    def __init__(self):
        self.entries: list[ProposalEntry] = self._load_entries()

    def _load_entries(self) -> list[ProposalEntry]:
        """Load all proposal entries from ledger"""
        entries = []
        try:
            if LEDGER_FILE.exists():
                for line in LEDGER_FILE.read_text().strip().split("\n"):
                    if line.strip():
                        data = json.loads(line)
                        entries.append(ProposalEntry(**data))
        except Exception:
            LOGGER.debug("Failed to load proposal ledger entries from %s", LEDGER_FILE, exc_info=True)
        return entries

    def add_proposal(
        self,
        title: str,
        description: str,
        value_score: int,
        risk_level: str = "low",
        proposed_by: str = "user",
        subsystems: Optional[list[str]] = None,
        validation_gates: Optional[list[str]] = None,
        dependencies: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
    ) -> ProposalEntry:
        """Add a new proposal to the ledger"""
        proposal_id = f"prop_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.entries)}"
        
        entry = ProposalEntry(
            id=proposal_id,
            title=title,
            description=description,
            proposed_at=datetime.now().isoformat(),
            proposed_by=proposed_by,
            status=ProposalStatus.PROPOSED.value,
            value_score=value_score,
            risk_level=risk_level,
            affected_subsystems=subsystems or [],
            validation_gates=validation_gates or [],
            dependencies=dependencies or [],
            tags=tags or [],
        )

        self.entries.append(entry)
        try:
            append_jsonl(LEDGER_FILE, entry.to_dict())
        except Exception:
            LOGGER.debug("Failed to append proposal ledger entry %s", entry.id, exc_info=True)

        return entry

    def update_proposal_status(
        self,
        proposal_id: str,
        status: str,
        notes: Optional[str] = None,
    ) -> Optional[ProposalEntry]:
        """Update proposal status and notes"""
        for entry in self.entries:
            if entry.id == proposal_id:
                entry.status = status
                if notes:
                    entry.implementation_notes = notes
                if status == ProposalStatus.IN_PROGRESS.value:
                    entry.started_at = datetime.now().isoformat()
                elif status == ProposalStatus.COMPLETED.value:
                    entry.completed_at = datetime.now().isoformat()
                
                self._save_ledger()
                return entry

        return None

    def record_validation_result(
        self,
        proposal_id: str,
        gate_name: str,
        passed: bool,
    ) -> Optional[ProposalEntry]:
        """Record validation result for a proposal"""
        for entry in self.entries:
            if entry.id == proposal_id:
                entry.validation_results[gate_name] = passed
                self._save_ledger()
                return entry
        return None

    def get_completed_proposals(self) -> list[ProposalEntry]:
        """Get all completed proposals"""
        return [e for e in self.entries if e.is_complete()]

    def get_in_progress_proposals(self) -> list[ProposalEntry]:
        """Get proposals currently being implemented"""
        return [e for e in self.entries if e.status == ProposalStatus.IN_PROGRESS.value]

    def get_proposed_proposals(self) -> list[ProposalEntry]:
        """Get all proposed but not yet started proposals"""
        return [e for e in self.entries if e.status == ProposalStatus.PROPOSED.value]

    def find_similar_completed(self, title: str, subsystems: list[str]) -> list[ProposalEntry]:
        """Find completed proposals with similar scope to prevent repetition"""
        similar = []
        title_lower = title.lower()
        
        for entry in self.get_completed_proposals():
            if entry.title.lower() == title_lower:
                similar.append(entry)
            elif any(sub in entry.affected_subsystems for sub in subsystems):
                if any(word in entry.title.lower() for word in title_lower.split()):
                    similar.append(entry)

        return similar

    def _save_ledger(self) -> None:
        """Rebuild ledger file from entries"""
        try:
            LEDGER_FILE.write_text("")  # Clear
            for entry in self.entries:
                append_jsonl(LEDGER_FILE, entry.to_dict())
        except Exception:
            LOGGER.debug("Failed to save proposal ledger to %s", LEDGER_FILE, exc_info=True)

    def build_impact_matrix(self) -> dict[str, Any]:
        """Build impact/risk matrix for all proposed items"""
        proposed = self.get_proposed_proposals()
        
        matrix = {
            "generated_at": datetime.now().isoformat(),
            "proposals": [],
            "summary": {
                "total": len(proposed),
                "low_risk_high_value": 0,
                "auto_implementable": 0,
            },
        }

        for proposal in sorted(proposed, key=lambda x: (-x.value_score, x.risk_level)):
            risk_score = {"low": 1, "medium": 2, "high": 3}.get(proposal.risk_level, 2)
            auto_impl = risk_score == 1 and proposal.value_score > 70 and not proposal.dependencies
            
            if auto_impl:
                matrix["summary"]["auto_implementable"] += 1
            if risk_score == 1 and proposal.value_score > 70:
                matrix["summary"]["low_risk_high_value"] += 1

            matrix["proposals"].append({
                "id": proposal.id,
                "title": proposal.title,
                "value_score": proposal.value_score,
                "risk_level": proposal.risk_level,
                "auto_implementable": auto_impl,
                "subsystems": proposal.affected_subsystems,
                "dependencies": proposal.dependencies,
            })

        return matrix


def render_proposal_ledger() -> str:
    """Render proposal ledger in markdown"""
    ledger = ProposalLedger()
    
    md = "# Proposal Ledger\n\n"
    md += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"

    # Completed
    completed = ledger.get_completed_proposals()
    md += f"## Completed Proposals ({len(completed)})\n\n"
    for prop in completed[:10]:  # Show last 10
        md += f"### {prop.title}\n"
        md += f"- **Status**: {prop.status}\n"
        md += f"- **Value Score**: {prop.value_score}/100\n"
        md += f"- **Risk**: {prop.risk_level}\n"
        if prop.completed_at:
            md += f"- **Completed**: {prop.completed_at}\n"
        md += "\n"

    # In Progress
    in_progress = ledger.get_in_progress_proposals()
    md += f"## In Progress ({len(in_progress)})\n\n"
    for prop in in_progress:
        md += f"- **{prop.title}** (value: {prop.value_score}/100)\n"
    md += "\n"

    # Proposed
    proposed = ledger.get_proposed_proposals()
    md += f"## Proposed ({len(proposed)})\n\n"
    for prop in sorted(proposed, key=lambda x: -x.value_score)[:5]:
        md += f"- **{prop.title}** (value: {prop.value_score}/100, risk: {prop.risk_level})\n"

    return md


# Global ledger instance
_proposal_ledger: Optional[ProposalLedger] = None


def get_proposal_ledger() -> ProposalLedger:
    """Get or create the global proposal ledger"""
    global _proposal_ledger
    if _proposal_ledger is None:
        _proposal_ledger = ProposalLedger()
    return _proposal_ledger
