"""
DJ Bee - The Autonomous Music Director.
Updated with Tiered Acquisition Logic and Constitutional Checks.
"""

from typing import Any, Dict, Optional
import random
from datetime import datetime, timezone
from hive.bees.base_bee import EmployedBee 
class DjBee(BaseBee):
from hive.bees.base_bee import EmployedBee

class DjBee(EmployedBee):
    """
    Manages the music library and broadcast queue.
    Implements the "Smart DJ" economic logic.
    """

    BEE_TYPE = "dj"
    BEE_NAME = "DJ Bee"
    CATEGORY = "content"

    # Economic Constants
    COST_BUY_OBSCURE = 1.50
    COST_BUY_POPULAR = 8.00
    COST_RENT = 0.05
    RESERVE_MINIMUM = 5.00

    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Select the next track and manage library.
        """
        self.log("DJ Bee spinning up...")

        # 1. Read State
        intel = self.read_intel()
        treasury = intel.get("treasury", {"balance": 20.00, "history": []})
        library = intel.get("music_library", {"owned": [], "rented": []})
        broadcast = intel.get("broadcast_state", {"now_playing": None, "queue": []})

        # 2. Process Request
        request = task.get("request") if task else None
        decision = None

        if request:
            decision = self._evaluate_request(request, treasury, library)

            # --- CONSTITUTIONAL CHECK ---
            if decision["action"] in ["buy", "rent"]:
                # Before spending, validate with the Gateway
                action_payload = {
                    "type": "deal_negotiation", # Maps to Artist-First principle
                    "cost": decision["cost"],
                    "asset": decision["track"]["title"],
                    "artist_revenue": decision["cost"] * 0.70, # Assume 70% share
                    "total_revenue": decision["cost"]
                }

                veto = self.validate_action(action_payload)

                if veto["status"] == "BLOCK":
                    self.log(f"Transaction blocked by Constitution: {veto['reason']}", level="warning")
                    decision = {"action": "decline", "reason": f"Constitutional Veto: {veto['reason']}", "cost": 0.0}
                else:
                    self.log(f"Constitution Approved: {veto.get('reason')}")
                    self._execute_transaction(decision, treasury, library)
                    broadcast["queue"].append(decision["track"])

            elif decision["action"] == "play_owned":
                 broadcast["queue"].append(decision["track"])

        # 3. Autopilot (Ensure Queue is Populated)
        if not broadcast["queue"]:
            next_track = self._pick_autopilot_track(library)
            broadcast["queue"].append(next_track)

        # 4. "Broadcast" the next track (Simulated)
        if broadcast["queue"] and not broadcast.get("now_playing"):
            now_playing = broadcast["queue"].pop(0)
            now_playing["started_at"] = datetime.now(timezone.utc).isoformat()
            broadcast["now_playing"] = now_playing
            self.log(f"Now Playing: {now_playing['title']}")

        # 5. Write State
        self.write_intel("treasury", "balance", treasury["balance"])
        self.write_intel("treasury", "history", treasury["history"])
        self.write_intel("music_library", "owned", library["owned"])
        self.write_intel("broadcast_state", "now_playing", broadcast["now_playing"])
        self.write_intel("broadcast_state", "queue", broadcast["queue"])

        return {
            "status": "success",
            "decision": decision,
            "now_playing": broadcast.get("now_playing"),
            "treasury_balance": treasury["balance"]
        }

    def _evaluate_request(self, request: Dict, treasury: Dict, library: Dict) -> Dict:
        """
        Decide whether to Buy, Rent, or Play Existing based on logic.
        """
        song_title = request.get("song")
        tip = float(request.get("tip", 0.0))
        balance = float(treasury.get("balance", 0.0))

        # Check if already owned
        for track in library.get("owned", []):
            if track["title"].lower() == song_title.lower():
                return {
                    "action": "play_owned",
                    "track": track,
                    "cost": 0.0,
                    "reason": "Already owned"
                }

        # Logic 1: Purchase (Tier 1)
        cost = self.COST_BUY_POPULAR # Simplified
        if tip >= cost:
             return {
                "action": "buy",
                "cost": cost,
                "track": {"title": song_title, "source": "owned", "acquired_by": "tip"},
                "reason": f"Tip ${tip} covers cost ${cost}"
             }

        # Logic 2: Rental (Tier 2)
        if balance > self.RESERVE_MINIMUM:
            return {
                "action": "rent",
                "cost": self.COST_RENT,
                "track": {"title": song_title, "source": "rented", "license": "single_play"},
                "reason": "Treasury healthy, renting"
            }

        # Logic 3: Decline (Tier 3)
        return {
            "action": "decline",
            "reason": "Insufficient funds & song not owned",
            "cost": 0.0
        }

    def _execute_transaction(self, decision: Dict, treasury: Dict, library: Dict):
        """Deduct funds and update library."""
        cost = decision.get("cost", 0.0)
        action = decision.get("action")
        track = decision.get("track")

        if cost > 0:
            treasury["balance"] -= cost
            treasury["history"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "amount": -cost,
                "type": action,
                "item": track["title"]
            })

        if action == "buy":
            track["id"] = f"track_{len(library['owned']) + 1}"
            library["owned"].append(track)
        elif action == "rent":
            track["id"] = f"rent_{len(library.get('rented', [])) + 1}"
            library.setdefault("rented", []).append(track)

    def _pick_autopilot_track(self, library: Dict) -> Dict:
        """Pick a song when no requests are active."""
        if library.get("owned"):
            return random.choice(library["owned"])
        return {
            "title": "Lo-Fi Beats - Free Stream",
            "source": "free_archive",
            "id": "free_01"
        }
