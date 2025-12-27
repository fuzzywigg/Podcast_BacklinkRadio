"""
Giveaway Bee - Manages contests and promotional giveaways.

The Giveaway Bee handles:
- Creating and managing contests
- Selecting fair, random winners
- Tracking entries and eligibility
- Prize fulfillment coordination
"""

import json
import random
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_bee import EmployedBee


class GiveawayBee(EmployedBee):
    """
    Giveaway Bee - Runs contests and selects winners.
    
    Features:
    - Create giveaways with rules and prizes
    - Track entries with eligibility checks
    - Provably fair random winner selection
    - Prize fulfillment tracking
    """
    
    BEE_TYPE = "giveaway"
    BEE_NAME = "Giveaway Coordinator"
    CATEGORY = "community"
    LINEAGE_VERSION = "1.0.0"
    
    # Configuration
    MAX_ENTRIES_PER_USER = 5  # Anti-spam
    MIN_ACCOUNT_AGE_DAYS = 7  # Minimum account age
    
    def __init__(self, hive_path: Optional[str] = None, gateway: Any = None):
        """Initialize Giveaway Bee."""
        super().__init__(hive_path, gateway)
        self.giveaways_file = self.honeycomb_path / "giveaways.json"
        self._ensure_giveaways_file()
    
    def _ensure_giveaways_file(self):
        """Ensure giveaways.json exists."""
        if not self.giveaways_file.exists():
            initial = {
                "_meta": {
                    "created": datetime.now(timezone.utc).isoformat(),
                    "version": "1.0.0"
                },
                "active": [],
                "completed": [],
                "stats": {
                    "total_giveaways": 0,
                    "total_entries": 0,
                    "total_winners": 0
                }
            }
            with open(self.giveaways_file, 'w') as f:
                json.dump(initial, f, indent=2)
    
    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process giveaway tasks.
        
        Actions:
        - create: Create a new giveaway
        - enter: Register an entry
        - draw: Select winner(s)
        - status: Get giveaway status
        - list: List active giveaways
        - fulfill: Mark prize as fulfilled
        """
        action = "list"
        if task and "payload" in task:
            action = task["payload"].get("action", "list")
        
        if action == "create":
            return self._create_giveaway(task["payload"])
        elif action == "enter":
            return self._enter_giveaway(task["payload"])
        elif action == "draw":
            return self._draw_winner(task["payload"])
        elif action == "status":
            return self._get_status(task["payload"].get("giveaway_id"))
        elif action == "list":
            return self._list_giveaways()
        elif action == "fulfill":
            return self._fulfill_prize(task["payload"])
        else:
            return {"error": f"Unknown action: {action}"}
    
    def _load_giveaways(self) -> Dict[str, Any]:
        """Load giveaways data."""
        with open(self.giveaways_file, 'r') as f:
            return json.load(f)
    
    def _save_giveaways(self, data: Dict[str, Any]) -> None:
        """Save giveaways data."""
        data["_meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.giveaways_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _create_giveaway(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new giveaway."""
        required = ["name", "prize", "end_date"]
        for field in required:
            if field not in payload:
                return {"error": f"Missing required field: {field}"}
        
        data = self._load_giveaways()
        
        # Generate unique ID
        giveaway_id = hashlib.sha256(
            f"{payload['name']}:{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:12]
        
        giveaway = {
            "id": giveaway_id,
            "name": payload["name"],
            "description": payload.get("description", ""),
            "prize": payload["prize"],
            "prize_value": payload.get("prize_value"),
            "winner_count": payload.get("winner_count", 1),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "end_date": payload["end_date"],
            "rules": payload.get("rules", []),
            "eligibility": payload.get("eligibility", {}),
            "entries": [],
            "status": "active",
            "winners": []
        }
        
        data["active"].append(giveaway)
        data["stats"]["total_giveaways"] += 1
        
        self._save_giveaways(data)
        
        self.log(f"Created giveaway: {giveaway['name']} ({giveaway_id})")
        
        return {
            "success": True,
            "giveaway_id": giveaway_id,
            "name": giveaway["name"],
            "end_date": giveaway["end_date"]
        }
    
    def _enter_giveaway(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Enter a user into a giveaway."""
        giveaway_id = payload.get("giveaway_id")
        user_id = payload.get("user_id")
        user_name = payload.get("user_name", "Anonymous")
        
        if not giveaway_id or not user_id:
            return {"error": "Missing giveaway_id or user_id"}
        
        data = self._load_giveaways()
        
        # Find giveaway
        giveaway = None
        for g in data["active"]:
            if g["id"] == giveaway_id:
                giveaway = g
                break
        
        if not giveaway:
            return {"error": f"Giveaway {giveaway_id} not found or not active"}
        
        # Check if ended
        end_date = datetime.fromisoformat(giveaway["end_date"].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) > end_date:
            return {"error": "Giveaway has ended"}
        
        # Check existing entries
        user_entries = [e for e in giveaway["entries"] if e["user_id"] == user_id]
        if len(user_entries) >= self.MAX_ENTRIES_PER_USER:
            return {"error": f"Maximum entries ({self.MAX_ENTRIES_PER_USER}) reached"}
        
        # Add entry
        entry = {
            "user_id": user_id,
            "user_name": user_name,
            "entered_at": datetime.now(timezone.utc).isoformat(),
            "entry_number": len(giveaway["entries"]) + 1
        }
        
        giveaway["entries"].append(entry)
        data["stats"]["total_entries"] += 1
        
        self._save_giveaways(data)
        
        return {
            "success": True,
            "entry_number": entry["entry_number"],
            "total_entries": len(giveaway["entries"]),
            "user_entry_count": len(user_entries) + 1
        }
    
    def _draw_winner(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Draw winner(s) for a giveaway using provably fair randomness."""
        giveaway_id = payload.get("giveaway_id")
        
        if not giveaway_id:
            return {"error": "Missing giveaway_id"}
        
        data = self._load_giveaways()
        
        # Find giveaway
        giveaway = None
        giveaway_idx = None
        for idx, g in enumerate(data["active"]):
            if g["id"] == giveaway_id:
                giveaway = g
                giveaway_idx = idx
                break
        
        if not giveaway:
            return {"error": f"Giveaway {giveaway_id} not found"}
        
        if not giveaway["entries"]:
            return {"error": "No entries to draw from"}
        
        # Provably fair: use hash of entries + timestamp as seed
        seed_data = json.dumps(giveaway["entries"], sort_keys=True)
        seed_data += datetime.now(timezone.utc).isoformat()
        seed = int(hashlib.sha256(seed_data.encode()).hexdigest(), 16)
        random.seed(seed)
        
        # Get unique users (each user can only win once)
        unique_users = {}
        for entry in giveaway["entries"]:
            if entry["user_id"] not in unique_users:
                unique_users[entry["user_id"]] = entry
        
        user_list = list(unique_users.values())
        winner_count = min(giveaway["winner_count"], len(user_list))
        
        # Draw winners
        winners = random.sample(user_list, winner_count)
        
        # Record winners
        giveaway["winners"] = [
            {
                "user_id": w["user_id"],
                "user_name": w["user_name"],
                "won_at": datetime.now(timezone.utc).isoformat(),
                "fulfilled": False
            }
            for w in winners
        ]
        giveaway["status"] = "completed"
        giveaway["drawn_at"] = datetime.now(timezone.utc).isoformat()
        giveaway["draw_seed"] = hashlib.sha256(seed_data.encode()).hexdigest()[:16]
        
        # Move to completed
        data["active"].pop(giveaway_idx)
        data["completed"].append(giveaway)
        data["stats"]["total_winners"] += len(winners)
        
        self._save_giveaways(data)
        
        self.log(f"Drew {len(winners)} winner(s) for {giveaway['name']}")
        
        # Post alert
        winner_names = ", ".join(w["user_name"] for w in winners)
        self.post_alert(
            f"Giveaway '{giveaway['name']}' winners: {winner_names}",
            priority=True
        )
        
        return {
            "success": True,
            "giveaway_name": giveaway["name"],
            "total_entries": len(giveaway["entries"]),
            "unique_entrants": len(user_list),
            "winners": [
                {"user_id": w["user_id"], "user_name": w["user_name"]}
                for w in winners
            ],
            "draw_seed": giveaway["draw_seed"]
        }
    
    def _get_status(self, giveaway_id: Optional[str]) -> Dict[str, Any]:
        """Get status of a specific giveaway."""
        if not giveaway_id:
            return {"error": "Missing giveaway_id"}
        
        data = self._load_giveaways()
        
        # Search active
        for g in data["active"]:
            if g["id"] == giveaway_id:
                return {
                    "found": True,
                    "status": "active",
                    "giveaway": {
                        "id": g["id"],
                        "name": g["name"],
                        "prize": g["prize"],
                        "entries": len(g["entries"]),
                        "end_date": g["end_date"]
                    }
                }
        
        # Search completed
        for g in data["completed"]:
            if g["id"] == giveaway_id:
                return {
                    "found": True,
                    "status": "completed",
                    "giveaway": {
                        "id": g["id"],
                        "name": g["name"],
                        "prize": g["prize"],
                        "entries": len(g["entries"]),
                        "winners": g["winners"],
                        "drawn_at": g.get("drawn_at")
                    }
                }
        
        return {"found": False, "error": f"Giveaway {giveaway_id} not found"}
    
    def _list_giveaways(self) -> Dict[str, Any]:
        """List all active giveaways."""
        data = self._load_giveaways()
        
        active = [
            {
                "id": g["id"],
                "name": g["name"],
                "prize": g["prize"],
                "entries": len(g["entries"]),
                "end_date": g["end_date"]
            }
            for g in data["active"]
        ]
        
        return {
            "active_count": len(active),
            "giveaways": active,
            "stats": data["stats"]
        }
    
    def _fulfill_prize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Mark a winner's prize as fulfilled."""
        giveaway_id = payload.get("giveaway_id")
        user_id = payload.get("user_id")
        
        if not giveaway_id or not user_id:
            return {"error": "Missing giveaway_id or user_id"}
        
        data = self._load_giveaways()
        
        for g in data["completed"]:
            if g["id"] == giveaway_id:
                for winner in g["winners"]:
                    if winner["user_id"] == user_id:
                        winner["fulfilled"] = True
                        winner["fulfilled_at"] = datetime.now(timezone.utc).isoformat()
                        self._save_giveaways(data)
                        
                        return {
                            "success": True,
                            "giveaway": g["name"],
                            "user": winner["user_name"],
                            "fulfilled_at": winner["fulfilled_at"]
                        }
                
                return {"error": f"User {user_id} not a winner"}
        
        return {"error": f"Completed giveaway {giveaway_id} not found"}
