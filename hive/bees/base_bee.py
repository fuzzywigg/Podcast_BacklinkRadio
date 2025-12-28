"""
Base Bee Agent - The template for all worker bees in the hive.

All bees inherit from this class and implement their specific work() method.
Bees communicate through the honeycomb (shared state files), not directly.
Updated to support Constitutional Governance.
"""

import json
import logging
import uuid
import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime, timezone

from hive.utils.state_manager import StateManager
from hive.utils.storage_adapter import StorageAdapter
from hive.utils.prompt_engineer import PromptEngineer


class BaseBee(ABC):
    """
    Abstract base class for all bee agents.
    Now equipped with a Constitutional Gateway for ethical checks.

    Bees follow the stigmergy pattern:
    - Read from honeycomb (shared state)
    - Do their work
    - Write results back to honeycomb
    - No direct bee-to-bee communication
    """

    BEE_TYPE = "base"
    BEE_NAME = "Base Bee"
    CATEGORY = "general"

    def __init__(self, hive_path: Optional[str] = None, gateway: Any = None):
        """
        Initialize the bee with path to hive.
        Initialize the bee.

        Args:
            hive_path: Path to the root hive directory.
            gateway: Instance of ConstitutionalGateway for governance checks.
        """
        if hive_path is None:
            # Default to hive directory relative to this file
            hive_path = Path(__file__).parent.parent.parent
        from hive.utils.wisdom_manager import WisdomManager

        self.hive_path = Path(hive_path)
        self.honeycomb_path = self.hive_path / "hive" / "honeycomb"
        self.gateway = gateway

        # Generate Unique Bee ID
        self.bee_id = f"{self.BEE_TYPE}_{str(uuid.uuid4())[:8]}"

        # Initialize State Manager
        self.state_manager = StateManager(self.hive_path)
        
        # Initialize Storage Adapter
        self.storage = StorageAdapter(self.honeycomb_path)

        # Initialize Wisdom Manager (System 3)
        self.wisdom_manager = WisdomManager(self.hive_path)

        # Logging setup
        self.logger = logging.getLogger(self.BEE_NAME)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(f'[%(asctime)s] [{self.BEE_TYPE.upper()}] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    @abstractmethod
    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform the bee's primary function.
        Must be implemented by subclasses.
        """
        pass

    def run(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main entry point. Wraps work() with validation and error handling.
        """
        start_time = time.time()
        self.log(f"Starting work... Task: {task.get('id') if task else 'None'}")

        try:
            # 1. Validate (if Gateway exists)
            if self.gateway:
                action_context = {
                    "bee": self.BEE_TYPE,
                    "task": task
                }
                is_valid, reason = self.gateway.validate_action(action_context)
                if not is_valid:
                    self.log(f"Action BLOCKED by Gateway: {reason}", level="error")
                    return {
                        "success": False,
                        "error": "constitutional_block",
                        "reason": reason,
                        "bee_id": self.bee_id,
                        "duration_seconds": time.time() - start_time
                    }

            # 2. Execute
            work_result = self.work(task)

            # 3. Log Success
            self.log("Work complete.")
            return {
                "success": True,
                "result": work_result,
                "bee_id": self.bee_id,
                "duration_seconds": time.time() - start_time
            }

        except Exception as e:
            self.log(f"CRITICAL FAILURE: {e}", level="error")
            return {
                "success": False,
                "error": str(e),
                "bee_id": self.bee_id,
                "duration_seconds": time.time() - start_time
            }

    # ─────────────────────────────────────────────────────────────
    # STATE / HONEYCOMB INTERFACE (Updated)
    # ─────────────────────────────────────────────────────────────

    def _read_json(self, filename: str) -> Dict[str, Any]:
        """Read a JSON file from honeycomb."""
        # Check for path traversal
        safe_path = (self.honeycomb_path / filename).resolve()
        # In testing with mock paths, resolve() might behave differently if files don't exist?
        # But we create them in fixtures.
        # Assuming simple check for now.

        if filename == "state.json":
            return self.state_manager.read_state()

        if not safe_path.exists():
            return {}
        try:
            with open(safe_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def _write_json(self, filename: str, data: Dict[str, Any]) -> None:
        """Write a JSON file to honeycomb."""
        safe_path = (self.honeycomb_path / filename).resolve()

        if filename == "state.json":
            self.state_manager.write_state(data, self.BEE_TYPE)
            return

        try:
            # Atomic write for other files
            temp_path = safe_path.with_suffix(".tmp")
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)
            temp_path.replace(safe_path)
        except Exception as e:
            self.log(f"Error writing {filename}: {e}", level="error")

    # ─────────────────────────────────────────────────────────────
    # CONVENIENCE METHODS (Restored for Backwards Compat)
    # ─────────────────────────────────────────────────────────────

    def read_state(self) -> Dict[str, Any]:
        """Read state.json."""
        return self._read_json("state.json")

    def read_tasks(self) -> Dict[str, Any]:
        """Read tasks.json."""
        return self._read_json("tasks.json")

    def write_task(self, task: Dict[str, Any]) -> str:
        """Add a new task to pending queue."""
        tasks = self.read_tasks()
        if "pending" not in tasks:
            tasks["pending"] = []

        task_id = str(uuid.uuid4())
        task["id"] = task_id
        task["status"] = "pending"
        task["created_at"] = datetime.now(timezone.utc).isoformat()

        tasks["pending"].append(task)
        self._write_json("tasks.json", tasks)
        return task_id

    def claim_task(self, task_id_or_type: str) -> Optional[Dict[str, Any]]:
        """Claim a task from the pending queue."""
        tasks = self.read_tasks()
        pending = tasks.get("pending", [])

        found_index = -1
        found_task = None

        for i, task in enumerate(pending):
            if task.get("id") == task_id_or_type or task.get("type") == task_id_or_type:
                found_index = i
                found_task = task
                break

        if found_task:
            tasks["pending"].pop(found_index)
            found_task["status"] = "in_progress"
            found_task["started_at"] = datetime.now(timezone.utc).isoformat()
            found_task["worker_bee_id"] = self.bee_id

            if "in_progress" not in tasks:
                tasks["in_progress"] = []
            tasks["in_progress"].append(found_task)

            self._write_json("tasks.json", tasks)
            return found_task

        return None

    def complete_task(self, task_id: str, result: Dict[str, Any]) -> None:
        """Mark a task as completed."""
        tasks = self.read_tasks()
        in_progress = tasks.get("in_progress", [])

        found_index = -1
        found_task = None

        for i, task in enumerate(in_progress):
            if task.get("id") == task_id:
                found_index = i
                found_task = task
                break

        if found_task:
            tasks["in_progress"].pop(found_index)
            found_task["status"] = "completed"
            found_task["completed_at"] = datetime.now(timezone.utc).isoformat()
            found_task["result"] = result

            if "completed" not in tasks:
                tasks["completed"] = []
            tasks["completed"].append(found_task)

    def _validate_path(self, filename: str) -> Path:
        """
        Validate that the filename results in a path inside honeycomb.
        Prevents path traversal attacks.
        """
        # Resolve the honeycomb path to absolute path
        honeycomb = self.honeycomb_path.resolve()

        # Join and resolve the target path
        target = (self.honeycomb_path / filename).resolve()

        # Check if target is relative to honeycomb
        # is_relative_to is available in Python 3.9+
        if not target.is_relative_to(honeycomb):
            raise ValueError(f"Security Alert: Path traversal detected - {filename}")

        return target

    def _read_json(self, filename: str) -> Dict[str, Any]:
        """Read a JSON file from honeycomb."""
        # Resolve to absolute paths for security check
        base_path = self.honeycomb_path.resolve()
        filepath = (self.honeycomb_path / filename).resolve()

        # Ensure the resolved path is within the honeycomb directory
        if not filepath.is_relative_to(base_path):
             self.log(f"SECURITY ALERT: Path traversal attempt detected: {filename}", level="error")
             raise ValueError(f"Path traversal detected: {filename}")

        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
        return {}

    def _write_json(self, filename: str, data: Dict[str, Any]) -> None:
        """Write a JSON file to honeycomb."""
        # Resolve to absolute paths for security check
        base_path = self.honeycomb_path.resolve()
        filepath = (self.honeycomb_path / filename).resolve()

        # Ensure the resolved path is within the honeycomb directory
        if not filepath.is_relative_to(base_path):
             self.log(f"SECURITY ALERT: Path traversal attempt detected: {filename}", level="error")
             raise ValueError(f"Path traversal detected: {filename}")

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def read_intel(self) -> Dict[str, Any]:
        """Read intel.json."""
        return self._read_json("intel.json")

    def update_intel(self, updates: Dict[str, Any]) -> None:
        """Update intel.json."""
        intel = self.read_intel()
        intel.update(updates)
        self._write_json("intel.json", intel)

    def add_listener_intel(self, listener_id: str, data: Dict[str, Any]) -> None:
        """Add specific listener intel."""
        intel = self.read_intel()
        if "listeners" not in intel:
            intel["listeners"] = {}

        current = intel["listeners"].get(listener_id, {})
        current.update(data)
        current["last_seen"] = datetime.now(timezone.utc).isoformat()

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

    def write_intel(self, category: str, key: str,
                    data: Dict[str, Any]) -> None:
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
        existing = self.read_intel().get(
            "listeners",
            {}).get(
            "known_nodes",
            {}).get(
            node_id,
            {})

        # Ensure notes are appended, not replaced
        if "notes" in intel_data and "notes" in existing:
            intel_data["notes"] = existing["notes"] + intel_data["notes"]

        # Ensure numeric fields like 'dao_credits' are accumulated, not
        # overwritten
        for field in ["dao_credits", "donation_total", "interaction_count"]:
            if field in intel_data and field in existing:
                intel_data[field] = existing[field] + intel_data[field]

        intel_data["last_seen"] = datetime.now(timezone.utc).isoformat()
        if "first_seen" not in existing:
            intel_data["first_seen"] = intel_data["last_seen"]

        self.write_intel("listeners", f"known_nodes.{node_id}", intel_data)

    def post_alert(self, message: str, priority: bool = False) -> None:
        """Post an alert to state.json."""
        state = self._read_json("state.json")
        if "alerts" not in state:
            state["alerts"] = {"priority": [], "general": [], "normal": []}

        alert = {
            "message": message,
            "from": self.BEE_TYPE,
            "at": datetime.now(timezone.utc).isoformat()
        }

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
        """Read a JSON file using StorageAdapter."""
        if filename == "state.json":
            return self.state_manager.read_state()
            
        return self.storage.read(filename)

    def _write_json(self, filename: str, data: Dict[str, Any]) -> None:
        """Write a JSON file using StorageAdapter."""
        if filename == "state.json":
            self.state_manager.write_state(data, self.BEE_TYPE)
            return

        self.storage.write(filename, data)

    def _deep_merge(self, base: Dict, updates: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in updates.items():
            if key in result and isinstance(
                    result[key],
                    dict) and isinstance(
                    value,
                    dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _ask_llm_json(self, prompt_engineer: PromptEngineer, user_input: str) -> Dict[str, Any]:
        """
        Structured LLM Query.
        Args:
            prompt_engineer: Configured PromptEngineer instance.
            user_input: The user/event trigger text.
        Returns:
            Dict parsed from JSON.
        """
        # 0. Inject System 3 Wisdom (Episodic Memory)
        try:
            wisdom = self.wisdom_manager.get_relevant_wisdom()
            
            # Add Global Constraints if any
            if wisdom.get("constraints"):
                prompt_engineer.add_section("SYSTEM 3 WISDOM (LEARNED CONSTRAINTS)")
                for constraint in wisdom["constraints"]:
                    prompt_engineer.add_constraint(f"[LEARNED] {constraint['content']}")
            
            # Add Theology/Context
            if wisdom.get("theology", {}).get("core_tenets"):
                 prompt_engineer.add_context("\n".join(wisdom["theology"]["core_tenets"]))

        except Exception as w_err:
            self.log(f"Wisdom retrieval failed: {w_err}", level="warning")

        system_prompt = prompt_engineer.build_system_prompt()
        
        try:
            # We construct a message list for the chat model
            # Assuming self.llm_client.chat implies a method that takes history
            # If the client is simple text-in-text-out, we concat.
            
            # For this repo's simple client wrapper (likely):
            full_prompt = f"{system_prompt}\n\nUSER INPUT: {user_input}"
            
            # Call the LLM (using existing method)
            # Note: We rely on the model obeying the system prompt format instructions
            response_text = self.llm_client.generate(full_prompt)
            
            # Parse
            return PromptEngineer.parse_json_output(response_text)
            
        except Exception as e:
            self.log(f"LLM Structure Failure: {e}", level="error")
            return {"error": str(e)}

    def log(self, message: str, level: str = "info") -> None:
        """Log a message."""
        print(f"[{datetime.now().isoformat()}] [{self.BEE_TYPE.upper()}] {message}")

class EmployedBee(BaseBee):
    """
    A bee that has a specific role or employment (e.g. DJ, Researcher).
    """
    BEE_TYPE = "employed"
    CATEGORY = "content"

class ScoutBee(BaseBee):
    """
    A bee that looks for things (trends, sponsors).
    """
    BEE_TYPE = "scout"
    CATEGORY = "research"

class OnlookerBee(BaseBee):
    """
    A bee that observes (monitoring, logging).
    """
    BEE_TYPE = "onlooker"
    CATEGORY = "research"
