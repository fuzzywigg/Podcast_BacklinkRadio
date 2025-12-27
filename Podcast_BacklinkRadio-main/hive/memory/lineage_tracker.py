"""
Lineage Tracker - Version control for bee templates.

Tracks the evolutionary history of bee types, allowing:
- Version tracking of bee templates
- Evolution proposals from cloned bees
- Governance approval of updates
- Rollback to previous versions

This is the "genetic" evolution system for the hive.
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
import threading


class UpdateStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


@dataclass
class LineageVersion:
    """A specific version of a bee template."""
    version: str
    bee_type: str
    template_hash: str
    created_at: str
    created_by: str  # "origin" or hive that proposed it
    changes: List[str]
    performance_metrics: Dict[str, float]
    parent_version: Optional[str] = None


@dataclass
class UpdateProposal:
    """A proposal to update a bee template."""
    id: str
    bee_type: str
    proposed_version: str
    current_version: str
    proposed_by: str  # Hive ID that proposed
    proposed_at: str
    changes: List[str]
    evidence: Dict[str, Any]  # Performance evidence
    status: str = "pending"
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    rejection_reason: Optional[str] = None


class LineageTracker:
    """
    Tracks bee template versions and evolution proposals.
    
    When a bee clone outperforms its origin:
    1. It creates an UpdateProposal with evidence
    2. The Evolution Governor evaluates the proposal
    3. If approved, the new version becomes canonical
    4. All future clones use the updated template
    """
    
    def __init__(self, hive_path: Optional[str] = None):
        """Initialize lineage tracker."""
        if hive_path is None:
            hive_path = Path(__file__).parent.parent
        self.hive_path = Path(hive_path)
        self.lineage_file = self.hive_path / "honeycomb" / "lineage.json"
        self._lock = threading.Lock()
        
        # In-memory state
        self._versions: Dict[str, Dict[str, LineageVersion]] = {}  # bee_type -> version -> LineageVersion
        self._current: Dict[str, str] = {}  # bee_type -> current version
        self._proposals: Dict[str, UpdateProposal] = {}  # proposal_id -> UpdateProposal
        
        self._ensure_lineage_file()
        self._load()
    
    def _ensure_lineage_file(self) -> None:
        """Ensure lineage.json exists."""
        if not self.lineage_file.exists():
            initial = {
                "_meta": {
                    "version": "1.0.0",
                    "description": "Bee lineage tracking - evolutionary history",
                    "created": datetime.now(timezone.utc).isoformat()
                },
                "bee_types": {},
                "proposals": [],
                "stats": {
                    "total_versions": 0,
                    "total_proposals": 0,
                    "approved_proposals": 0,
                    "rejected_proposals": 0
                }
            }
            self.lineage_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.lineage_file, 'w') as f:
                json.dump(initial, f, indent=2)
    
    def _load(self) -> None:
        """Load lineage data from disk."""
        with self._lock:
            try:
                with open(self.lineage_file, 'r') as f:
                    data = json.load(f)
                
                # Load versions
                for bee_type, type_data in data.get("bee_types", {}).items():
                    self._versions[bee_type] = {}
                    self._current[bee_type] = type_data.get("current_version", "1.0.0")
                    
                    for version_dict in type_data.get("versions", []):
                        version = LineageVersion(**version_dict)
                        self._versions[bee_type][version.version] = version
                
                # Load proposals
                for proposal_dict in data.get("proposals", []):
                    proposal = UpdateProposal(**proposal_dict)
                    self._proposals[proposal.id] = proposal
                    
            except Exception:
                self._versions = {}
                self._current = {}
                self._proposals = {}
    
    def _persist(self) -> None:
        """Persist lineage data to disk."""
        bee_types_data = {}
        for bee_type, versions in self._versions.items():
            bee_types_data[bee_type] = {
                "current_version": self._current.get(bee_type, "1.0.0"),
                "versions": [asdict(v) for v in versions.values()]
            }
        
        # Calculate stats
        approved = sum(1 for p in self._proposals.values() if p.status == "approved")
        rejected = sum(1 for p in self._proposals.values() if p.status == "rejected")
        
        data = {
            "_meta": {
                "version": "1.0.0",
                "description": "Bee lineage tracking - evolutionary history",
                "last_updated": datetime.now(timezone.utc).isoformat()
            },
            "bee_types": bee_types_data,
            "proposals": [asdict(p) for p in self._proposals.values()],
            "stats": {
                "total_versions": sum(len(v) for v in self._versions.values()),
                "total_proposals": len(self._proposals),
                "approved_proposals": approved,
                "rejected_proposals": rejected
            }
        }
        
        with open(self.lineage_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def register_bee_type(
        self,
        bee_type: str,
        initial_version: str = "1.0.0",
        template_hash: Optional[str] = None
    ) -> None:
        """Register a new bee type with initial version."""
        with self._lock:
            if bee_type not in self._versions:
                self._versions[bee_type] = {}
                self._current[bee_type] = initial_version
                
                version = LineageVersion(
                    version=initial_version,
                    bee_type=bee_type,
                    template_hash=template_hash or self._hash_template(bee_type),
                    created_at=datetime.now(timezone.utc).isoformat(),
                    created_by="origin",
                    changes=["Initial version"],
                    performance_metrics={}
                )
                self._versions[bee_type][initial_version] = version
                self._persist()
    
    def _hash_template(self, bee_type: str) -> str:
        """Generate hash for bee template file."""
        # Try to find the bee file and hash it
        try:
            # Map bee type to potential file locations
            bee_file = None
            for category in ["content", "research", "marketing", "monetization", 
                           "community", "technical", "admin", "cognitive", "safety"]:
                potential = self.hive_path / "bees" / category / f"{self._to_snake_case(bee_type)}.py"
                if potential.exists():
                    bee_file = potential
                    break
            
            if bee_file:
                content = bee_file.read_text()
                return hashlib.sha256(content.encode()).hexdigest()[:16]
        except Exception:
            pass
        
        return hashlib.sha256(bee_type.encode()).hexdigest()[:16]
    
    def _to_snake_case(self, name: str) -> str:
        """Convert BeeTypeName to bee_type_name."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def get_current_version(self, bee_type: str) -> str:
        """Get current canonical version for a bee type."""
        return self._current.get(bee_type, "1.0.0")
    
    def get_version(self, bee_type: str, version: str) -> Optional[LineageVersion]:
        """Get specific version of a bee type."""
        return self._versions.get(bee_type, {}).get(version)
    
    def propose_update(
        self,
        bee_type: str,
        changes: List[str],
        evidence: Dict[str, Any],
        proposed_by: str = "unknown_hive"
    ) -> str:
        """
        Propose an update to a bee template.
        
        This is called when a cloned bee outperforms its origin.
        
        Args:
            bee_type: Type of bee to update
            changes: List of changes made
            evidence: Performance evidence (metrics, success rate, etc.)
            proposed_by: ID of hive proposing the update
        
        Returns:
            Proposal ID
        """
        with self._lock:
            # Ensure bee type is registered
            if bee_type not in self._versions:
                self.register_bee_type(bee_type)
            
            current = self._current[bee_type]
            
            # Generate new version
            parts = current.split(".")
            new_version = f"{parts[0]}.{int(parts[1]) + 1}.0"
            
            # Create proposal
            proposal_id = hashlib.sha256(
                f"{bee_type}:{new_version}:{datetime.now().isoformat()}".encode()
            ).hexdigest()[:12]
            
            proposal = UpdateProposal(
                id=proposal_id,
                bee_type=bee_type,
                proposed_version=new_version,
                current_version=current,
                proposed_by=proposed_by,
                proposed_at=datetime.now(timezone.utc).isoformat(),
                changes=changes,
                evidence=evidence
            )
            
            self._proposals[proposal_id] = proposal
            self._persist()
            
            return proposal_id
    
    def approve_proposal(
        self,
        proposal_id: str,
        reviewer: str = "evolution_governor"
    ) -> bool:
        """
        Approve an update proposal.
        
        This makes the proposed version the new canonical version.
        """
        with self._lock:
            proposal = self._proposals.get(proposal_id)
            if not proposal or proposal.status != "pending":
                return False
            
            # Create new version
            new_version = LineageVersion(
                version=proposal.proposed_version,
                bee_type=proposal.bee_type,
                template_hash=self._hash_template(proposal.bee_type),
                created_at=datetime.now(timezone.utc).isoformat(),
                created_by=proposal.proposed_by,
                changes=proposal.changes,
                performance_metrics=proposal.evidence.get("metrics", {}),
                parent_version=proposal.current_version
            )
            
            # Update state
            self._versions[proposal.bee_type][proposal.proposed_version] = new_version
            self._current[proposal.bee_type] = proposal.proposed_version
            
            # Update proposal
            proposal.status = "approved"
            proposal.reviewed_at = datetime.now(timezone.utc).isoformat()
            proposal.reviewed_by = reviewer
            
            self._persist()
            return True
    
    def reject_proposal(
        self,
        proposal_id: str,
        reason: str,
        reviewer: str = "evolution_governor"
    ) -> bool:
        """Reject an update proposal."""
        with self._lock:
            proposal = self._proposals.get(proposal_id)
            if not proposal or proposal.status != "pending":
                return False
            
            proposal.status = "rejected"
            proposal.rejection_reason = reason
            proposal.reviewed_at = datetime.now(timezone.utc).isoformat()
            proposal.reviewed_by = reviewer
            
            self._persist()
            return True
    
    def get_pending_proposals(self) -> List[UpdateProposal]:
        """Get all pending update proposals."""
        return [p for p in self._proposals.values() if p.status == "pending"]
    
    def get_lineage_history(self, bee_type: str) -> List[LineageVersion]:
        """Get full version history for a bee type."""
        versions = list(self._versions.get(bee_type, {}).values())
        versions.sort(key=lambda v: v.created_at)
        return versions
    
    def get_stats(self) -> Dict[str, Any]:
        """Get lineage tracking statistics."""
        return {
            "registered_bee_types": len(self._versions),
            "total_versions": sum(len(v) for v in self._versions.values()),
            "pending_proposals": sum(1 for p in self._proposals.values() if p.status == "pending"),
            "approved_proposals": sum(1 for p in self._proposals.values() if p.status == "approved"),
            "rejected_proposals": sum(1 for p in self._proposals.values() if p.status == "rejected"),
            "current_versions": dict(self._current)
        }
