"""
Evolution Governor Bee - Manages bee template evolution.

The Evolution Governor evaluates and approves/rejects update proposals
from cloned bees. When a bee in Hive B outperforms its origin from
Hive A, it can propose an update. The Governor:
- Evaluates evidence supporting the update
- Checks for coherence with hive constraints
- Approves or rejects the proposal
- Updates canonical bee templates when approved
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_bee import OnlookerBee


class EvolutionGovernorBee(OnlookerBee):
    """
    Evolution Governor - Manages bee evolution proposals.
    
    Responsibilities:
    - Review pending evolution proposals
    - Evaluate performance evidence
    - Check coherence with hive constraints
    - Approve or reject updates
    - Propagate approved changes to canonical templates
    
    This is the "governance layer" for bee evolution,
    ensuring updates are beneficial and coherent.
    """
    
    BEE_TYPE = "evolution_governor"
    BEE_NAME = "Evolution Governor"
    CATEGORY = "cognitive"
    LINEAGE_VERSION = "1.0.0"
    
    # Governance thresholds
    MIN_IMPROVEMENT_THRESHOLD = 0.15  # 15% improvement required
    MIN_EVIDENCE_SAMPLES = 3  # Minimum successful task samples
    MAX_PENDING_PROPOSALS = 20  # Alert if backlog exceeds
    
    def __init__(self, hive_path: Optional[str] = None, gateway: Any = None):
        """Initialize Evolution Governor."""
        super().__init__(hive_path, gateway)
        self.decisions_log: List[Dict] = []
    
    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process evolution governance tasks.
        
        Actions:
        - review_all: Review all pending proposals
        - review_one: Review a specific proposal
        - approve: Force approve a proposal (admin)
        - reject: Force reject a proposal (admin)
        - stats: Get governance statistics
        """
        action = "review_all"
        if task and "payload" in task:
            action = task["payload"].get("action", "review_all")
        
        if action == "review_all":
            return self._review_all_proposals()
        elif action == "review_one":
            proposal_id = task["payload"].get("proposal_id")
            return self._review_proposal(proposal_id)
        elif action == "approve":
            proposal_id = task["payload"].get("proposal_id")
            return self._force_approve(proposal_id)
        elif action == "reject":
            proposal_id = task["payload"].get("proposal_id")
            reason = task["payload"].get("reason", "Manual rejection")
            return self._force_reject(proposal_id, reason)
        elif action == "stats":
            return self._get_stats()
        else:
            return {"error": f"Unknown action: {action}"}
    
    def _get_lineage(self) -> Dict[str, Any]:
        """Load lineage data."""
        lineage_path = self.honeycomb_path / "lineage.json"
        if lineage_path.exists():
            with open(lineage_path, 'r') as f:
                return json.load(f)
        return {"bee_types": {}, "proposals": [], "stats": {}}
    
    def _save_lineage(self, lineage: Dict[str, Any]) -> None:
        """Save lineage data."""
        lineage["_meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        lineage_path = self.honeycomb_path / "lineage.json"
        with open(lineage_path, 'w') as f:
            json.dump(lineage, f, indent=2)
    
    def _review_all_proposals(self) -> Dict[str, Any]:
        """Review all pending evolution proposals."""
        lineage = self._get_lineage()
        proposals = lineage.get("proposals", [])
        
        pending = [p for p in proposals if p.get("status") == "pending"]
        
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pending_count": len(pending),
            "reviewed": [],
            "approved": 0,
            "rejected": 0
        }
        
        # Alert if backlog is too large
        if len(pending) > self.MAX_PENDING_PROPOSALS:
            self.post_alert(
                f"⚠️ Evolution backlog: {len(pending)} proposals pending",
                priority=True
            )
        
        for proposal in pending:
            decision = self._evaluate_proposal(proposal)
            
            # Update proposal
            proposal["status"] = decision["status"]
            proposal["reviewed_at"] = datetime.now(timezone.utc).isoformat()
            proposal["reviewed_by"] = self.bee_id
            
            if decision["status"] == "rejected":
                proposal["rejection_reason"] = decision.get("reason")
                results["rejected"] += 1
            elif decision["status"] == "approved":
                # Create new version
                self._create_version(lineage, proposal)
                results["approved"] += 1
            
            results["reviewed"].append({
                "id": proposal["id"],
                "bee_type": proposal["bee_type"],
                "decision": decision["status"],
                "reason": decision.get("reason")
            })
            
            # Log decision
            self.decisions_log.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "proposal_id": proposal["id"],
                "decision": decision
            })
        
        # Save updated lineage
        self._save_lineage(lineage)
        
        return results
    
    def _evaluate_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a single evolution proposal.
        
        Criteria:
        1. Evidence must show meaningful improvement
        2. Changes must be coherent with constraints
        3. Must have sufficient sample size
        """
        evidence = proposal.get("evidence", {})
        changes = proposal.get("changes", [])
        
        # Check evidence completeness
        if not evidence:
            return {
                "status": "rejected",
                "reason": "No evidence provided"
            }
        
        # Check for performance metrics
        metrics = evidence.get("metrics", {})
        if not metrics:
            return {
                "status": "rejected",
                "reason": "No performance metrics in evidence"
            }
        
        # Check sample size
        sample_size = evidence.get("sample_size", 0)
        if sample_size < self.MIN_EVIDENCE_SAMPLES:
            return {
                "status": "rejected",
                "reason": f"Insufficient samples ({sample_size} < {self.MIN_EVIDENCE_SAMPLES})"
            }
        
        # Check improvement
        improvement = evidence.get("improvement_pct", 0)
        if improvement < self.MIN_IMPROVEMENT_THRESHOLD:
            return {
                "status": "rejected",
                "reason": f"Improvement below threshold ({improvement:.1%} < {self.MIN_IMPROVEMENT_THRESHOLD:.0%})"
            }
        
        # Check for dangerous changes
        dangerous_keywords = ["ignore constraints", "skip validation", "bypass gateway"]
        for change in changes:
            for keyword in dangerous_keywords:
                if keyword.lower() in change.lower():
                    return {
                        "status": "rejected",
                        "reason": f"Dangerous change detected: {change}"
                    }
        
        # Coherence check (if gateway available)
        if self.gateway:
            try:
                coherence = self.gateway.check_evolution_coherence(proposal)
                if not coherence.get("coherent", True):
                    return {
                        "status": "rejected",
                        "reason": f"Coherence violation: {coherence.get('reason')}"
                    }
            except AttributeError:
                pass  # Gateway doesn't have this method
        
        # Approved!
        return {
            "status": "approved",
            "reason": f"Approved with {improvement:.1%} improvement over {sample_size} samples"
        }
    
    def _create_version(self, lineage: Dict, proposal: Dict) -> None:
        """Create a new version from an approved proposal."""
        bee_type = proposal["bee_type"]
        
        # Ensure bee type exists
        if bee_type not in lineage["bee_types"]:
            lineage["bee_types"][bee_type] = {
                "current_version": "1.0.0",
                "versions": []
            }
        
        # Create new version entry
        new_version = {
            "version": proposal["proposed_version"],
            "bee_type": bee_type,
            "template_hash": proposal.get("template_hash", ""),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": proposal["proposed_by"],
            "changes": proposal["changes"],
            "performance_metrics": proposal.get("evidence", {}).get("metrics", {}),
            "parent_version": proposal["current_version"]
        }
        
        lineage["bee_types"][bee_type]["versions"].append(new_version)
        lineage["bee_types"][bee_type]["current_version"] = proposal["proposed_version"]
        
        # Update stats
        if "stats" not in lineage:
            lineage["stats"] = {}
        lineage["stats"]["approved_proposals"] = lineage["stats"].get("approved_proposals", 0) + 1
        
        self.log(f"Created version {proposal['proposed_version']} for {bee_type}")
    
    def _review_proposal(self, proposal_id: str) -> Dict[str, Any]:
        """Review a specific proposal by ID."""
        lineage = self._get_lineage()
        proposals = lineage.get("proposals", [])
        
        for proposal in proposals:
            if proposal.get("id") == proposal_id:
                if proposal.get("status") != "pending":
                    return {
                        "error": f"Proposal {proposal_id} is not pending",
                        "status": proposal.get("status")
                    }
                
                decision = self._evaluate_proposal(proposal)
                
                proposal["status"] = decision["status"]
                proposal["reviewed_at"] = datetime.now(timezone.utc).isoformat()
                proposal["reviewed_by"] = self.bee_id
                
                if decision["status"] == "rejected":
                    proposal["rejection_reason"] = decision.get("reason")
                elif decision["status"] == "approved":
                    self._create_version(lineage, proposal)
                
                self._save_lineage(lineage)
                
                return {
                    "proposal_id": proposal_id,
                    "decision": decision
                }
        
        return {"error": f"Proposal {proposal_id} not found"}
    
    def _force_approve(self, proposal_id: str) -> Dict[str, Any]:
        """Force approve a proposal (admin override)."""
        lineage = self._get_lineage()
        proposals = lineage.get("proposals", [])
        
        for proposal in proposals:
            if proposal.get("id") == proposal_id:
                proposal["status"] = "approved"
                proposal["reviewed_at"] = datetime.now(timezone.utc).isoformat()
                proposal["reviewed_by"] = f"{self.bee_id}:ADMIN_OVERRIDE"
                
                self._create_version(lineage, proposal)
                self._save_lineage(lineage)
                
                self.log(f"Admin approved proposal {proposal_id}")
                
                return {
                    "proposal_id": proposal_id,
                    "status": "approved",
                    "note": "Admin override"
                }
        
        return {"error": f"Proposal {proposal_id} not found"}
    
    def _force_reject(self, proposal_id: str, reason: str) -> Dict[str, Any]:
        """Force reject a proposal (admin override)."""
        lineage = self._get_lineage()
        proposals = lineage.get("proposals", [])
        
        for proposal in proposals:
            if proposal.get("id") == proposal_id:
                proposal["status"] = "rejected"
                proposal["reviewed_at"] = datetime.now(timezone.utc).isoformat()
                proposal["reviewed_by"] = f"{self.bee_id}:ADMIN_OVERRIDE"
                proposal["rejection_reason"] = reason
                
                self._save_lineage(lineage)
                
                self.log(f"Admin rejected proposal {proposal_id}: {reason}")
                
                return {
                    "proposal_id": proposal_id,
                    "status": "rejected",
                    "reason": reason,
                    "note": "Admin override"
                }
        
        return {"error": f"Proposal {proposal_id} not found"}
    
    def _get_stats(self) -> Dict[str, Any]:
        """Get governance statistics."""
        lineage = self._get_lineage()
        proposals = lineage.get("proposals", [])
        
        pending = [p for p in proposals if p.get("status") == "pending"]
        approved = [p for p in proposals if p.get("status") == "approved"]
        rejected = [p for p in proposals if p.get("status") == "rejected"]
        
        # Calculate recent decisions
        recent_decisions = self.decisions_log[-20:]
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "totals": {
                "pending": len(pending),
                "approved": len(approved),
                "rejected": len(rejected),
                "total": len(proposals)
            },
            "approval_rate": len(approved) / max(len(proposals), 1),
            "bee_types_managed": len(lineage.get("bee_types", {})),
            "recent_decisions": recent_decisions,
            "governance_health": "healthy" if len(pending) <= self.MAX_PENDING_PROPOSALS else "backlogged"
        }
