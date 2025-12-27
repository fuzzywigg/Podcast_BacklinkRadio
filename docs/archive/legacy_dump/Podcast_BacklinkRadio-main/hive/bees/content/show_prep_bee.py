"""
Show Prep Bee - Prepares content for the broadcast.

Responsibilities:
- Research topics for DJ banter
- Pull relevant news/events for listener locations
- Prepare talking points
- Queue up trivia and fun facts
"""

from typing import Any, Dict, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_bee import EmployedBee


class ShowPrepBee(EmployedBee):
    """
    Prepares show content and talking points.

    Reads listener intel and current trends to generate
    relevant content for the DJ to use during broadcasts.
    """

    BEE_TYPE = "show_prep"
    BEE_NAME = "Show Prep Bee"
    CATEGORY = "content"

    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate show prep materials.

        Task payload can include:
        - time_slot: morning|afternoon|evening|night
        - focus_nodes: list of listener locations to research
        - topics: specific topics to prep
        """
        self.log("Starting show prep...")

        # Read current intel
        intel = self.read_intel()
        state = self.read_state()

        # Determine time slot
        time_slot = "evening"
        if task and "time_slot" in task:
            time_slot = task["time_slot"]

        prep_materials = {
            "time_slot": time_slot,
            "talking_points": [],
            "listener_shoutouts": [],
            "trivia": [],
            "local_context": {}
        }

        # Generate time-appropriate talking points
        prep_materials["talking_points"] = self._generate_talking_points(time_slot)

        # Pull listener intel for shoutouts
        known_nodes = intel.get("listeners", {}).get("known_nodes", {})
        for node_id, node_data in known_nodes.items():
            if node_data.get("location"):
                shoutout = self._prepare_shoutout(node_id, node_data)
                prep_materials["listener_shoutouts"].append(shoutout)

        # Generate trivia for ad break replacements
        prep_materials["trivia"] = self._generate_trivia()

        # Write to state for DJ to pick up
        self.write_state({
            "show_prep": prep_materials
        })

        self.log(f"Prep complete: {len(prep_materials['talking_points'])} talking points, "
                f"{len(prep_materials['listener_shoutouts'])} shoutouts ready")

        return prep_materials

    def _generate_talking_points(self, time_slot: str) -> list:
        """Generate talking points based on time of day."""

        # Base talking points by time slot
        points_by_slot = {
            "morning": [
                {"type": "energy", "text": "Rise and grind. New day, new frequencies."},
                {"type": "weather", "text": "Check your local conditions before heading out."},
                {"type": "motivation", "text": "The queue is locked and loaded. Let's move."}
            ],
            "afternoon": [
                {"type": "focus", "text": "Midday momentum. Stay locked in."},
                {"type": "productivity", "text": "This one's for the grinders still at it."},
                {"type": "transition", "text": "Halfway there. Keep the signal strong."}
            ],
            "evening": [
                {"type": "unwind", "text": "Day's done. Time to decompress."},
                {"type": "vibe", "text": "Evening frequencies settling in."},
                {"type": "chill", "text": "No rush now. Just the music."}
            ],
            "night": [
                {"type": "late", "text": "Night owls, you know who you are."},
                {"type": "deep", "text": "The quiet hours. Best transmission time."},
                {"type": "cosmic", "text": "Out there in the dark, we're all connected."}
            ]
        }

        return points_by_slot.get(time_slot, points_by_slot["evening"])

    def _prepare_shoutout(self, node_id: str, node_data: dict) -> dict:
        """Prepare a personalized shoutout for a listener."""

        location = node_data.get("location", {})
        city = location.get("city", "somewhere out there")

        return {
            "node_id": node_id,
            "city": city,
            "template": f"Signal coming in from {city}. We see you.",
            "context": node_data.get("notes", [])[-1] if node_data.get("notes") else None
        }

    def _generate_trivia(self) -> list:
        """Generate trivia for commercial break replacements."""

        # Static trivia for now - could be enhanced to pull from APIs
        return [
            {
                "type": "music",
                "text": "The first song played on MTV was 'Video Killed the Radio Star.' Ironic.",
                "use_after_genre": "rock"
            },
            {
                "type": "tech",
                "text": "The first radio broadcast was in 1906. We've been connecting nodes ever since.",
                "use_after_genre": None
            },
            {
                "type": "station",
                "text": "Commercial-free since day one. That's the Backlink promise.",
                "use_after_genre": None
            }
        ]


if __name__ == "__main__":
    # Test run
    bee = ShowPrepBee()
    result = bee.run({"time_slot": "evening"})
    print(result)
