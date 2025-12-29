import random
from datetime import datetime, timezone
from typing import Any

from hive.bees.base_bee import EmployedBee
from hive.utils.audio_adapter import AudioStreamAdapter


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

    def __init__(self, hive_path: str | None = None):
        super().__init__(hive_path)
        self.audio_adapter = AudioStreamAdapter()

    def work(self, task: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Select the next track and manage library.
        """
        self.log("DJ Bee spinning up...")

        # 1. Read State
        intel = self.read_intel()
        treasury = intel.get("treasury", {"balance": 20.00, "history": []})
        library = intel.get("music_library", {"owned": [], "rented": []})
        broadcast = intel.get("broadcast_state", {"now_playing": None, "queue": []})

        # 2. Process Incoming Task
        action = task.get("payload", {}).get("action") if task else None

        # Handle Directive Injection
        if action == "apply_directive":
            directives = task.get("payload", {}).get("directives", {})
            self._apply_listener_directive(directives)
            # Also continue to ensure queue is populated

        request = task.get("request") if task else None
        decision = None

        if request:
            decision = self._evaluate_request(request, treasury, library)

            # --- CONSTITUTIONAL CHECK ---
            if decision["action"] in ["buy", "rent"]:
                # Before spending, validate with the Gateway
                action_payload = {
                    "type": "deal_negotiation",  # Maps to Artist-First principle
                    "cost": decision["cost"],
                    "asset": decision["track"]["title"],
                    "artist_revenue": decision["cost"] * 0.70,  # Assume 70% share
                    "total_revenue": decision["cost"],
                }

                veto = self.validate_action(action_payload)

                if veto["status"] == "BLOCK":
                    self.log(
                        f"Transaction blocked by Constitution: {veto['reason']}", level="warning"
                    )
                    decision = {
                        "action": "decline",
                        "reason": f"Constitutional Veto: {veto['reason']}",
                        "cost": 0.0,
                    }
                else:
                    self.log(f"Constitution Approved: {veto.get('reason')}")
                    self._execute_transaction(decision, treasury, library)
                    broadcast["queue"].append(decision["track"])

            elif decision["action"] == "play_owned":
                broadcast["queue"].append(decision["track"])
            else:
                self.log(f"Declined request: {decision['reason']}")

            # Track Tip Revenue (if any)
            tip = float(request.get("tip", 0.0))
            if tip > 0:
                # Assuming tip is added to treasury? The current logic doesn't explicitly add tip to balance
                # But we should track it as revenue regardless.
                # If we were to add it: treasury["balance"] += tip
                # For now, just tracking the event as per requirements.
                # analytics.track_tip_received(
                #    amount=tip,
                #    source=request.get("source", "unknown"),
                #    song_requested=request.get("song")
                # )
                pass

        # 3. Autopilot (Ensure Queue is Populated)
        if not broadcast["queue"]:
            next_track = self._pick_autopilot_track(library)
            broadcast["queue"].append(next_track)

        # 4. "Broadcast" the next track (Simulated)
        if broadcast["queue"] and not broadcast.get("now_playing"):
            now_playing = broadcast["queue"].pop(0)
            now_playing["started_at"] = datetime.now(timezone.utc).isoformat()
            broadcast["now_playing"] = now_playing

            self.log(f"Now Playing: {now_playing['title']} (Source: {now_playing['source']})")

            # Track Queue/Play
            # Track Queue/Play
            # analytics.track_song_queued(
            #    song_title=now_playing["title"],
            #    acquisition_type=now_playing.get("source", "unknown")
            # )

            # PUSH METADATA TO LIVE365
            self.audio_adapter.update_metadata(now_playing)

        # 5. Write State
        # We need to update treasury, library, and broadcast state
        # Note: intel.json update should be atomic in real impl, here we just
        # merge
        updates = {"treasury": treasury, "music_library": library, "broadcast_state": broadcast}

        # We need to carefully merge this back to intel.json
        # Since EmployedBee.write_state writes to 'state.json', we might need
        # to use a specialized method or direct intel write if 'treasury' is shared.
        # But for now, we'll assume we can update these keys in intel.

        # To update intel.json directly (shared state):
        full_intel = self.read_intel()
        full_intel.update(updates)
        # BaseBee._write_json prepends honeycomb_path, so we just pass the
        # filename
        self._write_json("intel.json", full_intel)

        return {
            "status": "success",
            "decision": decision,
            "now_playing": broadcast.get("now_playing"),
            "treasury_balance": treasury["balance"],
        }

    def _evaluate_request(self, request: dict, treasury: dict, library: dict) -> dict:
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
                    "reason": "Already owned",
                }

        # Logic 1: Purchase (Tier 1)
        # If tip covers cost OR (obscure & cheap & decent balance)
        is_obscure = request.get("obscure", False)  # Simplified flag
        cost = self.COST_BUY_OBSCURE if is_obscure else self.COST_BUY_POPULAR

        if tip >= cost:
            return {
                "action": "buy",
                "cost": cost,
                "track": {"title": song_title, "source": "owned", "acquired_by": "tip"},
                "reason": f"Tip ${tip} covers cost ${cost}",
            }

        # Logic 2: Rental (Tier 2)
        if balance > self.RESERVE_MINIMUM:
            return {
                "action": "rent",
                "cost": self.COST_RENT,
                "track": {"title": song_title, "source": "rented", "license": "single_play"},
                "reason": "Treasury healthy, renting",
            }

        # Logic 3: Decline (Tier 3)
        return {"action": "decline", "reason": "Insufficient funds & song not owned", "cost": 0.0}

    def _execute_transaction(self, decision: dict, treasury: dict, library: dict):
        """Deduct funds and update library."""
        cost = decision.get("cost", 0.0)
        action = decision.get("action")
        track = decision.get("track")

        if cost > 0:
            treasury["balance"] -= cost
            treasury["history"].append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "amount": -cost,
                    "type": action,
                    "item": track["title"],
                }
            )

        if action == "buy":
            track["id"] = f"track_{len(library['owned']) + 1}"
            library["owned"].append(track)
        elif action == "rent":
            track["id"] = f"rent_{len(library.get('rented', [])) + 1}"
            library["rented"].append(track)  # Log history if needed

    def _apply_listener_directive(self, directives: dict[str, Any]):
        """
        Apply payment-injected preferences
        """
        # Update music/talk ratio
        if "music_ratio" in directives:
            self.music_ratio = directives["music_ratio"]
            self.write_to_honeycomb(
                "dj_config",
                {
                    "music_ratio": self.music_ratio,
                    "updated_by": "listener_payment",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            self.log(f"Music ratio updated to {self.music_ratio}")

        # Update source files
        if "source_files" in directives:
            self._load_grok_list(directives["source_files"])

        # Update no-repeat window
        if "no_repeat_window" in directives:
            self.no_repeat_hours = directives["no_repeat_window"]
            self.log(f"No-repeat window updated to {self.no_repeat_hours} hours")

        # Queue tracks immediately (simulated logic for "queue_now")
        if directives.get("queue_now"):
            # Logic to queue 5 tracks would go here
            pass

    async def fill_talk_window(self, song_end_time: datetime, next_minute: datetime) -> str:
        """
        Fill the gap between song end and next minute
        NEVER exceed next whole minute
        """
        available_seconds = (next_minute - song_end_time).total_seconds()

        # Placeholder for next track fetching (simulated)
        next_track = self._get_next_track_meta()

        if available_seconds < 5:
            # Too short - just announce next track
            return f"Up next: {next_track.get('artist')} - {next_track.get('title')}"

        # Build announcement segments (priority order)
        segments = []
        time_used = 0

        # 1. REQUIRED: Next track announcement (always first, ~5 sec)
        segments.append(self.announce_next_track(next_track))
        time_used += 5

        # 2. OPTIONAL: Add-ons if time permits
        if available_seconds >= 15:
            # New node announcement
            if self._has_new_nodes():
                segments.append(self.announce_new_nodes())
                time_used += 10

        if available_seconds >= 30:
            # Update on the 8s content (if at :08 or :38)
            if self.is_update_time():
                segments.append(self.get_update_on_8s())
                time_used += 15

        # Generate speech, verify timing
        # In this simulation, we just join segments.
        # In prod, we'd use TTS duration estimation.
        speech = " ".join(segments)
        # speech_duration = self.estimate_duration(speech) # Not implemented

        # if speech_duration > available_seconds:
        #    # Fallback: just next track
        #    return segments[0]

        return speech

    def announce_next_track(self, track: dict) -> str:
        """
        REQUIRED: Always announce what's coming
        Format: "Artist - Track Name"
        """
        return f"Coming up: {track.get('artist', 'Unknown')}, {track.get('title', 'Unknown')}."

    def announce_new_nodes(self) -> str:
        """Announce new nodes."""
        return "We see new Nodes coming online. Welcome to the swarm."

    def is_update_time(self) -> bool:
        """Check if it's :08 or :38."""
        now = datetime.now(timezone.utc)
        return now.minute in [8, 38]

    def get_update_on_8s(self) -> str:
        """Get 'Update on the 8s' content."""
        # Ideally fetches from WeatherBee via Honeycomb
        intel = self.read_intel()
        weather_snippet = intel.get("weather", {}).get("latest_snippet", "Weather data processing.")
        return f"Update on the 8s: {weather_snippet}"

    def _get_next_track_meta(self) -> dict:
        """Helper to get next track meta."""
        broadcast = self.read_intel().get("broadcast_state", {})
        queue = broadcast.get("queue", [])
        if queue:
            return queue[0]
        return {"artist": "Unknown", "title": "Mystery Track"}

    def _has_new_nodes(self) -> bool:
        """Check for new nodes in intel."""
        intel = self.read_intel()
        return intel.get("listeners", {}).get("has_new", False)

    def _load_grok_list(self, files: list):
        """
        Load music from GROK.txt or other specified lists
        """
        for filename in files:
            if filename == "grok.txt":
                # Simplified loader for demonstration
                try:
                    file_path = self.hive_path.parent / "GROK.txt"
                    if file_path.exists():
                        with open(file_path) as f:
                            # Just a mock parsing for now as GROK.txt structure
                            # is unknown
                            self.log(f"Loaded tracks from {filename}")
                            # In real impl, parse and add to wishlist/library
                except Exception as e:
                    self.log(f"Failed to load {filename}: {e}", level="error")

    def _pick_autopilot_track(self, library: dict) -> dict:
        """Pick a song when no requests are active."""
        if library.get("owned"):
            return random.choice(library["owned"])
        return {"title": "Lo-Fi Beats - Free Stream", "source": "free_archive", "id": "free_01"}

    def write_to_honeycomb(self, key: str, data: Any):
        """Write specific key to honeycomb (intel.json wrapper)."""
        intel = self.read_intel()
        intel[key] = data
        self._write_json("intel.json", intel)


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
        "request": {"song": "Never Gonna Give You Up", "tip": 10.00, "source": "simulated_user"}
    }
    res = bee.work(task)
    print(res)
