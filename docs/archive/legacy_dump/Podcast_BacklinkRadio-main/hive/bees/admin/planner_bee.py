"""
Planner Bee - Content calendar and strategic planning.

The Planner Bee handles:
- Weekly/monthly content planning
- Seasonal theme coordination
- Cross-bee task orchestration
- Goal tracking and milestones
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_bee import OnlookerBee


class PlannerBee(OnlookerBee):
    """
    Planner Bee - Strategic content planning.
    
    Features:
    - Create and manage content calendar
    - Set weekly/monthly themes
    - Track goals and milestones
    - Coordinate cross-bee initiatives
    """
    
    BEE_TYPE = "planner"
    BEE_NAME = "Content Planner"
    CATEGORY = "admin"
    LINEAGE_VERSION = "1.0.0"
    
    # Planning horizons
    HORIZONS = ["daily", "weekly", "monthly", "quarterly"]
    
    def __init__(self, hive_path: Optional[str] = None, gateway: Any = None):
        """Initialize Planner Bee."""
        super().__init__(hive_path, gateway)
        self.calendar_file = self.honeycomb_path / "calendar.json"
        self._ensure_calendar_file()
    
    def _ensure_calendar_file(self):
        """Ensure calendar.json exists."""
        if not self.calendar_file.exists():
            initial = {
                "_meta": {
                    "created": datetime.now(timezone.utc).isoformat(),
                    "version": "1.0.0"
                },
                "themes": {
                    "weekly": {},
                    "monthly": {},
                    "seasonal": []
                },
                "events": [],
                "goals": [],
                "milestones": []
            }
            with open(self.calendar_file, 'w') as f:
                json.dump(initial, f, indent=2)
    
    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process planning tasks.
        
        Actions:
        - plan_week: Generate weekly plan
        - set_theme: Set a theme for a period
        - add_event: Add calendar event
        - set_goal: Set a goal with milestones
        - review: Review current period status
        """
        action = "review"
        if task and "payload" in task:
            action = task["payload"].get("action", "review")
        
        if action == "plan_week":
            return self._plan_week(task.get("payload", {}) if task else {})
        elif action == "set_theme":
            return self._set_theme(task["payload"])
        elif action == "add_event":
            return self._add_event(task["payload"])
        elif action == "set_goal":
            return self._set_goal(task["payload"])
        elif action == "review":
            return self._review_period(task.get("payload", {}) if task else {})
        else:
            return {"error": f"Unknown action: {action}"}
    
    def _load_calendar(self) -> Dict[str, Any]:
        """Load calendar data."""
        with open(self.calendar_file, 'r') as f:
            return json.load(f)
    
    def _save_calendar(self, data: Dict[str, Any]) -> None:
        """Save calendar data."""
        data["_meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.calendar_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _plan_week(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a weekly content plan."""
        # Get current intel for planning context
        intel = self.read_intel()
        state = self.read_state()
        
        # Determine week boundaries
        today = datetime.now(timezone.utc)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        week_key = start_of_week.strftime("%Y-W%W")
        
        # Load calendar
        calendar = self._load_calendar()
        
        # Get current theme
        theme = calendar["themes"]["weekly"].get(week_key, {})
        monthly_theme = calendar["themes"]["monthly"].get(today.strftime("%Y-%m"), {})
        
        # Build weekly plan
        plan = {
            "week": week_key,
            "start_date": start_of_week.isoformat(),
            "end_date": end_of_week.isoformat(),
            "theme": theme.get("name", monthly_theme.get("name", "General")),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "days": {}
        }
        
        # Plan each day
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for i, day_name in enumerate(day_names):
            day_date = start_of_week + timedelta(days=i)
            plan["days"][day_name] = {
                "date": day_date.strftime("%Y-%m-%d"),
                "content_focus": self._get_day_focus(day_name, theme),
                "scheduled_events": self._get_events_for_date(calendar, day_date),
                "suggested_tasks": self._suggest_tasks(day_name, intel)
            }
        
        # Get active goals for the week
        active_goals = [
            g for g in calendar["goals"]
            if g.get("status") == "active"
        ]
        plan["goals_in_progress"] = len(active_goals)
        
        return {
            "success": True,
            "plan": plan,
            "theme": plan["theme"],
            "events_count": sum(
                len(d["scheduled_events"]) for d in plan["days"].values()
            )
        }
    
    def _get_day_focus(self, day_name: str, theme: Dict) -> str:
        """Get content focus for a specific day."""
        # Default focuses by day
        focuses = {
            "Monday": "Motivation & Week Kickoff",
            "Tuesday": "Deep Dives & Education",
            "Wednesday": "Community Spotlight",
            "Thursday": "Throwback & Nostalgia",
            "Friday": "Fun & Weekend Preview",
            "Saturday": "Special Features",
            "Sunday": "Chill & Reflection"
        }
        
        # Override with theme-specific focus if available
        if theme and "day_focuses" in theme:
            return theme["day_focuses"].get(day_name, focuses.get(day_name, "General"))
        
        return focuses.get(day_name, "General")
    
    def _get_events_for_date(self, calendar: Dict, date: datetime) -> List[Dict]:
        """Get events scheduled for a specific date."""
        date_str = date.strftime("%Y-%m-%d")
        events = []
        
        for event in calendar["events"]:
            if event.get("date", "").startswith(date_str):
                events.append({
                    "title": event.get("title"),
                    "time": event.get("time"),
                    "type": event.get("type")
                })
        
        return events
    
    def _suggest_tasks(self, day_name: str, intel: Dict) -> List[str]:
        """Suggest tasks based on day and intel."""
        suggestions = []
        
        # Day-specific suggestions
        if day_name == "Monday":
            suggestions.append("Review weekend analytics")
            suggestions.append("Plan week's social content")
        elif day_name == "Wednesday":
            suggestions.append("Community shoutout compilation")
        elif day_name == "Friday":
            suggestions.append("Weekend playlist preparation")
        
        # Intel-based suggestions
        if intel.get("trends", {}).get("hot_topics"):
            suggestions.append("Create content around trending topic")
        
        return suggestions
    
    def _set_theme(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Set a theme for a time period."""
        period_type = payload.get("period_type", "weekly")  # weekly, monthly, seasonal
        period_key = payload.get("period_key")  # e.g., "2025-W01" or "2025-01"
        theme_name = payload.get("theme_name")
        
        if not period_key or not theme_name:
            return {"error": "Missing period_key or theme_name"}
        
        calendar = self._load_calendar()
        
        theme_data = {
            "name": theme_name,
            "description": payload.get("description", ""),
            "colors": payload.get("colors", []),
            "hashtags": payload.get("hashtags", []),
            "day_focuses": payload.get("day_focuses", {}),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        if period_type in ["weekly", "monthly"]:
            calendar["themes"][period_type][period_key] = theme_data
        elif period_type == "seasonal":
            calendar["themes"]["seasonal"].append({
                **theme_data,
                "period_key": period_key
            })
        
        self._save_calendar(calendar)
        
        self.log(f"Set {period_type} theme: {theme_name} for {period_key}")
        
        return {
            "success": True,
            "period_type": period_type,
            "period_key": period_key,
            "theme": theme_name
        }
    
    def _add_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Add an event to the calendar."""
        required = ["title", "date"]
        for field in required:
            if field not in payload:
                return {"error": f"Missing required field: {field}"}
        
        calendar = self._load_calendar()
        
        import hashlib
        event_id = hashlib.sha256(
            f"{payload['title']}:{payload['date']}".encode()
        ).hexdigest()[:12]
        
        event = {
            "id": event_id,
            "title": payload["title"],
            "date": payload["date"],
            "time": payload.get("time"),
            "type": payload.get("type", "general"),
            "description": payload.get("description", ""),
            "recurring": payload.get("recurring"),
            "notify_bees": payload.get("notify_bees", []),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        calendar["events"].append(event)
        self._save_calendar(calendar)
        
        return {
            "success": True,
            "event_id": event_id,
            "title": event["title"],
            "date": event["date"]
        }
    
    def _set_goal(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Set a goal with optional milestones."""
        required = ["title", "target_date"]
        for field in required:
            if field not in payload:
                return {"error": f"Missing required field: {field}"}
        
        calendar = self._load_calendar()
        
        import hashlib
        goal_id = hashlib.sha256(
            f"goal:{payload['title']}:{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:12]
        
        goal = {
            "id": goal_id,
            "title": payload["title"],
            "description": payload.get("description", ""),
            "target_date": payload["target_date"],
            "metric": payload.get("metric"),  # e.g., "listeners", "revenue"
            "target_value": payload.get("target_value"),
            "current_value": payload.get("current_value", 0),
            "milestones": payload.get("milestones", []),
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        calendar["goals"].append(goal)
        self._save_calendar(calendar)
        
        self.log(f"Set goal: {goal['title']} (target: {goal['target_date']})")
        
        return {
            "success": True,
            "goal_id": goal_id,
            "title": goal["title"],
            "target_date": goal["target_date"]
        }
    
    def _review_period(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Review current period status."""
        period = payload.get("period", "weekly")
        
        calendar = self._load_calendar()
        today = datetime.now(timezone.utc)
        
        review = {
            "timestamp": today.isoformat(),
            "period": period
        }
        
        if period == "weekly":
            week_key = today.strftime("%Y-W%W")
            review["period_key"] = week_key
            review["theme"] = calendar["themes"]["weekly"].get(week_key, {})
            
            # Count events this week
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            week_events = [
                e for e in calendar["events"]
                if start_of_week.strftime("%Y-%m-%d") <= e.get("date", "")[:10] <= end_of_week.strftime("%Y-%m-%d")
            ]
            review["events_this_period"] = len(week_events)
            
        elif period == "monthly":
            month_key = today.strftime("%Y-%m")
            review["period_key"] = month_key
            review["theme"] = calendar["themes"]["monthly"].get(month_key, {})
            
            # Count events this month
            month_events = [
                e for e in calendar["events"]
                if e.get("date", "")[:7] == month_key
            ]
            review["events_this_period"] = len(month_events)
        
        # Active goals
        active_goals = [g for g in calendar["goals"] if g.get("status") == "active"]
        review["active_goals"] = [
            {
                "id": g["id"],
                "title": g["title"],
                "target_date": g["target_date"],
                "progress": (
                    g.get("current_value", 0) / max(g.get("target_value", 1), 1)
                ) if g.get("target_value") else None
            }
            for g in active_goals
        ]
        
        # Upcoming events (next 7 days)
        next_week = today + timedelta(days=7)
        upcoming = [
            e for e in calendar["events"]
            if today.strftime("%Y-%m-%d") <= e.get("date", "")[:10] <= next_week.strftime("%Y-%m-%d")
        ]
        review["upcoming_events"] = sorted(upcoming, key=lambda x: x.get("date", ""))[:10]
        
        return review
