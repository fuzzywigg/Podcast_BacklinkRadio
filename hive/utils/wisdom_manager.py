"""
Wisdom Manager
Center for Episodic Memory and Learned Constraints (System 3).
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class WisdomManager:
    """
    Manages the 'wisdom.json' file, serving as the Hive's Episodic Memory.
    Allows bees to Retrieve relevant past lessons and Auditors to Commit new lessons.
    """

    def __init__(self, hive_path: Path):
        self.hive_path = hive_path
        self.honeycomb_path = hive_path / "hive" / "honeycomb"
        self.wisdom_path = self.honeycomb_path / "wisdom.json"

        # Ensure proper initialization
        self._ensure_wisdom_store()

    def _ensure_wisdom_store(self):
        """Initialize wisdom.json if it doesn't exist."""
        if not self.wisdom_path.exists():
            initial_state = {
                "integrity_hash": "genesis",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "global_constraints": [],
                "episodes": [],
                "theology": {
                    "core_tenets": ["The Hive exists to Broadcast.", "The 4th Wall is Sacred."]
                },
            }
            self._write_wisdom(initial_state)

    def _read_wisdom(self) -> dict[str, Any]:
        """Read the raw wisdom store."""
        try:
            with open(self.wisdom_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to read wisdom: {e}")
            return {"global_constraints": [], "episodes": []}

    def _write_wisdom(self, data: dict[str, Any]):
        """Write to wisdom store atomically."""
        temp_path = self.wisdom_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            temp_path.replace(self.wisdom_path)
        except Exception as e:
            logging.error(f"Failed to write wisdom: {e}")

    def get_relevant_wisdom(self, context_tags: list[str] | None = None) -> dict[str, Any]:
        """
        Retrieve wisdom relevant to the current context.
        Currently returns ALL global constraints.
        TODO: Implement vector/tag-based filtering for Episodes.
        """
        data = self._read_wisdom()

        # Always return global constraints
        constraints = data.get("global_constraints", [])

        # Simple Logic: If we ever have tagged episodes, filter here.
        # For now, return the 'Theology' as context.
        theology = data.get("theology", {})

        return {"constraints": constraints, "theology": theology}

    def add_lesson(self, lesson: dict[str, Any]):
        """
        Add a new lesson (Constraint or Episode) to the store.
        args:
            lesson: {
                "type": "constraint" | "episode",
                "content": str,
                "source": "ConstitutionalAuditorBee",
                "context": str (optional)
            }
        """
        data = self._read_wisdom()

        entry = {"timestamp": datetime.now(timezone.utc).isoformat(), **lesson}

        if lesson.get("type") == "constraint":
            # Check for duplicates? simple text check for now
            existing = [c["content"] for c in data.get("global_constraints", [])]
            if lesson["content"] not in existing:
                if "global_constraints" not in data:
                    data["global_constraints"] = []
                data["global_constraints"].append(entry)

        elif lesson.get("type") == "episode":
            if "episodes" not in data:
                data["episodes"] = []
            data["episodes"].append(entry)
            # Keep episodes bounded? e.g. last 100
            if len(data["episodes"]) > 100:
                data["episodes"] = data["episodes"][-100:]

        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._write_wisdom(data)
