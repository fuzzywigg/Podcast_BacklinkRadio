"""
Queen Orchestrator - Central coordinator for the hive.

The Queen doesn't micromanage. She:
1. Wakes bees on schedules (cron-like)
2. Wakes bees on events (triggers)
3. Monitors hive health
4. Balances workload

The Queen is the heartbeat of the operation.
"""

import json
import time
import importlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
import threading
import queue


class QueenOrchestrator:
    """
    The Queen - orchestrates the entire hive operation.

    Manages bee scheduling, event handling, and overall
    hive coordination without micromanaging individual bees.
    """

    def __init__(self, hive_path: Optional[str] = None):
        """Initialize the Queen."""
        if hive_path is None:
            hive_path = Path(__file__).parent.parent
        self.hive_path = Path(hive_path)
        self.honeycomb_path = self.hive_path / "honeycomb"

        # Registered bees
        self.bee_registry: Dict[str, Type] = {}

        # Event queue
        self.event_queue: queue.Queue = queue.Queue()

        # State
        self.running = False
        self.last_heartbeat = None

        # Load configuration
        self.config = self._load_config()

        # Register default bees
        self._register_default_bees()

    def _load_config(self) -> Dict[str, Any]:
        """Load hive configuration."""
        config_path = self.hive_path / "config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Default hive configuration."""
        return {
            "heartbeat_interval_seconds": 60,
            "max_concurrent_bees": 10,
            "schedules": {
                "trend_scout": {"interval_minutes": 60, "enabled": True},
                "listener_intel": {"interval_minutes": 5, "enabled": True},
                "stream_monitor": {"interval_minutes": 1, "enabled": True},
                "social_poster": {"interval_minutes": 15, "enabled": True},
                "show_prep": {"interval_minutes": 30, "enabled": True},
                "sponsor_hunter": {"interval_minutes": 1440, "enabled": True}  # Daily
            },
            "event_triggers": {
                "donation": ["engagement", "social_poster"],
                "mention": ["engagement", "listener_intel"],
                "trend_alert": ["show_prep", "social_poster"],
                "vip_detected": ["engagement"]
            }
        }

    def _register_default_bees(self) -> None:
        """Register all default bee types."""

        # Import and register bees
        bee_mappings = {
            "show_prep": ("bees.content.show_prep_bee", "ShowPrepBee"),
            "clip_cutter": ("bees.content.clip_cutter_bee", "ClipCutterBee"),
            "trend_scout": ("bees.research.trend_scout_bee", "TrendScoutBee"),
            "listener_intel": ("bees.research.listener_intel_bee", "ListenerIntelBee"),
            "social_poster": ("bees.marketing.social_poster_bee", "SocialPosterBee"),
            "sponsor_hunter": ("bees.monetization.sponsor_hunter_bee", "SponsorHunterBee"),
            "engagement": ("bees.community.engagement_bee", "EngagementBee"),
            "stream_monitor": ("bees.technical.stream_monitor_bee", "StreamMonitorBee")
        }

        for bee_type, (module_path, class_name) in bee_mappings.items():
            try:
                # Dynamic import
                full_path = f"hive.{module_path}"
                # For now, just store the mapping - actual import happens when spawning
                self.bee_registry[bee_type] = (module_path, class_name)
            except Exception as e:
                self.log(f"Failed to register {bee_type}: {e}", level="warning")

    def register_bee(self, bee_type: str, bee_class: Type) -> None:
        """Register a bee type."""
        self.bee_registry[bee_type] = bee_class
        self.log(f"Registered bee type: {bee_type}")

    def spawn_bee(self, bee_type: str, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Spawn a bee to do work."""

        if bee_type not in self.bee_registry:
            return {"error": f"Unknown bee type: {bee_type}"}

        self.log(f"Spawning {bee_type} bee...")

        try:
            # Get bee class info
            bee_info = self.bee_registry[bee_type]

            if isinstance(bee_info, tuple):
                # Dynamic import
                module_path, class_name = bee_info
                # Construct import path relative to hive
                import sys
                bees_path = str(self.hive_path / "bees")
                if bees_path not in sys.path:
                    sys.path.insert(0, bees_path)

                # Import the specific module
                if "content" in module_path:
                    if "show_prep" in module_path:
                        from content.show_prep_bee import ShowPrepBee as BeeClass
                    elif "clip_cutter" in module_path:
                        from content.clip_cutter_bee import ClipCutterBee as BeeClass
                elif "research" in module_path:
                    if "trend_scout" in module_path:
                        from research.trend_scout_bee import TrendScoutBee as BeeClass
                    elif "listener_intel" in module_path:
                        from research.listener_intel_bee import ListenerIntelBee as BeeClass
                elif "marketing" in module_path:
                    from marketing.social_poster_bee import SocialPosterBee as BeeClass
                elif "monetization" in module_path:
                    from monetization.sponsor_hunter_bee import SponsorHunterBee as BeeClass
                elif "community" in module_path:
                    from community.engagement_bee import EngagementBee as BeeClass
                elif "technical" in module_path:
                    from technical.stream_monitor_bee import StreamMonitorBee as BeeClass
                else:
                    return {"error": f"Cannot import bee: {bee_type}"}
            else:
                BeeClass = bee_info

            # Instantiate and run
            bee = BeeClass(hive_path=self.hive_path)
            result = bee.run(task)

            return result

        except Exception as e:
            self.log(f"Error spawning {bee_type}: {e}", level="error")
            return {"error": str(e)}

    def trigger_event(self, event_type: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Trigger an event that may wake multiple bees."""

        self.log(f"Event triggered: {event_type}")

        triggers = self.config.get("event_triggers", {})
        bees_to_wake = triggers.get(event_type, [])

        results = []
        for bee_type in bees_to_wake:
            task = {
                "triggered_by": event_type,
                "payload": data
            }
            result = self.spawn_bee(bee_type, task)
            results.append({
                "bee_type": bee_type,
                "result": result
            })

        return results

    def run_schedule(self) -> Dict[str, Any]:
        """Run scheduled bee tasks."""

        now = datetime.now(timezone.utc)
        schedules = self.config.get("schedules", {})

        # Track which bees were run
        bees_run = []

        # Read last run times
        state = self._read_state()
        last_runs = state.get("scheduler", {}).get("last_runs", {})

        for bee_type, schedule in schedules.items():
            if not schedule.get("enabled", True):
                continue

            interval_minutes = schedule.get("interval_minutes", 60)
            last_run = last_runs.get(bee_type)

            should_run = False
            if last_run is None:
                should_run = True
            else:
                last_run_dt = datetime.fromisoformat(last_run.replace('Z', '+00:00'))
                minutes_since = (now - last_run_dt).total_seconds() / 60
                should_run = minutes_since >= interval_minutes

            if should_run:
                result = self.spawn_bee(bee_type)
                bees_run.append({
                    "bee_type": bee_type,
                    "result": result
                })
                last_runs[bee_type] = now.isoformat()

        # Update last run times
        self._update_state({
            "scheduler": {
                "last_runs": last_runs,
                "last_schedule_check": now.isoformat()
            }
        })

        return {
            "checked_at": now.isoformat(),
            "bees_run": len(bees_run),
            "results": bees_run
        }

    def process_task_queue(self) -> Dict[str, Any]:
        """Process pending tasks from the task queue."""

        tasks = self._read_tasks()
        pending = tasks.get("pending", [])

        if not pending:
            return {"processed": 0}

        processed = []
        for task in pending[:5]:  # Process up to 5 tasks per cycle
            bee_type = task.get("bee_type")
            if bee_type:
                result = self.spawn_bee(bee_type, task)
                processed.append({
                    "task_id": task.get("id"),
                    "bee_type": bee_type,
                    "result": result
                })

        return {
            "processed": len(processed),
            "results": processed
        }

    def heartbeat(self) -> Dict[str, Any]:
        """Perform a heartbeat check - the Queen's pulse."""

        now = datetime.now(timezone.utc)
        self.last_heartbeat = now

        status = {
            "timestamp": now.isoformat(),
            "queen_status": "alive",
            "registered_bees": list(self.bee_registry.keys()),
            "hive_health": self._check_hive_health()
        }

        # Update state
        self._update_state({
            "queen": {
                "last_heartbeat": now.isoformat(),
                "status": "alive"
            }
        })

        return status

    def _check_hive_health(self) -> Dict[str, Any]:
        """Check overall hive health."""

        state = self._read_state()
        tasks = self._read_tasks()

        return {
            "broadcast_status": state.get("broadcast", {}).get("status", "unknown"),
            "pending_tasks": len(tasks.get("pending", [])),
            "in_progress_tasks": len(tasks.get("in_progress", [])),
            "failed_tasks": len(tasks.get("failed", [])),
            "alerts_pending": len(state.get("alerts", {}).get("priority", []))
        }

    def run(self, once: bool = False) -> None:
        """
        Run the Queen's main loop.

        Args:
            once: If True, run one cycle and exit. If False, run continuously.
        """
        self.running = True
        self.log("Queen is online. Hive is active.")

        while self.running:
            try:
                # Heartbeat
                self.heartbeat()

                # Run scheduled tasks
                schedule_result = self.run_schedule()
                if schedule_result.get("bees_run", 0) > 0:
                    self.log(f"Scheduled {schedule_result['bees_run']} bees")

                # Process task queue
                queue_result = self.process_task_queue()
                if queue_result.get("processed", 0) > 0:
                    self.log(f"Processed {queue_result['processed']} queued tasks")

                if once:
                    break

                # Wait for next cycle
                interval = self.config.get("heartbeat_interval_seconds", 60)
                time.sleep(interval)

            except KeyboardInterrupt:
                self.log("Queen shutting down...")
                self.running = False
            except Exception as e:
                self.log(f"Error in main loop: {e}", level="error")
                if once:
                    break
                time.sleep(5)  # Brief pause before retry

        self.log("Queen is offline.")

    def stop(self) -> None:
        """Stop the Queen."""
        self.running = False

    # ─────────────────────────────────────────────────────────────
    # UTILITY METHODS
    # ─────────────────────────────────────────────────────────────

    def log(self, message: str, level: str = "info") -> None:
        """Log a message."""
        timestamp = datetime.now(timezone.utc).isoformat()
        print(f"[{timestamp}] [QUEEN] [{level.upper()}] {message}")

    def _read_state(self) -> Dict[str, Any]:
        """Read current state."""
        state_path = self.honeycomb_path / "state.json"
        if state_path.exists():
            with open(state_path, 'r') as f:
                return json.load(f)
        return {}

    def _update_state(self, updates: Dict[str, Any]) -> None:
        """Update state file."""
        state = self._read_state()
        state = self._deep_merge(state, updates)
        state["_meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        state["_meta"]["last_updated_by"] = "queen"

        state_path = self.honeycomb_path / "state.json"
        with open(state_path, 'w') as f:
            json.dump(state, f, indent=2)

    def _read_tasks(self) -> Dict[str, Any]:
        """Read task queue."""
        tasks_path = self.honeycomb_path / "tasks.json"
        if tasks_path.exists():
            with open(tasks_path, 'r') as f:
                return json.load(f)
        return {}

    def _deep_merge(self, base: Dict, updates: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result


# ─────────────────────────────────────────────────────────────
# CLI INTERFACE
# ─────────────────────────────────────────────────────────────

def main():
    """CLI entry point for the Queen."""
    import argparse

    parser = argparse.ArgumentParser(description="Backlink Broadcast - Queen Orchestrator")
    parser.add_argument("command", choices=["run", "once", "spawn", "status", "trigger"],
                       help="Command to execute")
    parser.add_argument("--bee", "-b", help="Bee type to spawn")
    parser.add_argument("--event", "-e", help="Event type to trigger")
    parser.add_argument("--data", "-d", help="JSON data for task/event")

    args = parser.parse_args()

    queen = QueenOrchestrator()

    if args.command == "run":
        queen.run()

    elif args.command == "once":
        queen.run(once=True)

    elif args.command == "spawn":
        if not args.bee:
            print("Error: --bee required for spawn command")
            return
        task = json.loads(args.data) if args.data else None
        result = queen.spawn_bee(args.bee, task)
        print(json.dumps(result, indent=2))

    elif args.command == "status":
        status = queen.heartbeat()
        print(json.dumps(status, indent=2))

    elif args.command == "trigger":
        if not args.event:
            print("Error: --event required for trigger command")
            return
        data = json.loads(args.data) if args.data else {}
        results = queen.trigger_event(args.event, data)
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
