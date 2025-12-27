"""
AutomationBee - Handles dead air, playlist transitions, and failsafe triggers.

An Employed bee that ensures continuous broadcast by managing automated
playlist transitions and handling emergency fallback scenarios.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class AutomationBee:
    """
    AutomationBee - Broadcast continuity and automation.
    
    Responsibilities:
    - Detect and fill dead air gaps
    - Manage playlist transitions
    - Handle emergency failsafes
    - Schedule automated content
    - Monitor broadcast queue
    
    Outputs:
    - Automation logs
    - Failsafe triggers
    - Queue management
    - Transition events
    """
    
    BEE_TYPE = "employed"
    PRIORITY = "critical"
    
    # Dead air threshold (seconds)
    DEAD_AIR_THRESHOLD = 5
    
    # Failsafe content types
    FAILSAFE_TYPES = [
        "station_id",
        "promo",
        "filler_track",
        "emergency_playlist"
    ]
    
    def __init__(self, hive_path: Optional[str] = None):
        """Initialize AutomationBee."""
        if hive_path is None:
            hive_path = Path(__file__).parent.parent.parent
        self.hive_path = Path(hive_path)
        self.honeycomb_path = self.hive_path / "honeycomb"
        
        # Automation data storage
        self.automation_path = self.honeycomb_path / "automation.json"
        self._ensure_automation_file()
    
    def _ensure_automation_file(self) -> None:
        """Ensure automation data file exists."""
        if not self.automation_path.exists():
            initial_data = {
                "queue": [],
                "failsafe_content": {},
                "schedule": [],
                "logs": [],
                "current_state": "normal",
                "last_check": None
            }
            with open(self.automation_path, 'w') as f:
                json.dump(initial_data, f, indent=2)
    
    def _load_automation(self) -> Dict[str, Any]:
        """Load automation data."""
        with open(self.automation_path, 'r') as f:
            return json.load(f)
    
    def _save_automation(self, data: Dict[str, Any]) -> None:
        """Save automation data."""
        with open(self.automation_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _log_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log an automation event."""
        data = self._load_automation()
        data["logs"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "details": details
        })
        # Keep last 1000 logs
        data["logs"] = data["logs"][-1000:]
        self._save_automation(data)

    
    def run(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute automation task.
        
        Actions:
        - check: Check broadcast status
        - fill_gap: Fill dead air gap
        - queue_content: Add to automation queue
        - schedule: Schedule automated content
        - failsafe: Trigger failsafe mode
        - recover: Recover from failsafe
        - get_status: Get automation status
        - get_logs: Get recent logs
        """
        if task is None:
            task = {}
        
        action = task.get("action", "check")
        
        actions = {
            "check": self._check_broadcast,
            "fill_gap": self._fill_gap,
            "queue_content": self._queue_content,
            "schedule": self._schedule_content,
            "failsafe": self._trigger_failsafe,
            "recover": self._recover_from_failsafe,
            "get_status": self._get_status,
            "get_stats": self._get_stats,
            "get_logs": self._get_logs,
            "add_failsafe_content": self._add_failsafe_content
        }
        
        handler = actions.get(action)
        if handler:
            return handler(task)
        
        return {"error": f"Unknown action: {action}"}
    
    def _check_broadcast(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Check broadcast status for issues."""
        data = self._load_automation()
        
        # Get current stream state (would integrate with StreamMonitorBee)
        state_path = self.honeycomb_path / "state.json"
        stream_health = {}
        if state_path.exists():
            with open(state_path, 'r') as f:
                state = json.load(f)
                stream_health = state.get("health", {})
        
        # Check for issues
        issues = []
        current_state = "normal"
        
        # Check audio level
        audio_level = stream_health.get("audio_level", -20)
        if audio_level < -50:
            issues.append({
                "type": "low_audio",
                "severity": "warning",
                "value": audio_level
            })
        
        # Check for silence (dead air)
        silence_duration = stream_health.get("silence_duration", 0)
        if silence_duration >= self.DEAD_AIR_THRESHOLD:
            issues.append({
                "type": "dead_air",
                "severity": "critical",
                "duration": silence_duration
            })
            current_state = "dead_air"
        
        # Check queue health
        queue = data.get("queue", [])
        if len(queue) < 2:
            issues.append({
                "type": "low_queue",
                "severity": "warning",
                "items": len(queue)
            })
        
        # Update state
        data["current_state"] = current_state
        data["last_check"] = datetime.now(timezone.utc).isoformat()
        self._save_automation(data)
        
        # Log if issues
        if issues:
            self._log_event("check_issues", {"issues": issues})
        
        return {
            "success": True,
            "state": current_state,
            "issues": issues,
            "queue_depth": len(queue),
            "checked_at": data["last_check"]
        }
    
    def _fill_gap(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Fill a dead air gap with content."""
        data = self._load_automation()
        failsafe_content = data.get("failsafe_content", {})
        
        # Determine what to play
        gap_type = task.get("gap_type", "short")  # short, medium, long
        
        content_to_play = None
        
        if gap_type == "short":
            # Play station ID or short promo
            content_to_play = failsafe_content.get("station_id") or {
                "type": "station_id",
                "duration": 10,
                "file": "default_station_id.mp3"
            }
        elif gap_type == "medium":
            # Play a promo or filler
            content_to_play = failsafe_content.get("promo") or {
                "type": "promo",
                "duration": 30,
                "file": "default_promo.mp3"
            }
        else:
            # Play emergency playlist
            content_to_play = failsafe_content.get("emergency_playlist") or {
                "type": "emergency_playlist",
                "duration": 300,
                "playlist": "emergency_mix"
            }
        
        # Log the fill event
        self._log_event("gap_filled", {
            "gap_type": gap_type,
            "content": content_to_play
        })
        
        return {
            "success": True,
            "action": "playing",
            "content": content_to_play,
            "gap_type": gap_type
        }

    
    def _queue_content(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Add content to the automation queue."""
        content = task.get("content")
        if not content:
            return {"error": "content required"}
        
        position = task.get("position", "end")  # start, end, or index
        
        data = self._load_automation()
        queue = data.get("queue", [])
        
        queue_item = {
            "id": f"q_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "content": content,
            "added_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
            "priority": task.get("priority", "normal")
        }
        
        if position == "start":
            queue.insert(0, queue_item)
        elif isinstance(position, int):
            queue.insert(position, queue_item)
        else:
            queue.append(queue_item)
        
        data["queue"] = queue
        self._save_automation(data)
        
        self._log_event("content_queued", {"item": queue_item})
        
        return {
            "success": True,
            "queued": queue_item,
            "queue_position": queue.index(queue_item),
            "total_queue": len(queue)
        }
    
    def _schedule_content(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule content for future automated playback."""
        content = task.get("content")
        scheduled_time = task.get("scheduled_time")
        repeat = task.get("repeat", "once")  # once, daily, weekly
        
        if not content or not scheduled_time:
            return {"error": "content and scheduled_time required"}
        
        data = self._load_automation()
        schedule = data.get("schedule", [])
        
        scheduled_item = {
            "id": f"sch_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "content": content,
            "scheduled_time": scheduled_time,
            "repeat": repeat,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "active"
        }
        
        schedule.append(scheduled_item)
        data["schedule"] = schedule
        self._save_automation(data)
        
        self._log_event("content_scheduled", {"item": scheduled_item})
        
        return {
            "success": True,
            "scheduled": scheduled_item,
            "total_scheduled": len(schedule)
        }
    
    def _trigger_failsafe(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger failsafe mode."""
        reason = task.get("reason", "unknown")
        
        data = self._load_automation()
        data["current_state"] = "failsafe"
        data["failsafe_triggered_at"] = datetime.now(timezone.utc).isoformat()
        data["failsafe_reason"] = reason
        self._save_automation(data)
        
        # Log critical event
        self._log_event("failsafe_triggered", {
            "reason": reason,
            "timestamp": data["failsafe_triggered_at"]
        })
        
        # Return failsafe content to play
        failsafe_content = data.get("failsafe_content", {})
        emergency_playlist = failsafe_content.get("emergency_playlist", {
            "type": "emergency_playlist",
            "duration": 3600,
            "playlist": "emergency_backup"
        })
        
        return {
            "success": True,
            "state": "failsafe",
            "reason": reason,
            "playing": emergency_playlist,
            "alert_sent": True
        }
    
    def _recover_from_failsafe(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Recover from failsafe mode."""
        data = self._load_automation()
        
        if data.get("current_state") != "failsafe":
            return {
                "success": False,
                "error": "Not in failsafe mode",
                "current_state": data.get("current_state")
            }
        
        # Calculate failsafe duration
        triggered_at = data.get("failsafe_triggered_at")
        duration = None
        if triggered_at:
            try:
                triggered = datetime.fromisoformat(triggered_at.replace('Z', '+00:00'))
                duration = (datetime.now(timezone.utc) - triggered).total_seconds()
            except:
                pass
        
        data["current_state"] = "normal"
        data["failsafe_recovered_at"] = datetime.now(timezone.utc).isoformat()
        self._save_automation(data)
        
        self._log_event("failsafe_recovered", {
            "duration_seconds": duration,
            "recovered_at": data["failsafe_recovered_at"]
        })
        
        return {
            "success": True,
            "state": "normal",
            "failsafe_duration_seconds": duration,
            "recovered_at": data["failsafe_recovered_at"]
        }
    
    def _add_failsafe_content(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Add or update failsafe content."""
        content_type = task.get("content_type")
        content = task.get("content")
        
        if content_type not in self.FAILSAFE_TYPES:
            return {
                "error": f"Invalid content_type. Must be one of: {self.FAILSAFE_TYPES}"
            }
        
        if not content:
            return {"error": "content required"}
        
        data = self._load_automation()
        if "failsafe_content" not in data:
            data["failsafe_content"] = {}
        
        data["failsafe_content"][content_type] = content
        self._save_automation(data)
        
        return {
            "success": True,
            "content_type": content_type,
            "content": content,
            "failsafe_types_configured": list(data["failsafe_content"].keys())
        }
    
    def _get_status(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get current automation status."""
        data = self._load_automation()
        
        return {
            "success": True,
            "current_state": data.get("current_state", "unknown"),
            "queue_depth": len(data.get("queue", [])),
            "scheduled_items": len(data.get("schedule", [])),
            "failsafe_types_configured": list(data.get("failsafe_content", {}).keys()),
            "last_check": data.get("last_check"),
            "failsafe_triggered_at": data.get("failsafe_triggered_at"),
            "recent_events": len(data.get("logs", []))
        }
    
    def _get_logs(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get recent automation logs."""
        limit = task.get("limit", 50)
        event_type = task.get("event_type")
        
        data = self._load_automation()
        logs = data.get("logs", [])
        
        if event_type:
            logs = [l for l in logs if l.get("event_type") == event_type]
        
        # Return most recent
        logs = logs[-limit:]
        logs.reverse()
        
        return {
            "success": True,
            "logs": logs,
            "total_logs": len(data.get("logs", [])),
            "filtered_by": event_type
        }
    
    def _get_stats(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get automation statistics."""
        data = self._load_automation()
        logs = data.get("logs", [])
        
        # Count events by type
        event_counts = {}
        for log in logs:
            evt = log.get("event_type", "unknown")
            event_counts[evt] = event_counts.get(evt, 0) + 1
        
        # Calculate uptime metrics
        failsafe_events = [l for l in logs if l.get("event_type") == "failsafe_triggered"]
        recovery_events = [l for l in logs if l.get("event_type") == "failsafe_recovered"]
        
        return {
            "success": True,
            "bee_type": self.BEE_TYPE,
            "priority": self.PRIORITY,
            "current_state": data.get("current_state", "unknown"),
            "queue_depth": len(data.get("queue", [])),
            "scheduled_items": len(data.get("schedule", [])),
            "failsafe_content_types": list(data.get("failsafe_content", {}).keys()),
            "total_events": len(logs),
            "event_breakdown": event_counts,
            "failsafe_count": len(failsafe_events),
            "recovery_count": len(recovery_events),
            "last_check": data.get("last_check")
        }
    
    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """BaseBee-compatible work method - delegates to run()."""
        return self.run(task)
