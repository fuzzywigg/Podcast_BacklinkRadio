"""
Experience Distiller Bee - Converts logs to reusable patterns.

The Experience Distiller analyzes completed tasks and successful
patterns, extracting high-signal experiences that become "pollen"
for future bee generations. It:
- Monitors completed tasks for high-value patterns
- Distills successful workflows into reusable templates
- Prunes low-quality or stale pollen
- Maintains optimal pollen quality
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_bee import OnlookerBee


class ExperienceDistillerBee(OnlookerBee):
    """
    Experience Distiller - Converts logs to pollen.
    
    Responsibilities:
    - Scan completed tasks for high-value patterns
    - Extract and store successful workflows as pollen
    - Prune stale or low-quality pollen entries
    - Analyze pollen utilization and recommend improvements
    
    This is the "learning" component that helps the hive
    improve over time by remembering what works.
    """
    
    BEE_TYPE = "experience_distiller"
    BEE_NAME = "Experience Distiller"
    CATEGORY = "cognitive"
    LINEAGE_VERSION = "1.0.0"
    
    # Distillation thresholds
    MIN_SUCCESS_SCORE = 0.7  # Minimum score to become pollen
    MAX_POLLEN_AGE_DAYS = 90  # Prune pollen older than this
    MIN_RECALL_FOR_PRESERVATION = 3  # Keep if recalled this many times
    
    def __init__(self, hive_path: Optional[str] = None, gateway: Any = None):
        """Initialize Experience Distiller."""
        super().__init__(hive_path, gateway)
        self.distillation_log: List[Dict] = []
    
    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process experience distillation tasks.
        
        Actions:
        - distill: Scan and distill new experiences
        - prune: Remove stale/low-quality pollen
        - analyze: Analyze pollen utilization
        - report: Generate distillation report
        """
        action = "distill"
        if task and "payload" in task:
            action = task["payload"].get("action", "distill")
        
        if action == "distill":
            return self._distill_experiences()
        elif action == "prune":
            return self._prune_pollen()
        elif action == "analyze":
            return self._analyze_utilization()
        elif action == "report":
            return self._generate_report()
        else:
            return {"error": f"Unknown action: {action}"}
    
    def _get_pollen(self) -> Dict[str, Any]:
        """Load pollen data."""
        pollen_path = self.honeycomb_path / "pollen.json"
        if pollen_path.exists():
            with open(pollen_path, 'r') as f:
                return json.load(f)
        return {"entries": [], "index": {}, "stats": {}}
    
    def _save_pollen(self, pollen: Dict[str, Any]) -> None:
        """Save pollen data."""
        pollen["_meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        pollen_path = self.honeycomb_path / "pollen.json"
        with open(pollen_path, 'w') as f:
            json.dump(pollen, f, indent=2)
    
    def _distill_experiences(self) -> Dict[str, Any]:
        """Scan completed tasks and distill into pollen."""
        tasks = self.read_tasks()
        completed = tasks.get("completed", [])
        
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scanned": 0,
            "distilled": 0,
            "skipped": 0,
            "new_pollen": []
        }
        
        # Get existing pollen to avoid duplicates
        existing_pollen = self._get_pollen()
        existing_ids = {e.get("id") for e in existing_pollen.get("entries", [])}
        
        for task in completed:
            results["scanned"] += 1
            
            # Check if task has result with success info
            result = task.get("result", {})
            if not isinstance(result, dict):
                results["skipped"] += 1
                continue
            
            # Check success
            success = result.get("success", False)
            if not success:
                results["skipped"] += 1
                continue
            
            # Extract model if present
            model = result.get("model", {})
            if not model:
                # Try to construct a basic model from task
                model = self._construct_model_from_task(task)
            
            # Calculate success score
            success_score = self._calculate_success_score(task, result)
            
            if success_score < self.MIN_SUCCESS_SCORE:
                results["skipped"] += 1
                continue
            
            # Generate pollen ID
            pollen_id = self._generate_pollen_id(task, model)
            
            if pollen_id in existing_ids:
                # Already exists, maybe update score
                results["skipped"] += 1
                continue
            
            # Create pollen entry
            pollen_entry = {
                "id": pollen_id,
                "bee_type": task.get("claimed_by", "unknown").split("_")[0],
                "task_type": task.get("type", "unknown"),
                "model": model,
                "result_summary": {
                    "success": True,
                    "duration": result.get("duration_seconds"),
                    "summary": str(result.get("result", ""))[:200]
                },
                "success_score": success_score,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "lineage_version": "1.0.0",
                "tags": self._extract_tags(task, model),
                "recall_count": 0,
                "last_recalled": None
            }
            
            existing_pollen["entries"].append(pollen_entry)
            existing_ids.add(pollen_id)
            
            results["distilled"] += 1
            results["new_pollen"].append({
                "id": pollen_id,
                "type": pollen_entry["task_type"],
                "score": success_score
            })
            
            self.distillation_log.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "task_id": task.get("id"),
                "pollen_id": pollen_id,
                "score": success_score
            })
        
        # Update stats
        existing_pollen["stats"]["total_entries"] = len(existing_pollen["entries"])
        
        # Save updated pollen
        self._save_pollen(existing_pollen)
        
        return results
    
    def _construct_model_from_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Construct a basic model from task data."""
        return {
            "task_type": task.get("type", "unknown"),
            "entities": [
                task.get("claimed_by", "unknown_bee"),
                task.get("created_by", "system")
            ],
            "state_variables": {},
            "possible_actions": ["process"],
            "constraints": [],
            "pollen_sources": []
        }
    
    def _calculate_success_score(self, task: Dict, result: Dict) -> float:
        """Calculate success score for a completed task."""
        score = 0.5  # Base score for any success
        
        # Bonus for fast completion
        duration = result.get("duration_seconds", 0)
        if duration > 0 and duration < 10:
            score += 0.2
        elif duration < 60:
            score += 0.1
        
        # Bonus for having a model
        if result.get("model"):
            score += 0.2
        
        # Bonus for no errors
        if not task.get("last_error"):
            score += 0.1
        
        # Penalty for retries
        attempts = task.get("attempts", 1)
        if attempts > 1:
            score -= 0.1 * (attempts - 1)
        
        return max(0.0, min(1.0, score))
    
    def _extract_tags(self, task: Dict, model: Dict) -> List[str]:
        """Extract tags from task and model."""
        tags = set()
        
        # Add task type
        if task.get("type"):
            tags.add(task["type"])
        
        # Add bee type
        if task.get("claimed_by"):
            bee_type = task["claimed_by"].split("_")[0]
            tags.add(bee_type)
        
        # Add model entities
        for entity in model.get("entities", []):
            if isinstance(entity, str) and len(entity) < 50:
                tags.add(entity)
        
        # Add task type
        if model.get("task_type"):
            tags.add(model["task_type"])
        
        return list(tags)
    
    def _generate_pollen_id(self, task: Dict, model: Dict) -> str:
        """Generate unique pollen ID."""
        import hashlib
        content = f"{task.get('id', '')}:{task.get('type', '')}:{json.dumps(model, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _prune_pollen(self) -> Dict[str, Any]:
        """Remove stale or low-quality pollen."""
        pollen = self._get_pollen()
        entries = pollen.get("entries", [])
        
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "before_count": len(entries),
            "pruned": 0,
            "preserved": 0,
            "reasons": []
        }
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.MAX_POLLEN_AGE_DAYS)
        
        kept = []
        for entry in entries:
            should_prune = False
            reason = None
            
            # Check age
            try:
                timestamp = datetime.fromisoformat(entry.get("timestamp", "").replace('Z', '+00:00'))
                if timestamp < cutoff:
                    # Old, but check if frequently recalled
                    if entry.get("recall_count", 0) >= self.MIN_RECALL_FOR_PRESERVATION:
                        # Preserve - frequently used
                        pass
                    else:
                        should_prune = True
                        reason = f"Stale (age > {self.MAX_POLLEN_AGE_DAYS} days, recalls < {self.MIN_RECALL_FOR_PRESERVATION})"
            except Exception:
                pass
            
            # Check quality
            if entry.get("success_score", 0) < 0.5:
                should_prune = True
                reason = f"Low quality (score < 0.5)"
            
            if should_prune:
                results["pruned"] += 1
                results["reasons"].append({
                    "id": entry.get("id"),
                    "reason": reason
                })
            else:
                kept.append(entry)
                results["preserved"] += 1
        
        # Update pollen
        pollen["entries"] = kept
        pollen["stats"]["total_entries"] = len(kept)
        
        # Rebuild indexes
        pollen["index"] = self._rebuild_indexes(kept)
        
        self._save_pollen(pollen)
        
        return results
    
    def _rebuild_indexes(self, entries: List[Dict]) -> Dict[str, Any]:
        """Rebuild pollen indexes."""
        by_bee_type: Dict[str, List[str]] = {}
        by_task_type: Dict[str, List[str]] = {}
        by_tag: Dict[str, List[str]] = {}
        
        for entry in entries:
            pollen_id = entry.get("id", "")
            
            # By bee type
            bee_type = entry.get("bee_type", "")
            if bee_type:
                if bee_type not in by_bee_type:
                    by_bee_type[bee_type] = []
                by_bee_type[bee_type].append(pollen_id)
            
            # By task type
            task_type = entry.get("task_type", "")
            if task_type:
                if task_type not in by_task_type:
                    by_task_type[task_type] = []
                by_task_type[task_type].append(pollen_id)
            
            # By tag
            for tag in entry.get("tags", []):
                if tag not in by_tag:
                    by_tag[tag] = []
                by_tag[tag].append(pollen_id)
        
        return {
            "by_bee_type": by_bee_type,
            "by_task_type": by_task_type,
            "by_tag": by_tag
        }
    
    def _analyze_utilization(self) -> Dict[str, Any]:
        """Analyze pollen utilization patterns."""
        pollen = self._get_pollen()
        entries = pollen.get("entries", [])
        
        if not entries:
            return {"status": "empty", "message": "No pollen entries"}
        
        # Calculate metrics
        total_recalls = sum(e.get("recall_count", 0) for e in entries)
        recalled_entries = [e for e in entries if e.get("recall_count", 0) > 0]
        never_recalled = len(entries) - len(recalled_entries)
        
        # Find top patterns
        top_patterns = sorted(
            entries,
            key=lambda e: (e.get("recall_count", 0), e.get("success_score", 0)),
            reverse=True
        )[:10]
        
        # Find unused high-quality patterns
        unused_quality = [
            e for e in entries
            if e.get("recall_count", 0) == 0 and e.get("success_score", 0) > 0.8
        ]
        
        # Age distribution
        now = datetime.now(timezone.utc)
        age_buckets = {"<7d": 0, "7-30d": 0, "30-90d": 0, ">90d": 0}
        for entry in entries:
            try:
                ts = datetime.fromisoformat(entry.get("timestamp", "").replace('Z', '+00:00'))
                age_days = (now - ts).days
                if age_days < 7:
                    age_buckets["<7d"] += 1
                elif age_days < 30:
                    age_buckets["7-30d"] += 1
                elif age_days < 90:
                    age_buckets["30-90d"] += 1
                else:
                    age_buckets[">90d"] += 1
            except Exception:
                pass
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_entries": len(entries),
            "total_recalls": total_recalls,
            "never_recalled": never_recalled,
            "utilization_rate": len(recalled_entries) / max(len(entries), 1),
            "avg_score": sum(e.get("success_score", 0) for e in entries) / len(entries),
            "top_patterns": [
                {"id": p["id"], "recalls": p.get("recall_count", 0), "score": p.get("success_score", 0)}
                for p in top_patterns
            ],
            "unused_quality_count": len(unused_quality),
            "age_distribution": age_buckets,
            "recommendations": self._get_recommendations(entries, never_recalled, unused_quality)
        }
    
    def _get_recommendations(
        self, 
        entries: List[Dict], 
        never_recalled: int,
        unused_quality: List[Dict]
    ) -> List[str]:
        """Generate recommendations for pollen improvement."""
        recommendations = []
        
        if never_recalled > len(entries) * 0.5:
            recommendations.append(
                f"Over 50% of pollen never recalled - consider pruning or improving recall"
            )
        
        if len(unused_quality) > 5:
            recommendations.append(
                f"{len(unused_quality)} high-quality patterns unused - check tagging/discovery"
            )
        
        if len(entries) > 500:
            recommendations.append(
                "Large pollen store (>500) - consider pruning to improve recall performance"
            )
        
        if len(entries) < 10:
            recommendations.append(
                "Small pollen store (<10) - run more distillation cycles"
            )
        
        return recommendations
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive distillation report."""
        utilization = self._analyze_utilization()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "utilization": utilization,
            "recent_distillations": self.distillation_log[-20:],
            "summary": {
                "total_pollen": utilization.get("total_entries", 0),
                "utilization_rate": f"{utilization.get('utilization_rate', 0):.1%}",
                "avg_score": f"{utilization.get('avg_score', 0):.2f}",
                "health": "healthy" if utilization.get("utilization_rate", 0) > 0.3 else "underutilized"
            }
        }
