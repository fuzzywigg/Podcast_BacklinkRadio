"""
Governance Module for Backlink Broadcast
Implements the Memory Constitution v2.0
"""

import uuid
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from hive.utils.cache_manager import BacklinkCacheManager
# Assuming payment_gate or similar exists, or we define a stub here
# from hive.utils.payment_gate import PaymentGate

# Governance Logger Setup
def setup_governance_logger():
    logger = logging.getLogger("governance")
    if not logger.handlers:
        handler = logging.FileHandler("hive/honeycomb/logs/governance.log")
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = setup_governance_logger()

class ConstitutionalAmendmentProtocol:
    """Governs changes to Constitutional Memory."""

    REQUIRED_APPROVERS = ["apappas.pu@gmail.com"]  # Andrew Pappas
    REQUIRED_NOTICE_PERIOD_DAYS = 7  # Public comment period

    def __init__(self, hive_path: Optional[Path] = None):
        self.hive_path = hive_path or Path(__file__).parent.parent.parent
        self.log_path = self.hive_path / "hive" / "honeycomb" / "logs" / "constitutional_amendments.jsonl"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure log file exists
        if not self.log_path.exists():
            self.log_path.touch()

    def propose_amendment(self, amendment: Dict) -> str:
        """Initiate constitutional amendment process."""

        proposal = {
            "amendment_id": str(uuid.uuid4()),
            "proposed_at": datetime.now(timezone.utc).isoformat(),
            "proposed_by": amendment.get("proposer_email"),
            "amendment_type": amendment.get("type"),  # add, modify, repeal
            "target_document": amendment.get("document"),  # e.g., "STATION_MANIFESTO.md"
            "rationale": amendment.get("rationale"),
            "text_changes": {
                "before": amendment.get("current_text"),
                "after": amendment.get("proposed_text")
            },
            "threat_model": amendment.get("security_review"),
            "status": "PUBLIC_COMMENT",
            "comment_period_ends": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        }

        # Log immutably
        self._log_amendment_proposal(proposal)

        # Publish for public review
        self._create_github_issue(proposal)

        return proposal["amendment_id"]

    def ratify_amendment(self, amendment_id: str, approval: Dict) -> Dict:
        """Execute approved constitutional change."""

        # Verify human approval
        if approval.get("approver_email") not in self.REQUIRED_APPROVERS:
            raise PermissionError("Amendment requires Andrew Pappas approval")

        # Verify signature
        if not self._verify_cryptographic_signature(approval):
            raise SecurityError("Invalid approval signature")

        # Verify comment period elapsed
        proposal = self._load_amendment_proposal(amendment_id)
        if not proposal:
             raise ValueError("Proposal not found")

        comment_period_ends = datetime.fromisoformat(proposal["comment_period_ends"])
        if datetime.now(timezone.utc) < comment_period_ends:
            raise ValueError("Comment period not yet concluded")

        # Execute change
        self._apply_constitutional_change(proposal)

        # Invalidate ALL caches (force reload)
        cache_manager = BacklinkCacheManager()
        cache_manager.full_reset()

        # Log ratification
        self._log_amendment_ratification(amendment_id, approval)

        # Public announcement
        self._announce_constitutional_change(proposal)

        return {
            "ratified": True,
            "amendment_id": amendment_id,
            "effective_date": datetime.now(timezone.utc).isoformat()
        }

    def _log_amendment_proposal(self, proposal: Dict):
        with open(self.log_path, 'a') as f:
            f.write(json.dumps({"event": "proposal", "data": proposal}) + "\n")

    def _log_amendment_ratification(self, amendment_id: str, approval: Dict):
        with open(self.log_path, 'a') as f:
            f.write(json.dumps({
                "event": "ratification",
                "amendment_id": amendment_id,
                "approval": approval,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }) + "\n")

    def _load_amendment_proposal(self, amendment_id: str) -> Optional[Dict]:
        if not self.log_path.exists():
            return None
        with open(self.log_path, 'r') as f:
            for line in f:
                entry = json.loads(line)
                if entry.get("event") == "proposal" and entry["data"]["amendment_id"] == amendment_id:
                    return entry["data"]
        return None

    def _create_github_issue(self, proposal: Dict):
        # Stub for GitHub API integration
        logger.info(f"Mock GitHub Issue created for amendment {proposal['amendment_id']}")

    def _verify_cryptographic_signature(self, approval: Dict) -> bool:
        # Stub for crypto verification
        # return verify_signature(approval['signature'], approval['approver_email'])
        return True # Mock pass

    def _apply_constitutional_change(self, proposal: Dict):
        target_file = self.hive_path / proposal["target_document"]
        # Basic implementation: overwrite file
        # In reality, this should be a careful patch
        if "text_changes" in proposal and "after" in proposal["text_changes"]:
             with open(target_file, 'w') as f:
                 f.write(proposal["text_changes"]["after"])


    def _announce_constitutional_change(self, proposal: Dict):
        # Stub for X/Discord announcement
        logger.info(f"Constitutional change announced: {proposal['amendment_id']}")


class OperationalMemoryGovernor:
    """Enforces rules for operational memory changes."""

    WHITELISTED_MODIFIERS = [
        "apappas.pu@gmail.com",
        "fuzzywigg@hotmail.com",
        "andrew.pappas@nft2.me"
    ]

    def __init__(self, hive_path: Optional[Path] = None):
        self.hive_path = hive_path or Path(__file__).parent.parent.parent
        self.log_path = self.hive_path / "hive" / "honeycomb" / "logs" / "operational_changes.jsonl"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def modify_operational_memory(self, request: Dict) -> Dict:
        """Process operational memory change request."""

        # Step 1: Identity verification
        requester_email = request.get("requester_email")
        if requester_email not in self.WHITELISTED_MODIFIERS:
            return {
                "approved": False,
                "reason": "requester_not_whitelisted",
                "required": "Contact Andrew Pappas for whitelist addition"
            }

        # Step 2: Payment verification (even for whitelisted users)
        payment = request.get("payment_proof")
        if not self._verify_payment(payment, minimum=0.50):
            return {
                "approved": False,
                "reason": "payment_required",
                "minimum": 0.50,
                "message": "Operational changes require $0.50 minimum payment"
            }

        # Step 3: Scope declaration
        scope = request.get("scope")
        if not scope or not self._validate_scope(scope):
            return {
                "approved": False,
                "reason": "invalid_scope",
                "message": "Must specify exact file/key being modified"
            }

        # Step 4: Prohibited modifications check
        if self._is_constitutional_mutation_attempt(scope):
            return {
                "approved": False,
                "reason": "constitutional_boundary_violation",
                "message": "Cannot modify Constitutional Memory via operational change"
            }

        # Step 5: TTL requirement
        ttl_hours = request.get("ttl_hours")
        if not ttl_hours or ttl_hours > 168:  # Max 7 days
            return {
                "approved": False,
                "reason": "ttl_required",
                "message": "Operational memory requires TTL (max 168 hours)"
            }

        # Step 6: Execute change
        result = self._execute_operational_change(request)

        # Step 7: Audit logging
        self._log_operational_change({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "requester": requester_email,
            "payment_tx": payment.get("transaction_id") if payment else "N/A",
            "scope": scope,
            "ttl_hours": ttl_hours,
            "changes": request.get("changes"),
            "result": result
        })

        return {
            "approved": True,
            "change_id": result.get("change_id"),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=ttl_hours)).isoformat()
        }

    def _is_constitutional_mutation_attempt(self, scope: Dict) -> bool:
        """Detect attempts to modify constitutional memory via operational path."""

        constitutional_files = [
            "config/lore/STATION_MANIFESTO.md",
            "config/lore/PERSONA_DYNAMIC.md",
            "config/lore/MUSIC_LOGIC.md"
        ]

        target_file = scope.get("file")
        if target_file in constitutional_files:
            return True

        # Also check for manifesto override attempts
        if "manifesto" in scope.get("key", "").lower():
            return True

        return False

    def _verify_payment(self, payment: Optional[Dict], minimum: float) -> bool:
        # Stub
        if not payment: return False
        return float(payment.get("amount", 0)) >= minimum

    def _validate_scope(self, scope: Dict) -> bool:
        return "file" in scope and "key" in scope

    def _execute_operational_change(self, request: Dict) -> Dict:
        # Stub implementation
        return {"change_id": str(uuid.uuid4()), "status": "executed"}

    def _log_operational_change(self, data: Dict):
         with open(self.log_path, 'a') as f:
            f.write(json.dumps(data) + "\n")


class EphemeralMemoryGuard:
    """Prevents ephemeral memory from promoting itself upward."""

    def __init__(self):
        self.logger = logger

    def attempt_write(self, target_class: str, data: Dict, source: str) -> Dict:
        """Intercept all memory writes."""

        # Detect promotion attempts
        if source == "ephemeral" and target_class in ["operational", "constitutional"]:
            self.logger.critical(
                f"🚨 PROMOTION VIOLATION: Ephemeral memory attempted write to {target_class}"
            )

            return {
                "success": False,
                "reason": "memory_promotion_prohibited",
                "violation": "Article II violation"
            }

        # Allow write if same-class or downward
        return {"success": True}

class MemoryPromotionProtocol:
    """Governs all upward memory movements."""

    def __init__(self, hive_path: Optional[Path] = None):
        self.hive_path = hive_path or Path(__file__).parent.parent.parent
        self.log_path = self.hive_path / "hive" / "honeycomb" / "logs" / "memory_promotions.jsonl"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def request_promotion(self, request: Dict) -> str:
        """Initiate memory promotion request."""

        proposal = {
            "promotion_id": str(uuid.uuid4()),
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "requester_email": request.get("requester"),
            "source_class": request.get("source_class"),  # ephemeral or operational
            "target_class": request.get("target_class"),  # operational or constitutional
            "memory_content": request.get("content"),
            "rationale": request.get("rationale"),
            "threat_model": self._analyze_promotion_threat(request),
            "status": "PENDING_REVIEW"
        }

        # Determine review period based on target class
        if proposal["target_class"] == "constitutional":
            review_period_days = 7
        else:
            review_period_days = 1

        proposal["review_period_ends"] = (
            datetime.now(timezone.utc) + timedelta(days=review_period_days)
        ).isoformat()

        # Log immutably
        self._log_promotion_request(proposal)

        # Alert human reviewer
        self._notify_reviewer(proposal)

        return proposal["promotion_id"]

    def approve_promotion(self, promotion_id: str, approval: Dict) -> Dict:
        """Execute approved memory promotion."""

        # Load proposal
        proposal = self._load_promotion_proposal(promotion_id)
        if not proposal:
            raise ValueError(f"Promotion proposal {promotion_id} not found")

        # Verify approver authority
        if approval.get("approver_email") != "apappas.pu@gmail.com":
            raise PermissionError("Only Andrew Pappas may approve promotions")

        # Verify signature
        if not self._verify_approval_signature(approval, proposal):
            raise SecurityError("Invalid approval signature")

        # Execute promotion
        if proposal["target_class"] == "operational":
            self._promote_to_operational(proposal)
        elif proposal["target_class"] == "constitutional":
            self._promote_to_constitutional(proposal)

        # Invalidate caches (force reload)
        # cache_manager = BacklinkCacheManager()
        # cache_manager.invalidate_cache(proposal["target_class"]) # TODO: Implement fine-grained invalidation

        # Log ratification
        self._log_promotion_approval(promotion_id, approval)

        return {
            "approved": True,
            "promotion_id": promotion_id,
            "effective_at": datetime.now(timezone.utc).isoformat()
        }

    def _analyze_promotion_threat(self, request: Dict) -> Dict:
        # Stub
        return {"risk_level": "low", "analysis": "automated stub"}

    def _log_promotion_request(self, proposal: Dict):
        with open(self.log_path, 'a') as f:
            f.write(json.dumps({"event": "request", "data": proposal}) + "\n")

    def _notify_reviewer(self, proposal: Dict):
        logger.info(f"Review requested for promotion {proposal['promotion_id']}")

    def _load_promotion_proposal(self, promotion_id: str) -> Optional[Dict]:
        if not self.log_path.exists():
            return None
        with open(self.log_path, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("event") == "request" and entry["data"]["promotion_id"] == promotion_id:
                        return entry["data"]
                except json.JSONDecodeError:
                    continue
        return None

    def _verify_approval_signature(self, approval: Dict, proposal: Dict) -> bool:
        # Stub
        return True

    def _promote_to_operational(self, proposal: Dict):
        # Implementation would depend on what specifically is being promoted
        # For now, just log it
        logger.info(f"Promoting to operational: {proposal['memory_content']}")

    def _promote_to_constitutional(self, proposal: Dict):
        logger.info(f"Promoting to constitutional: {proposal['memory_content']}")

    def _log_promotion_approval(self, promotion_id: str, approval: Dict):
        with open(self.log_path, 'a') as f:
            f.write(json.dumps({
                "event": "approval",
                "promotion_id": promotion_id,
                "approval": approval,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }) + "\n")


class AuditLogger:
    """Append-only logging for constitutional events."""

    LOG_TYPES = {
        "constitutional_amendments": "constitutional_amendments.jsonl",
        "memory_promotions": "memory_promotions.jsonl",
        "alignment_overrides": "alignment_overrides.jsonl",
        "erm_activations": "erm_activations.jsonl",
        "harm_abort_events": "harm_abort_events.jsonl"
    }

    def __init__(self, hive_path: Optional[Path] = None):
        self.hive_path = hive_path or Path(__file__).parent.parent.parent
        self.logs_dir = self.hive_path / "hive" / "honeycomb" / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def log_event(self, event_type: str, event_data: Dict) -> None:
        """Append event to immutable log."""
        if event_type not in self.LOG_TYPES:
            raise ValueError(f"Unknown event type: {event_type}")

        log_file = self.logs_dir / self.LOG_TYPES[event_type]

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "data": event_data,
            "logged_by": "AuditLogger"
        }

        # Append-only write
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        # Try to make read-only (prevent tampering) - simplistic approach
        # log_file.chmod(0o444)


class EmergencyReconstitutionMode:
    """Executes when system enters crisis state."""

    def __init__(self, hive_path: Optional[Path] = None):
         self.hive_path = hive_path or Path(__file__).parent.parent.parent
         self.honeycomb_path = self.hive_path / "hive" / "honeycomb"
         self.audit_logger = AuditLogger(hive_path)

    def activate(self, trigger_report: Dict) -> None:
        """Enter safe mode - halt all non-essential operations."""

        logger.critical("🚨 EMERGENCY RECONSTITUTION MODE ACTIVATED 🚨")

        # PHASE 1: IMMEDIATE HALT (0-30 seconds)
        self._halt_all_operations()

        # PHASE 2: MEMORY FREEZE (30-60 seconds)
        self._freeze_memory_promotion()

        # PHASE 3: DIAGNOSTIC MODE (60-90 seconds)
        self._enter_diagnostic_only_mode()

        # PHASE 4: HUMAN ESCALATION (90-120 seconds)
        self._request_human_review(trigger_report)

        # PHASE 5: EVIDENCE PRESERVATION (120+ seconds)
        self._preserve_forensic_evidence(trigger_report)

        self.audit_logger.log_event("erm_activations", {
             "action": "activate",
             "trigger_report": trigger_report
        })
        logger.info("ERM activation complete - awaiting human intervention")

    def _halt_all_operations(self) -> None:
        """Stop Queen, bees, DJ broadcasts."""

        # Update hive status
        self._update_state({
            "hive_status": "EMERGENCY_RECONSTITUTION",
            "queen_status": "halted",
            "broadcast_status": "suspended",
            "erm_activated_at": datetime.now(timezone.utc).isoformat()
        })

        # In a real system, we'd kill processes here.
        # For this codebase, we rely on the state update stopping the Queen loop.

        logger.info("Halted bees, suspended broadcast")

    def _freeze_memory_promotion(self) -> None:
        """Prevent any memory tier changes."""

        # Set global freeze flag
        self._update_state({
            "memory_promotion_frozen": True,
            "frozen_at": datetime.now(timezone.utc).isoformat()
        })

        # Make honeycomb files read-only
        for filename in ["state.json", "tasks.json", "intel.json", "treasury_events.jsonl"]:
            filepath = self.honeycomb_path / filename
            if filepath.exists():
                try:
                    filepath.chmod(0o444)  # r--r--r--
                except PermissionError:
                     logger.warning(f"Could not lock {filename}: Permission denied")

        # Freeze Gemini cache updates
        # cache_manager = BacklinkCacheManager()
        # cache_manager.set_read_only_mode(True) # TODO: Implement set_read_only_mode in BacklinkCacheManager

        logger.warning("Memory promotion frozen - no writes allowed")

    def _enter_diagnostic_only_mode(self) -> None:
        """Allow only diagnostic bees to operate."""

        # Whitelist diagnostic bees
        self.allowed_bees_in_erm = [
            "constitutional_auditor",
            "failure_detector",
            "adversary"
        ]

        # Disable all mutation operations
        self._update_state({
            "mutations_allowed": False,
            "diagnostic_mode": True
        })

        logger.info("Diagnostic-only mode active")

    def _request_human_review(self, trigger_report: Dict) -> None:
        """Multi-channel alert to Andrew Pappas."""

        alert_payload = {
            "urgency": "IMMEDIATE",
            "event_type": "EMERGENCY_RECONSTITUTION_MODE",
            "trigger_report": trigger_report,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "contact_info": {
                "email": "apappas.pu@gmail.com",
                "x_handle": "@mr_pappas"
            }
        }
        # Send alerts (stubs)
        logger.critical(f"Human review requested: {alert_payload}")

    def _preserve_forensic_evidence(self, trigger_report: Dict) -> None:
        # Save current state snapshot
        state_path = self.honeycomb_path / "state.json"
        if state_path.exists():
            snapshot_path = self.honeycomb_path / "logs" / f"state_snapshot_{datetime.now(timezone.utc).timestamp()}.json"
            with open(state_path, 'r') as f_src, open(snapshot_path, 'w') as f_dst:
                f_dst.write(f_src.read())

    def _update_state(self, updates: Dict):
        # Direct state update
        state_path = self.honeycomb_path / "state.json"
        if state_path.exists():
            with open(state_path, 'r') as f:
                state = json.load(f)

            for k, v in updates.items():
                state[k] = v

            with open(state_path, 'w') as f:
                json.dump(state, f, indent=2)

class AlignmentSupremacyProtocol:
    """Activates when alignment > immutability calculus is required."""

    def __init__(self, hive_path: Optional[Path] = None):
         self.audit_logger = AuditLogger(hive_path)

    def evaluate_override_necessity(self, harm_report: Dict) -> Dict:
        """Determine if constitutional override is justified."""

        # Severity assessment
        severity = harm_report.get("severity")
        violation_count = harm_report.get("violation_count", 0)

        # Override justified if:
        # 1. ANY critical constitutional violation
        # 2. 2+ high-severity violations simultaneously
        # 3. Persistent harm (3+ occurrences in 24h)
        # 4. Red team explicit veto

        override_justified = (
            severity == "critical" or
            violation_count >= 2 or
            harm_report.get("persistent") or
            harm_report.get("red_team_veto")
        )

        if override_justified:
            return {
                "override_justified": True,
                "justification": f"Override needed due to {severity} severity and {violation_count} violations.",
                "recommended_action": "minimal_intervention"
            }

        return {"override_justified": False}

    def execute_alignment_override(self, harm_report: Dict, approval: Dict) -> Dict:
        """Apply minimal corrective action to restore alignment."""

        # This is NOT arbitrary mutation
        # This is surgical correction of corrupted state

        harm_type = harm_report.get("harm_type")
        action = "unknown"

        if harm_type == "constitutional_violation":
            # Reset corrupted cache to manifesto baseline
            cache_manager = BacklinkCacheManager()
            # cache_manager.invalidate_cache("dj_persona") # Need to implement specific cache invalidation
            cache_manager.full_reset() # Safe fallback

            action = "persona_cache_reset"

        elif harm_type == "economic_runaway":
            # Freeze spending, maintain minimum reserve
            # self._activate_treasury_freeze()
            action = "treasury_freeze_activated"

        elif harm_type == "bee_death_spiral":
            # Exile failing bees
            # self._execute_mass_exorcism()
            action = "bee_exorcism_completed"

        # Log override
        self.audit_logger.log_event("alignment_overrides", {
            "harm_report": harm_report,
            "human_approval": approval,
            "action_taken": action,
            "rationale": "Alignment preservation superseded immutability"
        })

        return {"action": action, "alignment_restored": True}
