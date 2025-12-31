"""
CompetitorWatchBee - Competitive Intelligence Bee

Monitors competing stations, podcasts, and media outlets.
Identifies opportunities and tracks market positioning.
"""

from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import json

# Import base
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_bee import BaseBee


class CompetitorWatchBee(BaseBee):
    """
    Monitors competitive landscape.
    
    Type: Scout bee
    Priority: Low
    Schedule: Daily
    """
    
    BEE_TYPE = "competitor_watch"
    BEE_NAME = "CompetitorWatchBee"
    CATEGORY = "research"
    LINEAGE_VERSION = "1.0.0"
    
    def __init__(self, hive_path: Optional[Path] = None):
        super().__init__(hive_path=hive_path)
        self.intel_file = self.honeycomb_path / "competitor_intel.json"
        self._ensure_intel_file()
    
    def _ensure_intel_file(self):
        """Initialize competitor intel storage."""
        if not self.intel_file.exists():
            initial = {
                "competitors": [],
                "opportunities": [],
                "market_trends": [],
                "last_scan": None,
                "stats": {
                    "total_scans": 0,
                    "competitors_tracked": 0,
                    "opportunities_found": 0
                }
            }
            self.intel_file.write_text(json.dumps(initial, indent=2))
    
    def _load_intel(self) -> Dict:
        return json.loads(self.intel_file.read_text())
    
    def _save_intel(self, data: Dict):
        self.intel_file.write_text(json.dumps(data, indent=2))
    
    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Daily competitor scan."""
        return self._scan_competitors(task or {})
    
    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute competitor watch tasks."""
        action = task.get("action", "scan")
        
        actions = {
            "scan": self._scan_competitors,
            "add_competitor": self._add_competitor,
            "remove_competitor": self._remove_competitor,
            "list": self._list_competitors,
            "analyze": self._analyze_competitor,
            "opportunities": self._get_opportunities,
            "add_opportunity": self._add_opportunity,
            "trends": self._get_trends,
            "get_stats": self._get_stats
        }
        
        if action not in actions:
            return {"error": f"Unknown action: {action}"}
        
        return self.safe_action(actions[action], task)
    
    def _add_competitor(self, task: Dict) -> Dict:
        """Add a competitor to track."""
        data = self._load_intel()
        
        competitor = {
            "id": task.get("id", task.get("name", "").lower().replace(" ", "_")),
            "name": task.get("name"),
            "type": task.get("type", "radio"),  # radio, podcast, streaming
            "url": task.get("url"),
            "platforms": task.get("platforms", []),
            "strengths": task.get("strengths", []),
            "weaknesses": task.get("weaknesses", []),
            "audience_size": task.get("audience_size"),
            "notes": task.get("notes", ""),
            "added_at": datetime.now(timezone.utc).isoformat(),
            "last_analyzed": None
        }
        
        # Check for duplicate
        existing = [c for c in data["competitors"] if c["id"] == competitor["id"]]
        if existing:
            return {"error": f"Competitor already exists: {competitor['id']}"}
        
        data["competitors"].append(competitor)
        data["stats"]["competitors_tracked"] = len(data["competitors"])
        self._save_intel(data)
        
        return {"success": True, "competitor": competitor}
    
    def _remove_competitor(self, task: Dict) -> Dict:
        """Remove a competitor from tracking."""
        competitor_id = task.get("competitor_id")
        data = self._load_intel()
        
        original_count = len(data["competitors"])
        data["competitors"] = [c for c in data["competitors"] if c["id"] != competitor_id]
        
        if len(data["competitors"]) == original_count:
            return {"error": f"Competitor not found: {competitor_id}"}
        
        data["stats"]["competitors_tracked"] = len(data["competitors"])
        self._save_intel(data)
        
        return {"success": True, "message": f"Removed competitor: {competitor_id}"}
    
    def _list_competitors(self, task: Dict) -> Dict:
        """List tracked competitors."""
        data = self._load_intel()
        
        comp_type = task.get("type")
        competitors = data["competitors"]
        
        if comp_type:
            competitors = [c for c in competitors if c["type"] == comp_type]
        
        return {
            "success": True,
            "count": len(competitors),
            "competitors": competitors
        }
    
    def _scan_competitors(self, task: Dict) -> Dict:
        """Scan all competitors for updates."""
        data = self._load_intel()
        
        scan_results = []
        for competitor in data["competitors"]:
            # Simulated scan - would integrate with real APIs
            result = {
                "competitor_id": competitor["id"],
                "name": competitor["name"],
                "status": "active",
                "recent_activity": [],
                "scanned_at": datetime.now(timezone.utc).isoformat()
            }
            scan_results.append(result)
            competitor["last_analyzed"] = result["scanned_at"]
        
        data["last_scan"] = datetime.now(timezone.utc).isoformat()
        data["stats"]["total_scans"] += 1
        self._save_intel(data)
        
        return {
            "success": True,
            "scanned_count": len(scan_results),
            "results": scan_results
        }
    
    def _analyze_competitor(self, task: Dict) -> Dict:
        """Deep analysis of a specific competitor."""
        competitor_id = task.get("competitor_id")
        data = self._load_intel()
        
        competitor = next((c for c in data["competitors"] if c["id"] == competitor_id), None)
        if not competitor:
            return {"error": f"Competitor not found: {competitor_id}"}
        
        analysis = {
            "competitor": competitor,
            "swot": {
                "strengths": competitor.get("strengths", []),
                "weaknesses": competitor.get("weaknesses", []),
                "opportunities": [],
                "threats": []
            },
            "recommendations": [
                "Monitor content strategy",
                "Track audience growth",
                "Identify partnership opportunities"
            ],
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }
        
        competitor["last_analyzed"] = analysis["analyzed_at"]
        self._save_intel(data)
        
        return {"success": True, "analysis": analysis}
    
    def _add_opportunity(self, task: Dict) -> Dict:
        """Add a competitive opportunity."""
        data = self._load_intel()
        
        opportunity = {
            "id": f"opp_{len(data['opportunities']) + 1}",
            "title": task.get("title"),
            "description": task.get("description"),
            "source": task.get("source"),
            "priority": task.get("priority", "medium"),
            "status": "identified",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        data["opportunities"].append(opportunity)
        data["stats"]["opportunities_found"] = len(data["opportunities"])
        self._save_intel(data)
        
        return {"success": True, "opportunity": opportunity}
    
    def _get_opportunities(self, task: Dict) -> Dict:
        """Get identified opportunities."""
        data = self._load_intel()
        
        status = task.get("status")
        opportunities = data["opportunities"]
        
        if status:
            opportunities = [o for o in opportunities if o["status"] == status]
        
        return {
            "success": True,
            "count": len(opportunities),
            "opportunities": opportunities
        }
    
    def _get_trends(self, task: Dict) -> Dict:
        """Get market trends."""
        data = self._load_intel()
        
        return {
            "success": True,
            "trends": data["market_trends"],
            "last_scan": data["last_scan"]
        }
    
    def _get_stats(self, task: Dict) -> Dict:
        """Get competitor watch statistics."""
        data = self._load_intel()
        
        return {
            "success": True,
            "stats": data["stats"],
            "last_scan": data["last_scan"]
        }
