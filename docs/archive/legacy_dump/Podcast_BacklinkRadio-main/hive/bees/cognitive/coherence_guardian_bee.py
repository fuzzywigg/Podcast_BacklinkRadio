"""
Coherence Guardian Bee - Ensures hive consistency and prevents drift.

The Coherence Guardian is always-on and monitors:
- Bee behavior consistency across the hive
- Model-First Reasoning compliance
- State consistency across honeycomb files
- Constraint violations and drift detection

This is one of the "queen + council" equivalents that maintains
hive integrity as bees evolve and operate.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import hashlib

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_bee import OnlookerBee


class CoherenceGuardianBee(OnlookerBee):
    """
    Coherence Guardian - Maintains hive consistency.
    
    Responsibilities:
    - Monitor for drift between bee behaviors
    - Validate Model-First Reasoning compliance
    - Check state consistency across honeycomb
    - Flag constraint violations
    - Prevent incoherent updates from propagating
    
    This bee runs continuously to ensure the hive
    remains coherent as bees evolve and operate.
    """
    
    BEE_TYPE = "coherence_guardian"
    BEE_NAME = "Coherence Guardian"
    CATEGORY = "cognitive"
    LINEAGE_VERSION = "1.0.0"
    
    # Coherence thresholds
    STATE_DIVERGENCE_THRESHOLD = 0.3  # Max allowed state drift
    MODEL_COMPLETENESS_THRESHOLD = 0.7  # Min required model fields
    CONSTRAINT_VIOLATION_LIMIT = 3  # Max violations before alert
    
    def __init__(self, hive_path: Optional[str] = None, gateway: Any = None):
        """Initialize Coherence Guardian."""
        super().__init__(hive_path, gateway)
        self.violation_counts: Dict[str, int] = {}
        self.last_state_hash: Optional[str] = None
        self.coherence_history: List[Dict] = []
    
    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run coherence checks on the hive.
        
        Can be triggered:
        - On schedule (every 5 minutes)
        - On event (after major state changes)
        - Manually for diagnostics
        """
        action = "full_check"
        if task and "payload" in task:
            action = task["payload"].get("action", "full_check")
        
        if action == "full_check":
            return self._full_coherence_check()
        elif action == "validate_model":
            model = task["payload"].get("model", {})
            return self._validate_model(model)
        elif action == "check_state":
            return self._check_state_consistency()
        elif action == "check_bee":
            bee_type = task["payload"].get("bee_type")
            return self._check_bee_coherence(bee_type)
        elif action == "report":
            return self._generate_coherence_report()
        else:
            return {"error": f"Unknown action: {action}"}
    
    def _full_coherence_check(self) -> Dict[str, Any]:
        """Run all coherence checks."""
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks_performed": [],
            "issues_found": [],
            "overall_coherence": 1.0
        }
        
        # 1. State consistency check
        state_result = self._check_state_consistency()
        results["checks_performed"].append("state_consistency")
        if not state_result.get("consistent"):
            results["issues_found"].append({
                "type": "state_inconsistency",
                "details": state_result
            })
            results["overall_coherence"] *= 0.8
        
        # 2. Honeycomb integrity check
        honeycomb_result = self._check_honeycomb_integrity()
        results["checks_performed"].append("honeycomb_integrity")
        if honeycomb_result.get("issues"):
            results["issues_found"].extend(honeycomb_result["issues"])
            results["overall_coherence"] *= 0.9
        
        # 3. Pollen memory check
        pollen_result = self._check_pollen_health()
        results["checks_performed"].append("pollen_health")
        if pollen_result.get("warnings"):
            for warning in pollen_result["warnings"]:
                results["issues_found"].append({
                    "type": "pollen_warning",
                    "details": warning
                })
        
        # 4. Lineage tracking check
        lineage_result = self._check_lineage_health()
        results["checks_performed"].append("lineage_health")
        if lineage_result.get("pending_proposals", 0) > 5:
            results["issues_found"].append({
                "type": "governance_backlog",
                "details": f"{lineage_result['pending_proposals']} pending proposals"
            })
        
        # Store in history
        self.coherence_history.append({
            "timestamp": results["timestamp"],
            "coherence": results["overall_coherence"],
            "issue_count": len(results["issues_found"])
        })
        
        # Keep only last 100 checks
        self.coherence_history = self.coherence_history[-100:]
        
        # Alert if coherence drops too low
        if results["overall_coherence"] < 0.7:
            self.post_alert(
                f"⚠️ Hive coherence critical: {results['overall_coherence']:.0%}",
                priority=True
            )
        
        return results
    
    def _check_state_consistency(self) -> Dict[str, Any]:
        """Check state.json for consistency issues."""
        state = self.read_state()
        
        issues = []
        
        # Check required fields
        required_sections = ["broadcast", "persona", "nodes", "economy", "alerts"]
        for section in required_sections:
            if section not in state:
                issues.append(f"Missing section: {section}")
        
        # Check _meta timestamp
        meta = state.get("_meta", {})
        last_updated = meta.get("last_updated")
        if last_updated:
            try:
                update_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                age_hours = (datetime.now(timezone.utc) - update_time).total_seconds() / 3600
                if age_hours > 24:
                    issues.append(f"State is stale: {age_hours:.1f} hours old")
            except Exception:
                issues.append("Invalid last_updated timestamp")
        
        # Check for state hash changes
        current_hash = hashlib.md5(json.dumps(state, sort_keys=True).encode()).hexdigest()
        changed = self.last_state_hash and self.last_state_hash != current_hash
        self.last_state_hash = current_hash
        
        return {
            "consistent": len(issues) == 0,
            "issues": issues,
            "state_changed": changed,
            "sections_present": [s for s in required_sections if s in state]
        }
    
    def _check_honeycomb_integrity(self) -> Dict[str, Any]:
        """Check all honeycomb files for integrity."""
        issues = []
        files_checked = []
        
        honeycomb_files = ["state.json", "tasks.json", "intel.json", "pollen.json", "lineage.json"]
        
        for filename in honeycomb_files:
            filepath = self.honeycomb_path / filename
            files_checked.append(filename)
            
            if not filepath.exists():
                if filename in ["pollen.json", "lineage.json"]:
                    # These are optional
                    continue
                issues.append({
                    "file": filename,
                    "issue": "File missing"
                })
                continue
            
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Check for _meta section
                if "_meta" not in data and filename != "treasury.json":
                    issues.append({
                        "file": filename,
                        "issue": "Missing _meta section"
                    })
                    
            except json.JSONDecodeError as e:
                issues.append({
                    "file": filename,
                    "issue": f"Invalid JSON: {str(e)}"
                })
            except Exception as e:
                issues.append({
                    "file": filename,
                    "issue": f"Read error: {str(e)}"
                })
        
        return {
            "files_checked": files_checked,
            "issues": issues,
            "healthy": len(issues) == 0
        }
    
    def _check_pollen_health(self) -> Dict[str, Any]:
        """Check pollen memory for health issues."""
        pollen_path = self.honeycomb_path / "pollen.json"
        
        if not pollen_path.exists():
            return {"status": "not_initialized", "warnings": []}
        
        try:
            with open(pollen_path, 'r') as f:
                pollen = json.load(f)
            
            entries = pollen.get("entries", [])
            stats = pollen.get("stats", {})
            
            warnings = []
            
            # Check for stale pollen
            stale_count = 0
            for entry in entries:
                try:
                    timestamp = datetime.fromisoformat(entry.get("timestamp", "").replace('Z', '+00:00'))
                    age_days = (datetime.now(timezone.utc) - timestamp).days
                    if age_days > 90:
                        stale_count += 1
                except Exception:
                    pass
            
            if stale_count > len(entries) * 0.5:
                warnings.append(f"{stale_count} stale pollen entries (>90 days old)")
            
            # Check for low-quality patterns
            low_quality = sum(1 for e in entries if e.get("success_score", 0) < 0.6)
            if low_quality > len(entries) * 0.3:
                warnings.append(f"{low_quality} low-quality patterns (score < 0.6)")
            
            return {
                "status": "healthy" if not warnings else "warnings",
                "total_entries": len(entries),
                "total_recalls": stats.get("total_recalls", 0),
                "warnings": warnings
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e), "warnings": []}
    
    def _check_lineage_health(self) -> Dict[str, Any]:
        """Check lineage tracking for health issues."""
        lineage_path = self.honeycomb_path / "lineage.json"
        
        if not lineage_path.exists():
            return {"status": "not_initialized", "pending_proposals": 0}
        
        try:
            with open(lineage_path, 'r') as f:
                lineage = json.load(f)
            
            stats = lineage.get("stats", {})
            proposals = lineage.get("proposals", [])
            
            pending = sum(1 for p in proposals if p.get("status") == "pending")
            
            return {
                "status": "healthy",
                "registered_types": len(lineage.get("bee_types", {})),
                "total_proposals": len(proposals),
                "pending_proposals": pending,
                "approved_rate": (
                    stats.get("approved_proposals", 0) / max(len(proposals), 1)
                )
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e), "pending_proposals": 0}
    
    def _validate_model(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a Model-First Reasoning model for completeness.
        
        This is called by other bees to validate their models
        before execution.
        """
        required_fields = ["task_type", "entities", "state_variables", 
                         "possible_actions", "constraints"]
        
        missing = [f for f in required_fields if f not in model or not model[f]]
        completeness = 1.0 - (len(missing) / len(required_fields))
        
        issues = []
        
        # Check entities
        if not model.get("entities"):
            issues.append("No entities defined")
        
        # Check actions
        actions = model.get("possible_actions", [])
        if not actions:
            issues.append("No possible actions defined")
        elif len(actions) > 20:
            issues.append("Too many possible actions (>20) - may indicate unclear model")
        
        # Check constraints
        constraints = model.get("constraints", [])
        if not constraints:
            issues.append("No constraints defined - risky for coherence")
        
        # Check for pollen references
        if not model.get("pollen_sources"):
            issues.append("No pollen sources referenced - consider checking memory")
        
        valid = completeness >= self.MODEL_COMPLETENESS_THRESHOLD and len(issues) <= 1
        
        return {
            "valid": valid,
            "completeness": completeness,
            "missing_fields": missing,
            "issues": issues,
            "recommendation": "proceed" if valid else "revise_model"
        }
    
    def _check_bee_coherence(self, bee_type: str) -> Dict[str, Any]:
        """Check coherence of a specific bee type."""
        # Check lineage
        lineage_path = self.honeycomb_path / "lineage.json"
        
        lineage_info = {"registered": False}
        if lineage_path.exists():
            with open(lineage_path, 'r') as f:
                lineage = json.load(f)
            
            if bee_type in lineage.get("bee_types", {}):
                bee_data = lineage["bee_types"][bee_type]
                lineage_info = {
                    "registered": True,
                    "current_version": bee_data.get("current_version"),
                    "version_count": len(bee_data.get("versions", []))
                }
        
        # Check pollen for this bee
        pollen_path = self.honeycomb_path / "pollen.json"
        pollen_info = {"patterns": 0, "avg_score": 0}
        if pollen_path.exists():
            with open(pollen_path, 'r') as f:
                pollen = json.load(f)
            
            bee_entries = [e for e in pollen.get("entries", []) 
                         if e.get("bee_type") == bee_type]
            if bee_entries:
                pollen_info = {
                    "patterns": len(bee_entries),
                    "avg_score": sum(e.get("success_score", 0) for e in bee_entries) / len(bee_entries)
                }
        
        return {
            "bee_type": bee_type,
            "lineage": lineage_info,
            "pollen": pollen_info,
            "coherent": lineage_info.get("registered", False)
        }
    
    def _generate_coherence_report(self) -> Dict[str, Any]:
        """Generate a comprehensive coherence report."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "history_summary": {
                "checks": len(self.coherence_history),
                "avg_coherence": (
                    sum(h["coherence"] for h in self.coherence_history) / 
                    max(len(self.coherence_history), 1)
                ),
                "total_issues": sum(h["issue_count"] for h in self.coherence_history)
            },
            "current_state": self._check_state_consistency(),
            "honeycomb": self._check_honeycomb_integrity(),
            "pollen": self._check_pollen_health(),
            "lineage": self._check_lineage_health()
        }
