"""
Base Bee Agent - The template for all worker bees in the hive.
Updated to support Constitutional Governance.
"""

import json
import uuid
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

class BaseBee(ABC):
    """
    Abstract base class for all bee agents.
    Now equipped with a Constitutional Gateway for ethical checks.
    """

    BEE_TYPE = "base"
    BEE_NAME = "unnamed"
    CATEGORY = "general"

    def __init__(self, hive_path: Optional[str] = None, gateway: Any = None):
        """
        Initialize the bee.

        Args:
            hive_path: Path to the root hive directory.
            gateway: Instance of ConstitutionalGateway for governance checks.
        """
        if hive_path is None:
            # Default to hive directory relative to this file
            hive_path = Path(__file__).parent.parent.parent
        self.hive_path = Path(hive_path)
        # User code said self.honeycomb_path = self.hive_path / "hive" / "honeycomb"
        # BUT based on my exploration, if hive_path is repo root, honeycomb is at hive/honeycomb.
        self.honeycomb_path = self.hive_path / "hive" / "honeycomb"
        self.gateway = gateway
        self.bee_id = f"{self.BEE_TYPE}_{uuid.uuid4().hex[:8]}"
        self.started_at = None
        self.completed_at = None

    def validate_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pass an action through the Constitutional Gateway.
        Returns the evaluated result (APPROVE/BLOCK/MODIFY).
        """
        if not self.gateway:
            # If no gateway provided, assume safe (or log warning)
            return {"status": "APPROVE", "action": action, "reason": "No gateway present"}

        # Inject bee identity into the action for context
        action['bee_type'] = self.BEE_TYPE
        action['bee_id'] = self.bee_id

        return self.gateway.evaluate_action(action)

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
        if "pending" not in tasks:
            tasks["pending"] = []
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

    def read_intel(self) -> Dict[str, Any]:
        """Read the accumulated intelligence."""
        return self._read_json("intel.json")

    def write_intel(self, category: str, key: str, data: Any) -> None:
        """Add or update intel in a category."""
        intel = self.read_intel()
        if category not in intel:
            intel[category] = {}

        if key in intel[category] and isinstance(intel[category][key], dict) and isinstance(data, dict):
            # Merge with existing if both are dicts
            intel[category][key] = self._deep_merge(intel[category][key], data)
        else:
            # Overwrite if not dicts or key doesn't exist
            intel[category][key] = data

        intel["_meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._write_json("intel.json", intel)

    # ─────────────────────────────────────────────────────────────
    # CORE BEE LIFECYCLE
    # ─────────────────────────────────────────────────────────────

    def run(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the bee's work cycle.
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
        """The bee's main work method. Override in subclasses."""
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
        if isinstance(base, dict):
            result = base.copy()
        else:
            result = {}

        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    # ─────────────────────────────────────────────────────────────
    # LEGACY / EXTENDED UTILITY METHODS (Preserved)
    # ─────────────────────────────────────────────────────────────

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
        if "alerts" not in state:
             state["alerts"] = {"priority": [], "normal": []}

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

    def read_treasury(self) -> Dict[str, Any]:
        """Read treasury configuration for wallet addresses."""
        treasury_path = self.hive_path / "hive" / "treasury.json"
        if treasury_path.exists():
            with open(treasury_path, 'r') as f:
                return json.load(f)
        return {}

    def get_wallet_address(self, chain: str = "ETH") -> Optional[str]:
        """Get wallet address for a specific chain."""
        treasury = self.read_treasury()
        wallet = treasury.get("wallets", {}).get(chain, {})
        return wallet.get("address")

    def get_donation_addresses(self) -> Dict[str, str]:
        """Get all wallet addresses configured for donations."""
        treasury = self.read_treasury()
        wallets = treasury.get("wallets", {})
        donation_chains = treasury.get("usage", {}).get("donations", [])
        return {
            chain: wallets[chain]["address"]
            for chain in donation_chains
            if chain in wallets
        }

    def get_credits(self) -> Dict[str, Any]:
        """Get development team credits."""
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
        """Read a JSON file from honeycomb. Enforce path security."""
        try:
            filepath = (self.honeycomb_path / filename).resolve()
            # Security check: Ensure the resolved path is inside the honeycomb path
            if not filepath.is_relative_to(self.honeycomb_path.resolve()):
                self.log(f"Security Alert: Path traversal attempt blocked for {filename}", level="error")
                return {}

            if filepath.exists():
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.log(f"Error reading {filename}: {e}", level="error")
        return {}

    def _write_json(self, filename: str, data: Dict[str, Any]) -> None:
        """Write a JSON file to honeycomb. Enforce path security."""
        try:
            filepath = (self.honeycomb_path / filename).resolve()
            # Security check: Ensure the resolved path is inside the honeycomb path
            if not filepath.is_relative_to(self.honeycomb_path.resolve()):
                self.log(f"Security Alert: Path traversal attempt blocked for {filename}", level="error")
                return

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.log(f"Error writing {filename}: {e}", level="error")

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
