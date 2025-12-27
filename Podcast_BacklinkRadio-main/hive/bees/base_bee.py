"""
Base Bee Agent - The template for all worker bees in the hive.

All bees inherit from this class and implement their specific work() method.
Bees communicate through the honeycomb (shared state files), not directly.

Updated to support:
- Constitutional Governance via safe_action()
- Model-First Reasoning (MFR) workflow
- Pollen memory for successful patterns
- Lineage tracking for bee evolution
"""

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid


class BaseBee(ABC):
    """
    Abstract base class for all bee agents.

    Bees follow the stigmergy pattern:
    - Read from honeycomb (shared state)
    - Do their work
    - Write results back to honeycomb
    - No direct bee-to-bee communication

    Constitutional Governance:
    - All external actions should pass through safe_action()
    - Gateway validates against 5 Constitutional Principles
    - Actions may be APPROVED, MODIFIED, or BLOCKED
    """

    # Override in subclasses
    BEE_TYPE = "base"
    BEE_NAME = "unnamed"
    CATEGORY = "general"  # content, technical, marketing, monetization, community, research, admin
    LINEAGE_VERSION = "1.0.0"  # Bee template version for evolution tracking

    def __init__(self, hive_path: Optional[str] = None, gateway: Any = None):
        """
        Initialize the bee with path to hive.

        Args:
            hive_path: Path to the hive directory. Defaults to parent of bees/.
            gateway: Optional ConstitutionalGateway instance for governance checks.
        """
        if hive_path is None:
            # Default to hive directory relative to this file
            hive_path = Path(__file__).parent.parent
        self.hive_path = Path(hive_path)
        self.honeycomb_path = self.hive_path / "honeycomb"
        self.bee_id = f"{self.BEE_TYPE}_{uuid.uuid4().hex[:8]}"
        self.started_at = None
        self.completed_at = None
        self.gateway = gateway  # Constitutional Gateway for governance
        
        # Model-First Reasoning components
        self._pollen_store = None
        self._lineage_tracker = None
        self._current_model = None  # Explicit problem model for MFR

    # ─────────────────────────────────────────────────────────────
    # HONEYCOMB ACCESS (Read/Write to shared state)
    # ─────────────────────────────────────────────────────────────

    def read_state(self) -> Dict[str, Any]:
        """Read the current broadcast state."""
        return self._read_json("state.json")

    def write_state(self, updates: Dict[str, Any]) -> None:
        """Update the broadcast state (merges with existing)."""
        state = self.read_state()
        state = self._deep_merge(state, updates)
        state["_meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        state["_meta"]["last_updated_by"] = self.bee_id
        self._write_json("state.json", state)

    def read_tasks(self) -> Dict[str, Any]:
        """Read the task queue."""
        return self._read_json("tasks.json")

    def write_task(self, task: Dict[str, Any]) -> str:
        """Add a new task to the queue. Returns task ID."""
        tasks = self.read_tasks()
        task_id = task.get("id", str(uuid.uuid4()))
        task["id"] = task_id
        task["created_at"] = datetime.now(timezone.utc).isoformat()
        task["created_by"] = self.bee_id
        task["status"] = "pending"
        task["attempts"] = 0
        task["max_attempts"] = task.get("max_attempts", 3)
        tasks["pending"].append(task)
        self._write_json("tasks.json", tasks)
        return task_id

    def claim_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Claim a task from pending queue. Returns task or None."""
        tasks = self.read_tasks()
        for i, task in enumerate(tasks["pending"]):
            if task["id"] == task_id:
                task = tasks["pending"].pop(i)
                task["status"] = "in_progress"
                task["claimed_by"] = self.bee_id
                task["claimed_at"] = datetime.now(timezone.utc).isoformat()
                task["attempts"] += 1
                tasks["in_progress"].append(task)
                self._write_json("tasks.json", tasks)
                return task
        return None

    def complete_task(self, task_id: str, result: Any = None) -> None:
        """Mark a task as completed."""
        tasks = self.read_tasks()
        for i, task in enumerate(tasks["in_progress"]):
            if task["id"] == task_id:
                task = tasks["in_progress"].pop(i)
                task["status"] = "completed"
                task["completed_at"] = datetime.now(timezone.utc).isoformat()
                task["result"] = result
                tasks["completed"].append(task)
                self._write_json("tasks.json", tasks)
                return

    def fail_task(self, task_id: str, error: str) -> None:
        """Mark a task as failed (may retry if attempts < max)."""
        tasks = self.read_tasks()
        for i, task in enumerate(tasks["in_progress"]):
            if task["id"] == task_id:
                task = tasks["in_progress"].pop(i)
                task["last_error"] = error
                task["failed_at"] = datetime.now(timezone.utc).isoformat()

                if task["attempts"] < task["max_attempts"]:
                    # Retry - put back in pending
                    task["status"] = "pending"
                    tasks["pending"].append(task)
                else:
                    # Max attempts reached
                    task["status"] = "failed"
                    tasks["failed"].append(task)

                self._write_json("tasks.json", tasks)
                return

    def read_intel(self) -> Dict[str, Any]:
        """Read the accumulated intelligence."""
        return self._read_json("intel.json")

    def write_intel(self, category: str, key: str, data: Dict[str, Any]) -> None:
        """Add or update intel in a category."""
        intel = self.read_intel()
        if category not in intel:
            intel[category] = {}

        if key in intel[category]:
            # Merge with existing
            intel[category][key] = self._deep_merge(intel[category][key], data)
        else:
            intel[category][key] = data

        intel["_meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._write_json("intel.json", intel)

    def add_listener_intel(self, node_id: str, intel_data: Dict[str, Any]) -> None:
        """Convenience method to add listener intel."""
        existing = self.read_intel().get("listeners", {}).get("known_nodes", {}).get(node_id, {})

        # Ensure notes are appended, not replaced
        if "notes" in intel_data and "notes" in existing:
            intel_data["notes"] = existing["notes"] + intel_data["notes"]

        # Ensure numeric fields like 'dao_credits' are accumulated, not overwritten
        for field in ["dao_credits", "donation_total", "interaction_count"]:
            if field in intel_data and field in existing:
                intel_data[field] = existing[field] + intel_data[field]

        intel_data["last_seen"] = datetime.now(timezone.utc).isoformat()
        if "first_seen" not in existing:
            intel_data["first_seen"] = intel_data["last_seen"]

        self.write_intel("listeners", f"known_nodes.{node_id}", intel_data)

    def post_alert(self, message: str, priority: bool = False) -> None:
        """Post an alert to the state for the DJ to pick up."""
        state = self.read_state()
        alert = {
            "id": str(uuid.uuid4()),
            "message": message,
            "from": self.bee_id,
            "at": datetime.now(timezone.utc).isoformat()
        }
        if priority:
            state["alerts"]["priority"].append(alert)
        else:
            state["alerts"]["normal"].append(alert)
        self.write_state({"alerts": state["alerts"]})

    # ─────────────────────────────────────────────────────────────
    # CONSTITUTIONAL GOVERNANCE (safe_action for ethical checks)
    # ─────────────────────────────────────────────────────────────

    def safe_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pass action through Constitutional Gateway for validation.

        All external-facing actions (payments, posts, broadcasts) should
        use this method to ensure Constitutional compliance.

        The gateway checks against 5 principles:
        1. Artist-First (fair compensation)
        2. Transparency (disclosure requirements)
        3. Privacy-Respecting (consent for data)
        4. Ad-Free Integrity (sponsor limits)
        5. Community-First (listener priorities)

        Args:
            action: Dict with 'type' and relevant payload fields.

        Returns:
            The approved action (possibly modified for compliance).

        Raises:
            ValueError: If action is BLOCKED by Constitutional Gateway.
        """
        if self.gateway is None:
            # No gateway configured - pass through (log warning)
            self.log("WARNING: No Constitutional Gateway configured - action not validated")
            return action

        # Evaluate action through gateway
        decision = self.gateway.evaluate_action(action)

        # Log the decision
        self.log(f"Constitutional check: {decision.get('status')} - {decision.get('reason', 'OK')}")

        if decision['status'] == 'BLOCK':
            # Action violates Constitutional principles
            error_msg = f"Constitutional Violation (BLOCKED): {decision.get('reason')}"
            self.log(error_msg, level="error")
            raise ValueError(error_msg)

        if decision['status'] == 'MODIFY':
            # Action was modified for compliance
            self.log(f"Action modified for compliance: {decision.get('reason')}")

        # Return the approved (possibly modified) action
        return decision.get('action', action)

    # ─────────────────────────────────────────────────────────────
    # MODEL-FIRST REASONING (MFR) - Define before acting
    # ─────────────────────────────────────────────────────────────

    def _get_pollen_store(self):
        """Lazy-load pollen store."""
        if self._pollen_store is None:
            try:
                from hive.memory.pollen_store import PollenStore
                self._pollen_store = PollenStore(self.hive_path)
            except ImportError:
                self.log("WARNING: PollenStore not available", level="warning")
        return self._pollen_store

    def _get_lineage_tracker(self):
        """Lazy-load lineage tracker."""
        if self._lineage_tracker is None:
            try:
                from hive.memory.lineage_tracker import LineageTracker
                self._lineage_tracker = LineageTracker(self.hive_path)
            except ImportError:
                self.log("WARNING: LineageTracker not available", level="warning")
        return self._lineage_tracker

    def define_model(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        MFR Phase 1: Define explicit problem model BEFORE reasoning.
        
        This is the core of Model-First Reasoning - forces the bee to
        explicitly define:
        - What entities are involved
        - What state variables exist
        - What actions are possible
        - What constraints apply
        - What pollen (prior patterns) are relevant
        
        Subclasses should override _identify_* methods to customize.
        
        Args:
            task: The task to build a model for (can be None for general work)
            
        Returns:
            Explicit problem model dict
        """
        # Handle None task
        if task is None:
            task = {}
        
        model = {
            "task_type": task.get("type", "unknown"),
            "entities": self._identify_entities(task),
            "state_variables": self._identify_state_variables(task),
            "possible_actions": self._get_possible_actions(task),
            "constraints": self._get_constraints(task),
            "pollen_sources": self._recall_pollen(task),
            "defined_at": datetime.now(timezone.utc).isoformat(),
            "defined_by": self.bee_id
        }
        self._current_model = model
        return model

    def _identify_entities(self, task: Dict[str, Any]) -> List[str]:
        """Identify entities involved in task. Override in subclasses."""
        entities = [self.BEE_TYPE]
        if "payload" in task:
            payload = task["payload"]
            if "user_id" in payload:
                entities.append(f"user:{payload['user_id']}")
            if "content_id" in payload:
                entities.append(f"content:{payload['content_id']}")
        return entities

    def _identify_state_variables(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Identify relevant state variables. Override in subclasses."""
        state = self.read_state()
        return {
            "broadcast_status": state.get("broadcast", {}).get("status"),
            "pending_alerts": len(state.get("alerts", {}).get("priority", [])),
            "listener_count": state.get("broadcast", {}).get("listener_count", 0)
        }

    def _get_possible_actions(self, task: Dict[str, Any]) -> List[str]:
        """Get list of possible actions for this task. Override in subclasses."""
        return ["process", "skip", "defer", "escalate"]

    def _get_constraints(self, task: Dict[str, Any]) -> List[str]:
        """Get constraints that apply. Override in subclasses."""
        constraints = [
            "Must pass Constitutional Gateway check",
            "Cannot route funds to non-treasury wallets",
            "Must sanitize public inputs"
        ]
        return constraints

    def _recall_pollen(self, task: Dict[str, Any]) -> List[Dict]:
        """Recall relevant pollen (prior successful patterns)."""
        pollen_store = self._get_pollen_store()
        if pollen_store is None:
            return []
        
        return pollen_store.get_pollen_sources(task)

    def coherence_check(self, model: Dict[str, Any]) -> bool:
        """
        MFR Phase 2: Validate model against hive coherence.
        
        Checks that the defined model doesn't violate:
        - Constitutional principles
        - Hive constraints
        - Known hazards
        
        Args:
            model: The explicit problem model
            
        Returns:
            True if model passes coherence check
        """
        # Check against Constitutional Gateway if available
        if self.gateway:
            try:
                decision = self.gateway.evaluate_model(model)
                if decision.get('status') == 'BLOCK':
                    self.log(f"Model failed coherence: {decision.get('reason')}", level="warning")
                    return False
            except AttributeError:
                # Gateway doesn't have evaluate_model - skip
                pass
        
        # Basic coherence checks
        if not model.get("entities"):
            self.log("Model missing entities", level="warning")
            return False
        
        if not model.get("possible_actions"):
            self.log("Model has no possible actions", level="warning")
            return False
        
        return True

    def execute_within_model(
        self, 
        model: Dict[str, Any], 
        task: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        MFR Phase 3: Execute ONLY within the defined model.
        
        Subclasses can override this for custom model-aware execution.
        Default implementation delegates to work() method.
        
        Args:
            model: The validated problem model
            task: The original task (can be None)
            
        Returns:
            Execution result dict
        """
        # Default: delegate to work() method
        # Subclasses can override for model-aware execution
        return self.work(task)

    def store_pollen(
        self, 
        model: Dict[str, Any], 
        result: Dict[str, Any],
        success_score: float = 0.8
    ) -> Optional[str]:
        """
        MFR Phase 4: Store successful pattern as pollen.
        
        Called after successful execution to persist the pattern
        for future bee generations.
        
        Args:
            model: The model that was used
            result: The successful result
            success_score: How successful (0.0 to 1.0)
            
        Returns:
            Pollen entry ID if stored, None otherwise
        """
        pollen_store = self._get_pollen_store()
        if pollen_store is None:
            return None
        
        try:
            pollen_id = pollen_store.store(
                bee_type=self.__class__.__name__,
                task_type=model.get("task_type", "unknown"),
                model=model,
                result_summary={
                    "success": result.get("success"),
                    "summary": result.get("summary", str(result)[:200])
                },
                success_score=success_score,
                lineage_version=self.LINEAGE_VERSION
            )
            if pollen_id:
                self.log(f"Stored pollen: {pollen_id}")
            return pollen_id
        except Exception as e:
            self.log(f"Failed to store pollen: {e}", level="warning")
            return None

    def propose_evolution(
        self,
        changes: List[str],
        evidence: Dict[str, Any]
    ) -> Optional[str]:
        """
        Propose an evolution update for this bee type.
        
        Called when a bee clone discovers an improvement that
        should be propagated to the canonical bee template.
        
        Args:
            changes: List of changes made
            evidence: Performance evidence supporting the update
            
        Returns:
            Proposal ID if submitted, None otherwise
        """
        tracker = self._get_lineage_tracker()
        if tracker is None:
            return None
        
        try:
            proposal_id = tracker.propose_update(
                bee_type=self.__class__.__name__,
                changes=changes,
                evidence=evidence,
                proposed_by=self.bee_id
            )
            self.log(f"Evolution proposal submitted: {proposal_id}")
            return proposal_id
        except Exception as e:
            self.log(f"Failed to propose evolution: {e}", level="warning")
            return None

    # ─────────────────────────────────────────────────────────────
    # TREASURY ACCESS (Web3 wallet addresses for operations)
    # ─────────────────────────────────────────────────────────────

    def read_treasury(self) -> Dict[str, Any]:
        """
        Read treasury configuration for wallet addresses.

        Used for:
        - Receiving donations/tips
        - Compute support funding
        - On-chain obligations
        - Real-world payment obligations

        Returns wallet addresses for ETH, BTC, SOL, and other chains.
        """
        treasury_path = self.hive_path / "treasury.json"
        if treasury_path.exists():
            with open(treasury_path, 'r') as f:
                return json.load(f)
        return {}

    def get_wallet_address(self, chain: str = "ETH") -> Optional[str]:
        """
        Get wallet address for a specific chain.

        Args:
            chain: Chain identifier (ETH, BTC, SOL, Linea, SHIB, PEPE, BASED)

        Returns:
            Wallet address string or None if not configured.
        """
        treasury = self.read_treasury()
        wallet = treasury.get("wallets", {}).get(chain, {})
        return wallet.get("address")

    def get_donation_addresses(self) -> Dict[str, str]:
        """
        Get all wallet addresses configured for donations.

        Returns:
            Dict mapping chain names to addresses.
        """
        treasury = self.read_treasury()
        wallets = treasury.get("wallets", {})
        donation_chains = treasury.get("usage", {}).get("donations", [])

        return {
            chain: wallets[chain]["address"]
            for chain in donation_chains
            if chain in wallets
        }

    def get_credits(self) -> Dict[str, Any]:
        """
        Get development team credits.

        Credit belongs to:
        - SMTP.eth Team
        - nft2.me
        - fuzzywigg.ai Development Team
        """
        treasury = self.read_treasury()
        return treasury.get("credits", {})

    # ─────────────────────────────────────────────────────────────
    # CORE BEE LIFECYCLE
    # ─────────────────────────────────────────────────────────────

    def run(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the bee's work cycle.

        Args:
            task: Optional specific task to work on. If None, bee may
                  look for tasks or do general work.

        Returns:
            Dict with 'success', 'result', and optional 'error' keys.
        """
        self.started_at = datetime.now(timezone.utc)
        self.log(f"Starting work cycle")

        try:
            result = self.work(task)
            self.completed_at = datetime.now(timezone.utc)
            duration = (self.completed_at - self.started_at).total_seconds()
            self.log(f"Completed in {duration:.2f}s")

            return {
                "success": True,
                "result": result,
                "bee_id": self.bee_id,
                "duration_seconds": duration
            }

        except Exception as e:
            self.completed_at = datetime.now(timezone.utc)
            self.log(f"Failed with error: {str(e)}", level="error")

            return {
                "success": False,
                "error": str(e),
                "bee_id": self.bee_id
            }

    @abstractmethod
    def work(self, task: Optional[Dict[str, Any]] = None) -> Any:
        """
        The bee's main work method. Override in subclasses.

        Args:
            task: Optional task payload to work on.

        Returns:
            Result of the work (format depends on bee type).
        """
        pass

    # ─────────────────────────────────────────────────────────────
    # UTILITY METHODS
    # ─────────────────────────────────────────────────────────────

    def log(self, message: str, level: str = "info") -> None:
        """Log a message (for debugging/monitoring)."""
        timestamp = datetime.now(timezone.utc).isoformat()
        print(f"[{timestamp}] [{level.upper()}] [{self.bee_id}] {message}")

    def _read_json(self, filename: str) -> Dict[str, Any]:
        """Read a JSON file from honeycomb."""
        filepath = self.honeycomb_path / filename
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
        return {}

    def _write_json(self, filename: str, data: Dict[str, Any]) -> None:
        """Write a JSON file to honeycomb."""
        filepath = self.honeycomb_path / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def _deep_merge(self, base: Dict, updates: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result


class ScoutBee(BaseBee):
    """
    Scout bees explore and discover.

    They find new things: music, trends, listeners, opportunities.
    They don't refine or evaluate - they just bring back discoveries.
    """
    BEE_TYPE = "scout"
    CATEGORY = "research"


class EmployedBee(BaseBee):
    """
    Employed bees work on known resources.

    They refine, process, and improve what scouts have found.
    They do the actual production work.
    """
    BEE_TYPE = "employed"
    CATEGORY = "content"


class OnlookerBee(BaseBee):
    """
    Onlooker bees evaluate and select.

    They look at what employed bees have produced and pick winners.
    They make decisions about quality and priority.
    """
    BEE_TYPE = "onlooker"
    CATEGORY = "research"
