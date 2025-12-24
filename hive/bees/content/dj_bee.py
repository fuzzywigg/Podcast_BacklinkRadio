"""
DJ Bee - The Autonomous Music Director.

Responsibilities:
- Manage the $20 Treasury.
- Select music based on Tiered Acquisition Logic (Free, Rent, Buy).
- Process listener requests.
- Update broadcast state.
"""

from typing import Any, Dict, Optional
import sys
import random
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_bee import EmployedBee


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

        Task payload can include:
        - request: { "song": "Title", "tip": 5.00, "source": "twitter" }
        """
        self.log("DJ Bee spinning up...")

        # 1. Read State
        intel = self.read_intel()
        treasury = intel.get("treasury", {"balance": 20.00, "history": []})
        library = intel.get("music_library", {"owned": [], "rented": []})
        broadcast = intel.get("broadcast_state", {"now_playing": None, "queue": []})

        # 2. Process Incoming Request (if any)
        request = task.get("request") if task else None
        decision = None

        if request:
            decision = self._evaluate_request(request, treasury, library)
            if decision["action"] in ["buy", "rent"]:
                self._execute_transaction(decision, treasury, library)
                broadcast["queue"].append(decision["track"])
            elif decision["action"] == "play_owned":
                 broadcast["queue"].append(decision["track"])
            else:
                self.log(f"Declined request: {decision['reason']}")

        # 3. Ensure Queue is Populated (Autopilot)
        if not broadcast["queue"]:
            # If empty, pick a random owned song or a free track
            next_track = self._pick_autopilot_track(library)
            broadcast["queue"].append(next_track)

        # 4. "Broadcast" the next track (Simulated)
        # In a real loop, we'd wait for the current track to finish.
        # Here, we just pop the queue to 'now_playing'.
        if broadcast["queue"]:
            now_playing = broadcast["queue"].pop(0)
            now_playing["started_at"] = datetime.now(timezone.utc).isoformat()
            broadcast["now_playing"] = now_playing

            self.log(f"Now Playing: {now_playing['title']} (Source: {now_playing['source']})")

        # 5. Write State
        # We need to update treasury, library, and broadcast state
        # Note: intel.json update should be atomic in real impl, here we just merge
        updates = {
            "treasury": treasury,
            "music_library": library,
            "broadcast_state": broadcast
        }

        # We need to carefully merge this back to intel.json
        # Since EmployedBee.write_state writes to 'state.json', we might need
        # to use a specialized method or direct intel write if 'treasury' is shared.
        # But for now, we'll assume we can update these keys in intel.

        # To update intel.json directly (shared state):
        full_intel = self.read_intel()
        full_intel.update(updates)
        self._write_json(self.hive_path / "honeycomb/intel.json", full_intel)

        return {
            "status": "success",
            "decision": decision,
            "now_playing": broadcast["now_playing"],
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
                    "reason": "Already owned"
                }

        # Logic 1: Purchase (Tier 1)
        # If tip covers cost OR (obscure & cheap & decent balance)
        is_obscure = request.get("obscure", False) # Simplified flag
        cost = self.COST_BUY_OBSCURE if is_obscure else self.COST_BUY_POPULAR

        if tip >= cost:
             return {
                "action": "buy",
                "cost": cost,
                "track": {"title": song_title, "source": "owned", "acquired_by": "tip"},
                "reason": f"Tip ${tip} covers cost ${cost}"
             }

        # Logic 2: Rental (Tier 2)
        # If balance > reserve
        if balance > self.RESERVE_MINIMUM:
            return {
                "action": "rent",
                "cost": self.COST_RENT,
                "track": {"title": song_title, "source": "rented", "license": "single_play"},
                "reason": "Treasury healthy, renting"
            }

        # Logic 3: Decline (Tier 3 fallback)
        return {
            "action": "decline",
            "reason": "Insufficient funds & song not owned"
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
            # Add to owned library
            # Generate a pseudo-ID
            track["id"] = f"track_{len(library['owned']) + 1}"
            library["owned"].append(track)

        elif action == "rent":
            # Add to rented log (optional, or just queue it)
            track["id"] = f"rent_{len(library.get('rented', [])) + 1}"
            library["rented"].append(track) # Log history if needed

    def _pick_autopilot_track(self, library: Dict) -> Dict:
        """Pick a song when no requests are active."""
        if library["owned"]:
            return random.choice(library["owned"])

        # Fallback to "Free Creative Commons" placeholder
        return {
            "title": "Lo-Fi Beats - Free Stream",
            "source": "free_archive",
            "id": "free_01"
        }

if __name__ == "__main__":
    # Test Run
    bee = DjBee()

    # 1. Test Autopilot (no request)
    print("--- Autopilot Test ---")
    res = bee.work()
    print(res)

    # 2. Test Request (Tip)
    print("\n--- Request Test (Rich Tip) ---")
    task = {
        "request": {
            "song": "Never Gonna Give You Up",
            "tip": 10.00,
            "source": "simulated_user"
        }
    }
    res = bee.work(task)
    print(res)
