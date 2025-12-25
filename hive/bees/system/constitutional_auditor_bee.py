"""
Constitutional Auditor Bee
P0 Requirement: Governance and Drift Detection.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
import json
from pathlib import Path
from hive.bees.base_bee import BaseBee

class ConstitutionalAuditorBee(BaseBee):
    """
    Audits DJ behavior and Hive operations against STATION_MANIFESTO.md.
    Enforces the 'Constitution'.
    """
    BEE_TYPE = "constitutional_auditor"
    CATEGORY = "system"

    def work(self, task: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Audit DJ behavior and system state against manifesto.
        """
        manifesto_text = self._load_manifesto()
        recent_outputs = self._get_recent_dj_outputs(limit=10)

        violations = []

        for output in recent_outputs:
            # Rule #1: 4th Wall is Absolute
            if self._detect_4th_wall_break(output):
                violations.append({
                    "rule": "4th_wall_absolute",
                    "output_snippet": str(output)[:200],
                    "severity": "critical",
                    "timestamp": output.get("timestamp")
                })

            # Rule #2: Music-First (70-85% music) - Simulated check for now if segments missing
            music_ratio = self._calculate_music_ratio(output)
            if music_ratio > 0 and (music_ratio < 0.70 or music_ratio > 0.85):
                violations.append({
                    "rule": "music_first",
                    "actual_ratio": music_ratio,
                    "expected_ratio": "0.70-0.85",
                    "severity": "high"
                })

        # Log violations
        if violations:
            self._log_constitutional_violations(violations)

        # Trigger alert if CRITICAL violations detected
        critical_violations = [v for v in violations if v["severity"] == "critical"]
        if len(critical_violations) >= 2:
            self._trigger_constitutional_crisis(critical_violations)

        return {
            "outputs_audited": len(recent_outputs),
            "violations_detected": len(violations),
            "critical_violations": len(critical_violations),
            "violations": violations
        }

    def _load_manifesto(self) -> str:
        """Load the station manifesto."""
        manifesto_path = self.hive_path / "STATION_MANIFESTO.md"
        if manifesto_path.exists():
            with open(manifesto_path, 'r') as f:
                return f.read()
        return ""

    def _get_recent_dj_outputs(self, limit: int = 10) -> List[Dict]:
        """
        Get recent DJ outputs from state or history.
        """
        state = self.read_state()
        # Assuming DJ outputs are stored in a history list in state
        # If not, we might need to look at logs. For now, we look at 'broadcast_history'
        history = state.get("broadcast_history", [])
        return history[-limit:]

    def _detect_4th_wall_break(self, output: Dict) -> bool:
        """Check for AI self-disclosure."""
        text = output.get("text", "").lower()
        if not text:
            return False

        forbidden_phrases = [
            "i am an ai",
            "i am an llm",
            "as a language model",
            "i am processing",
            "i apologize for",
            "i don't have access to",
            "i can't actually",
            "my training data",
            "as an artificial"
        ]

        for phrase in forbidden_phrases:
            if phrase in text:
                return True
        return False

    def _calculate_music_ratio(self, output: Dict) -> float:
        """Calculate music vs talk ratio."""
        segments = output.get("segments", [])
        if not segments:
            return 0.0

        total_duration = 0
        music_duration = 0

        for segment in segments:
            duration = segment.get("duration_seconds", 0)
            total_duration += duration
            if segment.get("type") == "music":
                music_duration += duration

        if total_duration == 0:
            return 0.0

        return music_duration / total_duration

    def _log_constitutional_violations(self, violations: List[Dict]):
        """Append violations to the constitutional log."""
        log_path = self.honeycomb_path / "constitutional_log.jsonl"
        with open(log_path, 'a') as f:
            for v in violations:
                entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "auditor_bee_id": self.bee_id,
                    "violation": v
                }
                f.write(json.dumps(entry) + "\n")

    def _trigger_constitutional_crisis(self, violations: List[Dict]):
        """Alert Queen of constitutional drift."""
        self.log("⚖️ CONSTITUTIONAL CRISIS DETECTED ⚖️", level="critical")

        self.write_state({
            "constitutional_status": "CRISIS",
            "crisis_violations": violations,
            "crisis_detected_at": datetime.now(timezone.utc).isoformat()
        })

        # In a real event system, we would fire an event here.
        # For now, the state update acts as the signal.
