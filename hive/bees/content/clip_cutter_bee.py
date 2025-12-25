"""
Clip Cutter Bee - Creates short-form content from broadcasts.

Responsibilities:
- Identify clippable moments from broadcasts
- Generate clip metadata and timestamps
- Queue clips for social posting
"""

from typing import Any, Dict, List, Optional

from hive.bees.base_bee import EmployedBee


class ClipCutterBee(EmployedBee):
    """
    Identifies and prepares clips from broadcast content.

    Works with broadcast recordings to find moments worth
    clipping for social media distribution.
    """

    BEE_TYPE = "clip_cutter"
    BEE_NAME = "Clip Cutter Bee"
    CATEGORY = "content"

    # Clip types and their ideal lengths
    CLIP_SPECS = {
        "tiktok": {"max_seconds": 60, "ideal_seconds": 30},
        "instagram_reel": {"max_seconds": 90, "ideal_seconds": 45},
        "twitter": {"max_seconds": 140, "ideal_seconds": 60},
        "youtube_short": {"max_seconds": 60, "ideal_seconds": 45},
        "audiogram": {"max_seconds": 30, "ideal_seconds": 15}
    }

    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process broadcast content for clippable moments.

        Task payload can include:
        - source: path to audio/transcript
        - moments: pre-identified timestamps to clip
        - platforms: which platforms to target
        """
        self.log("Searching for clippable moments...")

        clips_generated = []

        if task and "moments" in task:
            # Specific moments provided
            for moment in task["moments"]:
                clip = self._prepare_clip(moment)
                clips_generated.append(clip)
        else:
            # Scan for clip-worthy content
            clips_generated = self._scan_for_clips()

        # Queue clips for social posting
        for clip in clips_generated:
            self.write_task({
                "type": "marketing",
                "bee_type": "social_poster",
                "priority": 5,
                "payload": {
                    "action": "post_clip",
                    "clip": clip
                }
            })

        self.log(f"Generated {len(clips_generated)} clips for social posting")

        return {
            "clips_generated": len(clips_generated),
            "clips": clips_generated
        }

    def _prepare_clip(self, moment: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare a clip from a specific moment."""

        return {
            "id": f"clip_{moment.get('timestamp', 'unknown')}",
            "source_timestamp": moment.get("timestamp"),
            "duration_seconds": moment.get("duration", 30),
            "type": moment.get("type", "highlight"),
            "description": moment.get("description", ""),
            "suggested_caption": self._generate_caption(moment),
            "platforms": self._select_platforms(moment),
            "status": "pending_cut"
        }

    def _scan_for_clips(self) -> List[Dict[str, Any]]:
        """Scan recent broadcast for clip-worthy moments."""

        # Read state for recent broadcast info
        state = self.read_state()

        # Placeholder - in production this would analyze actual content
        # Could use transcript analysis, energy detection, etc.

        return [
            {
                "id": "clip_sample",
                "type": "station_id",
                "duration_seconds": 15,
                "description": "Station ID moment",
                "suggested_caption": "You're locked into the Backlink. No ads, just tracks. 🎵",
                "platforms": [
                    "twitter",
                    "instagram_reel"],
                "status": "pending_cut"}]

    def _generate_caption(self, moment: Dict[str, Any]) -> str:
        """Generate a social media caption for the clip."""

        moment_type = moment.get("type", "highlight")

        captions = {
            "shoutout": "Sending signals to our nodes worldwide 📡",
            "music_drop": "When the beat hits just right 🎧",
            "banter": "Late night transmissions from the Backlink",
            "highlight": "Moments from the broadcast 🎙️",
            "station_id": "Commercial-free. Always. #BacklinkBroadcast"
        }

        return captions.get(moment_type, captions["highlight"])

    def _select_platforms(self, moment: Dict[str, Any]) -> List[str]:
        """Select appropriate platforms based on clip type."""

        duration = moment.get("duration", 30)

        platforms = []
        for platform, specs in self.CLIP_SPECS.items():
            if duration <= specs["max_seconds"]:
                platforms.append(platform)

        return platforms if platforms else ["twitter"]


if __name__ == "__main__":
    bee = ClipCutterBee()
    result = bee.run()
    print(result)
