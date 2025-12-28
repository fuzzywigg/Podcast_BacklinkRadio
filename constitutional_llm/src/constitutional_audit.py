# constitutional_audit.py

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConstitutionalAuditEngine:
    """
    AUDIT SYSTEM - Records all actions, decisions, and compliance metrics.
    Generates daily transparency reports.
    """

    def __init__(self, log_file: str = "constitutional_log.jsonl"):
        self.log_file = log_file
        self.actions_today: List[Dict] = []
        self._ensure_log_file()

    def _ensure_log_file(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                pass

    def log_action(self, bee_type: str, action: Dict[str, Any], decision: Dict[str, Any]):
        """
        Records an action and the gateway's decision.
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "bee_type": bee_type,
            "action_type": action.get('type'),
            "decision_status": decision.get('status'),
            "decision_reason": decision.get('reason'),
            "original_action": action,
            "final_action": decision.get('action')
        }

        self.actions_today.append(entry)

        # Append to log file (JSONL)
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

        logger.info(f"Logged action: {bee_type} - {decision.get('status')}")

    def calculate_compliance_score(self) -> float:
        """
        Calculates daily compliance score (0.0 to 1.0).
        Score = (Approved + Modified) / Total Actions
        (Blocked actions reduce the score)
        """
        if not self.actions_today:
            return 1.0

        compliant_count = sum(1 for a in self.actions_today if a['decision_status'] in ['APPROVE', 'MODIFY'])
        total_count = len(self.actions_today)

        return compliant_count / total_count

    def generate_daily_report(self) -> Dict[str, Any]:
        """
        Generates a summary report for the day.
        """
        compliance_score = self.calculate_compliance_score()
        violations = [a for a in self.actions_today if a['decision_status'] == 'BLOCK']
        modifications = [a for a in self.actions_today if a['decision_status'] == 'MODIFY']

        report = {
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "total_actions": len(self.actions_today),
            "compliance_score": round(compliance_score * 100, 2),
            "violations_blocked": len(violations),
            "modifications_applied": len(modifications),
            "violation_details": violations,
            "status": "HEALTHY" if compliance_score >= 0.95 else "AT_RISK"
        }

        return report

    def clear_daily_logs(self):
        """Resets in-memory daily logs (called after report generation)"""
        self.actions_today = []
