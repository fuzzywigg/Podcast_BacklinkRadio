"""
ViralAnalystBee - Viral Content Analysis Bee

Analyzes content virality potential, tracks what's spreading,
and identifies timing/format patterns for maximum reach.
"""

from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
import json

# Import base
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_bee import BaseBee


class ViralAnalystBee(BaseBee):
    """
    Analyzes viral potential and content spread patterns.
    
    Type: Onlooker bee
    Priority: Normal
    Schedule: Continuous monitoring
    """
    
    BEE_TYPE = "viral_analyst"
    BEE_NAME = "ViralAnalystBee"
    CATEGORY = "marketing"
    LINEAGE_VERSION = "1.0.0"
    
    def __init__(self, hive_path: Optional[Path] = None):
        super().__init__(hive_path=hive_path)
        self.viral_file = self.honeycomb_path / "viral_analysis.json"
        self._ensure_viral_file()
    
    def _ensure_viral_file(self):
        """Initialize viral analysis storage."""
        if not self.viral_file.exists():
            initial = {
                "content_tracked": [],
                "viral_patterns": [],
                "timing_insights": {
                    "best_days": ["Tuesday", "Wednesday", "Thursday"],
                    "best_hours": [9, 12, 17, 20],
                    "avoid_hours": [2, 3, 4, 5]
                },
                "format_scores": {
                    "short_video": 0.85,
                    "meme": 0.80,
                    "thread": 0.70,
                    "image": 0.65,
                    "audio_clip": 0.60,
                    "long_form": 0.40
                },
                "stats": {
                    "content_analyzed": 0,
                    "viral_hits": 0,
                    "avg_viral_score": 0
                }
            }
            self.viral_file.write_text(json.dumps(initial, indent=2))
    
    def _load_data(self) -> Dict:
        return json.loads(self.viral_file.read_text())
    
    def _save_data(self, data: Dict):
        self.viral_file.write_text(json.dumps(data, indent=2))
    
    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze viral patterns."""
        return self._get_patterns(task or {})
    
    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute viral analysis tasks."""
        action = task.get("action", "analyze")
        
        actions = {
            "analyze": self._analyze_content,
            "score": self._calculate_viral_score,
            "track": self._track_content,
            "patterns": self._get_patterns,
            "timing": self._get_timing_insights,
            "recommend": self._get_recommendations,
            "update_tracking": self._update_tracking,
            "get_stats": self._get_stats
        }
        
        if action not in actions:
            return {"error": f"Unknown action: {action}"}
        
        return self.safe_action(actions[action], task)
    
    def _calculate_viral_score(self, task: Dict) -> Dict:
        """Calculate viral potential score for content."""
        content_type = task.get("content_type", "image")
        has_hook = task.get("has_hook", False)
        is_timely = task.get("is_timely", False)
        emotional_trigger = task.get("emotional_trigger", False)
        shareable = task.get("shareable", True)
        length_optimal = task.get("length_optimal", True)
        
        data = self._load_data()
        
        # Base score from format
        base_score = data["format_scores"].get(content_type, 0.5)
        
        # Modifiers
        modifiers = 0
        if has_hook:
            modifiers += 0.15
        if is_timely:
            modifiers += 0.20
        if emotional_trigger:
            modifiers += 0.15
        if shareable:
            modifiers += 0.10
        if length_optimal:
            modifiers += 0.10
        
        # Calculate final score (cap at 1.0)
        final_score = min(base_score + modifiers, 1.0)
        
        # Determine tier
        if final_score >= 0.85:
            tier = "high_viral_potential"
            recommendation = "Prioritize for immediate posting"
        elif final_score >= 0.65:
            tier = "good_potential"
            recommendation = "Schedule for optimal timing"
        elif final_score >= 0.45:
            tier = "moderate_potential"
            recommendation = "Consider enhancing before posting"
        else:
            tier = "low_potential"
            recommendation = "Rework or deprioritize"
        
        return {
            "success": True,
            "viral_score": round(final_score, 2),
            "tier": tier,
            "recommendation": recommendation,
            "breakdown": {
                "base_score": base_score,
                "modifiers": round(modifiers, 2),
                "content_type": content_type
            }
        }
    
    def _analyze_content(self, task: Dict) -> Dict:
        """Full content analysis for virality."""
        content_id = task.get("content_id")
        content_type = task.get("content_type", "image")
        title = task.get("title", "")
        description = task.get("description", "")
        
        data = self._load_data()
        
        # Analyze characteristics
        has_hook = len(title) > 0 and len(title) < 60
        is_timely = task.get("is_timely", False)
        emotional_words = ["amazing", "shocking", "must", "urgent", "breaking"]
        emotional_trigger = any(word in (title + description).lower() for word in emotional_words)
        
        # Calculate score
        score_result = self._calculate_viral_score({
            "content_type": content_type,
            "has_hook": has_hook,
            "is_timely": is_timely,
            "emotional_trigger": emotional_trigger,
            "shareable": True,
            "length_optimal": True
        })
        
        analysis = {
            "content_id": content_id,
            "viral_score": score_result["viral_score"],
            "tier": score_result["tier"],
            "characteristics": {
                "has_hook": has_hook,
                "is_timely": is_timely,
                "emotional_trigger": emotional_trigger,
                "content_type": content_type
            },
            "recommendations": [
                score_result["recommendation"]
            ],
            "optimal_timing": self._get_next_optimal_time(),
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Update stats
        data["stats"]["content_analyzed"] += 1
        if score_result["viral_score"] >= 0.85:
            data["stats"]["viral_hits"] += 1
        
        self._save_data(data)
        
        return {"success": True, "analysis": analysis}
    
    def _get_next_optimal_time(self) -> str:
        """Get next optimal posting time."""
        now = datetime.now(timezone.utc)
        data = self._load_data()
        
        best_hours = data["timing_insights"]["best_hours"]
        
        for hour in best_hours:
            target = now.replace(hour=hour, minute=0, second=0)
            if target > now:
                return target.isoformat()
        
        # Next day first good hour
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=best_hours[0], minute=0, second=0).isoformat()
    
    def _track_content(self, task: Dict) -> Dict:
        """Start tracking content performance."""
        data = self._load_data()
        
        tracking = {
            "content_id": task.get("content_id"),
            "platform": task.get("platform"),
            "posted_at": task.get("posted_at", datetime.now(timezone.utc).isoformat()),
            "initial_viral_score": task.get("viral_score"),
            "metrics": {
                "views": 0,
                "shares": 0,
                "comments": 0,
                "likes": 0
            },
            "status": "tracking",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        data["content_tracked"].append(tracking)
        self._save_data(data)
        
        return {"success": True, "tracking": tracking}
    
    def _update_tracking(self, task: Dict) -> Dict:
        """Update tracking metrics for content."""
        content_id = task.get("content_id")
        metrics = task.get("metrics", {})
        
        data = self._load_data()
        
        for item in data["content_tracked"]:
            if item["content_id"] == content_id:
                item["metrics"].update(metrics)
                item["last_updated"] = datetime.now(timezone.utc).isoformat()
                
                # Check if went viral
                if metrics.get("shares", 0) > 1000 or metrics.get("views", 0) > 100000:
                    item["status"] = "viral"
                
                self._save_data(data)
                return {"success": True, "tracking": item}
        
        return {"error": f"Content not found: {content_id}"}
    
    def _get_patterns(self, task: Dict) -> Dict:
        """Get identified viral patterns."""
        data = self._load_data()
        
        return {
            "success": True,
            "patterns": data["viral_patterns"],
            "format_scores": data["format_scores"]
        }
    
    def _get_timing_insights(self, task: Dict) -> Dict:
        """Get optimal timing insights."""
        data = self._load_data()
        
        return {
            "success": True,
            "timing": data["timing_insights"],
            "next_optimal": self._get_next_optimal_time()
        }
    
    def _get_recommendations(self, task: Dict) -> Dict:
        """Get content recommendations for virality."""
        data = self._load_data()
        
        recommendations = [
            {
                "category": "format",
                "tip": "Short videos under 60 seconds have highest viral potential",
                "score_impact": "+0.85 base"
            },
            {
                "category": "timing",
                "tip": f"Post during peak hours: {data['timing_insights']['best_hours']}",
                "score_impact": "+engagement"
            },
            {
                "category": "hook",
                "tip": "Lead with curiosity gap or surprising statement",
                "score_impact": "+0.15"
            },
            {
                "category": "emotion",
                "tip": "Include emotional trigger words",
                "score_impact": "+0.15"
            }
        ]
        
        return {"success": True, "recommendations": recommendations}
    
    def _get_stats(self, task: Dict) -> Dict:
        """Get viral analysis statistics."""
        data = self._load_data()
        
        return {
            "success": True,
            "stats": data["stats"],
            "active_tracking": len([t for t in data["content_tracked"] if t["status"] == "tracking"]),
            "viral_content": len([t for t in data["content_tracked"] if t["status"] == "viral"])
        }
