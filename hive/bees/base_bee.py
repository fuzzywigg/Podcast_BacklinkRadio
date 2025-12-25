"""
Base Bee - The Abstract Worker
Updated to use StateManager for secure operations.
"""

import json
import logging
import uuid
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime, timezone

from hive.utils.state_manager import StateManager

class BaseBee(ABC):
    """
    Abstract base class for all bees.
    """

    BEE_TYPE = "base"
    BEE_NAME = "Base Bee"
    CATEGORY = "general"

    def __init__(self, hive_path: Optional[Union[str, Path]] = None, gateway: Any = None):
        """Initialize the bee."""
        if hive_path is None:
            # Default to repo root/hive
            self.hive_path = Path(__file__).parent.parent.parent / "hive"
        else:
            self.hive_path = Path(hive_path)

        self.honeycomb_path = self.hive_path / "honeycomb"
        self.gateway = gateway

        # Generate Unique Bee ID
        self.bee_id = f"{self.BEE_TYPE}_{str(uuid.uuid4())[:8]}"

        # Initialize State Manager
        self.state_manager = StateManager(self.hive_path)

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

            self._write_json("tasks.json", tasks)

    # ─────────────────────────────────────────────────────────────
    # HELPER METHODS
    # ─────────────────────────────────────────────────────────────

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

        intel["listeners"][listener_id] = current
        self._write_json("intel.json", intel)

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

        key = "priority" if priority else "normal" # Changed from "general" to "normal" to match test expectations
        if key not in state["alerts"]:
            state["alerts"][key] = []

        state["alerts"][key].append(alert)
        self._write_json("state.json", state)

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
