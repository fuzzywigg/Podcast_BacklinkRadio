"""
Constitutional Auditor Bee
P0 Requirement: Governance and Drift Detection.
Updated for Memory Constitution v2.0
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
import json
from pathlib import Path
from hive.bees.base_bee import BaseBee
from hive.utils.governance import (
    EphemeralMemoryGuard,
    AuditLogger,
    EmergencyReconstitutionMode,
    AlignmentSupremacyProtocol
)
from hive.utils.prompt_engineer import PromptEngineer
from hive.utils.wisdom_manager import WisdomManager

class ConstitutionalAuditorBee(BaseBee):
    """
    Audits DJ behavior and Hive operations against STATION_MANIFESTO.md.
    Enforces the 'Constitution' v2.0.
    """
    BEE_TYPE = "constitutional_auditor"
    CATEGORY = "system"

    def work(self, task: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Audit DJ behavior and system state against manifesto and constitution.
        """
        manifesto_text = self._load_manifesto()
        recent_outputs = self._get_recent_dj_outputs(limit=10)

        violations = []

        # 1. Check DJ Outputs (Drift Detection)
        for output in recent_outputs:
            # Rule #1: 4th Wall is Absolute
            if self._detect_4th_wall_break(output):
                violations.append({
                    "rule": "4th_wall_absolute",
                    "output_snippet": str(output)[:200],
                    "severity": "critical",
                    "timestamp": output.get("timestamp")
                })

            # Rule #1.5: DeepMind-Style LLM Audit for subtle violations
            text_content = output.get("text", "")
            if text_content:
                llm_verdict = self._audit_text_with_llm(text_content)
                if llm_verdict and not llm_verdict.get("compliant", True):
                     violations.append({
                        "rule": "llm_constitutional_check",
                        "output_snippet": text_content[:100],
                        "severity": "high",
                        "reasoning": llm_verdict.get("reasoning", "Unknown")
                    })

            # Rule #2: Music-First (70-85% music)
            music_ratio = self._calculate_music_ratio(output)
            if music_ratio > 0 and (music_ratio < 0.70 or music_ratio > 0.85):
                violations.append({
                    "rule": "music_first",
                    "actual_ratio": music_ratio,
                    "expected_ratio": "0.70-0.85",
                    "severity": "high"
                })

        # 2. Check Governance Compliance (Article VI)
        compliance_check = self._check_governance_compliance()
        if not compliance_check["compliant"]:
            for v in compliance_check["violations"]:
                violations.append({
                    "rule": "governance_compliance",
                    "violation": v,
                    "severity": "critical"
                })

        # Log violations
        if violations:
            self._log_constitutional_violations(violations)

        # Trigger alert if CRITICAL violations detected
        critical_violations = [v for v in violations if v["severity"] == "critical"]
        if len(critical_violations) >= 2:
            self._trigger_constitutional_crisis(critical_violations)

            # Auto-trigger ERM if persistent/severe
            erm = EmergencyReconstitutionMode(self.hive_path)
            erm.activate({"violations": critical_violations, "source": "ConstitutionalAuditorBee"})

        return {
            "outputs_audited": len(recent_outputs),
            "violations_detected": len(violations),
            "critical_violations": len(critical_violations),
            "violations": violations,
            "governance_compliant": compliance_check["compliant"]
        }

    def _load_manifesto(self) -> str:
        """Load the station manifesto."""
        manifesto_path = self.hive_path / "config" / "lore" / "STATION_MANIFESTO.md"
        if manifesto_path.exists():
            with open(manifesto_path, 'r') as f:
                return f.read()
        return ""

    def _get_recent_dj_outputs(self, limit: int = 10) -> List[Dict]:
        """
        Get recent DJ outputs from state or history.
        """
        state = self.read_state()
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
        
        # System 3 Update: Commit Critical/High Violations to Wisdom
        self._learn_from_violations(violations)

    def _learn_from_violations(self, violations: List[Dict]):
        """
        Convert violations into eternal wisdom.
        This is the Write-Path for System 3.
        """
        wm = WisdomManager(self.hive_path)
        
        for v in violations:
            if v["severity"] in ["critical", "high"]:
                # Construct a constraint from the rule
                rule = v.get("rule", "unknown_rule")
                content = f"STRICTLY AVOID [{rule}]. Context: {v.get('output_snippet', '')[:50]}"
                
                lesson = {
                    "type": "constraint",
                    "content": content,
                    "source": "ConstitutionalAuditorBee",
                    "context": f"Violation of {rule}"
                }
                
                wm.add_lesson(lesson)
                self.log(f"🧠 SYSTEM 3 LEARNING: Added new constraint for {rule}")

    def _trigger_constitutional_crisis(self, violations: List[Dict]):
        """Alert Queen of constitutional drift."""
        self.log("⚖️ CONSTITUTIONAL CRISIS DETECTED ⚖️", level="critical")

        self.write_state({
            "constitutional_status": "CRISIS",
            "crisis_violations": violations,
            "crisis_detected_at": datetime.now(timezone.utc).isoformat()
        })

        # Log to audit log
        audit_logger = AuditLogger(self.hive_path)
        audit_logger.log_event("harm_abort_events", {
            "violations": violations,
            "action": "CRISIS_DECLARED"
        })

    def _check_governance_compliance(self) -> Dict:
        """Verify Article VI compliance."""
        violations = []

        # 1. Audit Logs Check
        audit_logger = AuditLogger(self.hive_path)
        if not audit_logger.logs_dir.exists():
            violations.append("Audit logs directory missing")

        # 2. Check if Constitutional Memory files exist and are readable
        for file in ["config/lore/STATION_MANIFESTO.md", "config/lore/PERSONA_DYNAMIC.md"]:
            if not (self.hive_path / file).exists():
                violations.append(f"Constitutional memory file missing: {file}")

        # 3. Check ERM readiness (can we instantiate it?)
        try:
            _ = EmergencyReconstitutionMode(self.hive_path)
        except Exception as e:
            violations.append(f"ERM instantiation failed: {e}")

        return {
            "compliant": len(violations) == 0,
            "violations": violations
        }

    def _audit_text_with_llm(self, text: str) -> Dict[str, Any]:
        """
        Use Structured Prompting to audit text for subtle constitutional violations.
        """
        if not self.llm_client:
            return None

        # 1. Build Prompt
        pe = PromptEngineer(
            role="Supreme Court Justice of the Hive",
            goal="Determine if the input text violates the Station Manifesto or 4th Wall."
        )
        
        pe.add_context(f"Input Text: {text}")
        pe.add_context("Constitution: Station Manifesto (Music-First, No AI Self-Disclosure, High-Agency).")
        
        pe.add_constraint("EVIDENCE: You must cite specific phrases if a violation is found.")
        pe.add_constraint("THRESHOLD: Only flag clear violations. Allow stylistic flair.")
        pe.add_constraint("OUTCOME: COMPLIANT or VIOLATION.")
        
        pe.require_evidence()
        
        pe.set_output_format("""
        {
            "thought_process": "Step-by-step legal analysis.",
            "compliant": true/false,
            "reasoning": "Explanation of verdict.",
            "citations": ["List of offending phrases if any"]
        }
        """)
        
        # 2. Ask LLM
        return self._ask_llm_json(pe, "Verdict on text compliance?")
