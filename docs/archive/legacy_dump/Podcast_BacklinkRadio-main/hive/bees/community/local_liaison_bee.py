"""
LocalLiaisonBee - Local Community Connection Bee

Connects with local businesses, events, and community organizations.
Builds partnerships and identifies local content opportunities.
"""

from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import json
import uuid

# Import base
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_bee import BaseBee


class LocalLiaisonBee(BaseBee):
    """
    Manages local community connections.
    
    Type: Scout bee
    Priority: Low
    Schedule: Weekly
    """
    
    BEE_TYPE = "local_liaison"
    BEE_NAME = "LocalLiaisonBee"
    CATEGORY = "community"
    LINEAGE_VERSION = "1.0.0"
    
    def __init__(self, hive_path: Optional[Path] = None):
        super().__init__(hive_path=hive_path)
        self.local_file = self.honeycomb_path / "local_connections.json"
        self._ensure_local_file()
    
    def _ensure_local_file(self):
        """Initialize local connections storage."""
        if not self.local_file.exists():
            initial = {
                "businesses": [],
                "events": [],
                "partnerships": [],
                "venues": [],
                "regions": [],
                "stats": {
                    "businesses_contacted": 0,
                    "active_partnerships": 0,
                    "events_tracked": 0
                }
            }
            self.local_file.write_text(json.dumps(initial, indent=2))
    
    def _load_data(self) -> Dict:
        return json.loads(self.local_file.read_text())
    
    def _save_data(self, data: Dict):
        self.local_file.write_text(json.dumps(data, indent=2))
    
    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Scan for local opportunities."""
        return self._scan_opportunities(task or {})
    
    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute local liaison tasks."""
        action = task.get("action", "list_businesses")
        
        actions = {
            "add_business": self._add_business,
            "list_businesses": self._list_businesses,
            "add_event": self._add_event,
            "list_events": self._list_events,
            "create_partnership": self._create_partnership,
            "list_partnerships": self._list_partnerships,
            "add_venue": self._add_venue,
            "list_venues": self._list_venues,
            "add_region": self._add_region,
            "scan_opportunities": self._scan_opportunities,
            "get_stats": self._get_stats
        }
        
        if action not in actions:
            return {"error": f"Unknown action: {action}"}
        
        return self.safe_action(actions[action], task)
    
    def _add_business(self, task: Dict) -> Dict:
        """Add a local business contact."""
        data = self._load_data()
        
        business = {
            "id": str(uuid.uuid4())[:8],
            "name": task.get("name"),
            "type": task.get("type"),  # restaurant, venue, shop, service
            "location": task.get("location"),
            "contact": task.get("contact"),
            "website": task.get("website"),
            "notes": task.get("notes", ""),
            "status": "prospect",  # prospect, contacted, partner, inactive
            "added_at": datetime.now(timezone.utc).isoformat()
        }
        
        data["businesses"].append(business)
        data["stats"]["businesses_contacted"] += 1
        self._save_data(data)
        
        return {"success": True, "business": business}
    
    def _list_businesses(self, task: Dict) -> Dict:
        """List local businesses."""
        data = self._load_data()
        businesses = data["businesses"]
        
        status = task.get("status")
        business_type = task.get("type")
        
        if status:
            businesses = [b for b in businesses if b["status"] == status]
        if business_type:
            businesses = [b for b in businesses if b["type"] == business_type]
        
        return {
            "success": True,
            "count": len(businesses),
            "businesses": businesses
        }
    
    def _add_event(self, task: Dict) -> Dict:
        """Add a local event."""
        data = self._load_data()
        
        event = {
            "id": str(uuid.uuid4())[:8],
            "name": task.get("name"),
            "type": task.get("type"),  # concert, festival, fair, conference
            "date": task.get("date"),
            "location": task.get("location"),
            "venue_id": task.get("venue_id"),
            "description": task.get("description", ""),
            "opportunity_type": task.get("opportunity_type"),  # coverage, partnership, booth
            "status": "identified",
            "added_at": datetime.now(timezone.utc).isoformat()
        }
        
        data["events"].append(event)
        data["stats"]["events_tracked"] += 1
        self._save_data(data)
        
        return {"success": True, "event": event}
    
    def _list_events(self, task: Dict) -> Dict:
        """List local events."""
        data = self._load_data()
        events = data["events"]
        
        status = task.get("status")
        if status:
            events = [e for e in events if e["status"] == status]
        
        return {
            "success": True,
            "count": len(events),
            "events": events
        }
    
    def _create_partnership(self, task: Dict) -> Dict:
        """Create a local partnership."""
        data = self._load_data()
        
        partnership = {
            "id": str(uuid.uuid4())[:8],
            "business_id": task.get("business_id"),
            "business_name": task.get("business_name"),
            "type": task.get("type"),  # sponsor, cross-promo, venue, content
            "terms": task.get("terms", ""),
            "value": task.get("value", 0),
            "start_date": task.get("start_date"),
            "end_date": task.get("end_date"),
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        data["partnerships"].append(partnership)
        data["stats"]["active_partnerships"] = len([p for p in data["partnerships"] if p["status"] == "active"])
        
        # Update business status
        for business in data["businesses"]:
            if business["id"] == partnership["business_id"]:
                business["status"] = "partner"
        
        self._save_data(data)
        
        return {"success": True, "partnership": partnership}
    
    def _list_partnerships(self, task: Dict) -> Dict:
        """List partnerships."""
        data = self._load_data()
        partnerships = data["partnerships"]
        
        status = task.get("status", "active")
        if status:
            partnerships = [p for p in partnerships if p["status"] == status]
        
        return {
            "success": True,
            "count": len(partnerships),
            "partnerships": partnerships
        }
    
    def _add_venue(self, task: Dict) -> Dict:
        """Add a venue for potential broadcasts."""
        data = self._load_data()
        
        venue = {
            "id": str(uuid.uuid4())[:8],
            "name": task.get("name"),
            "type": task.get("type"),  # bar, club, theater, outdoor
            "capacity": task.get("capacity"),
            "location": task.get("location"),
            "contact": task.get("contact"),
            "tech_specs": task.get("tech_specs", {}),
            "status": "available",
            "added_at": datetime.now(timezone.utc).isoformat()
        }
        
        data["venues"].append(venue)
        self._save_data(data)
        
        return {"success": True, "venue": venue}
    
    def _list_venues(self, task: Dict) -> Dict:
        """List venues."""
        data = self._load_data()
        venues = data["venues"]
        
        venue_type = task.get("type")
        if venue_type:
            venues = [v for v in venues if v["type"] == venue_type]
        
        return {
            "success": True,
            "count": len(venues),
            "venues": venues
        }
    
    def _add_region(self, task: Dict) -> Dict:
        """Add a target region."""
        data = self._load_data()
        
        region = {
            "id": str(uuid.uuid4())[:8],
            "name": task.get("name"),
            "city": task.get("city"),
            "state": task.get("state"),
            "country": task.get("country", "USA"),
            "priority": task.get("priority", "medium"),
            "notes": task.get("notes", ""),
            "added_at": datetime.now(timezone.utc).isoformat()
        }
        
        data["regions"].append(region)
        self._save_data(data)
        
        return {"success": True, "region": region}
    
    def _scan_opportunities(self, task: Dict) -> Dict:
        """Scan for local opportunities."""
        data = self._load_data()
        
        opportunities = []
        
        # Prospect businesses
        prospects = [b for b in data["businesses"] if b["status"] == "prospect"]
        if prospects:
            opportunities.append({
                "type": "business_outreach",
                "count": len(prospects),
                "message": f"{len(prospects)} businesses to contact"
            })
        
        # Upcoming events
        upcoming = [e for e in data["events"] if e["status"] == "identified"]
        if upcoming:
            opportunities.append({
                "type": "event_opportunity",
                "count": len(upcoming),
                "message": f"{len(upcoming)} events to evaluate"
            })
        
        # Available venues
        venues = [v for v in data["venues"] if v["status"] == "available"]
        if venues:
            opportunities.append({
                "type": "venue_booking",
                "count": len(venues),
                "message": f"{len(venues)} venues available"
            })
        
        return {
            "success": True,
            "opportunities": opportunities,
            "total": len(opportunities)
        }
    
    def _get_stats(self, task: Dict) -> Dict:
        """Get local liaison statistics."""
        data = self._load_data()
        
        return {
            "success": True,
            "stats": {
                **data["stats"],
                "total_businesses": len(data["businesses"]),
                "total_venues": len(data["venues"]),
                "regions_tracked": len(data["regions"])
            }
        }
