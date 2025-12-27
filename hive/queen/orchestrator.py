"""
Queen Orchestrator - Central coordinator for the hive.
Updated to initialize Constitutional Gateway.
"""

import json
import time
import copy
import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
import queue
from hive.utils.cache_manager import BacklinkCacheManager
import sys

# Ensure we can find the sibling constitutional-llm package
ROOT_DIR = Path(__file__).parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

try:
    from constitutional_llm.src.constitutional_gateway import ConstitutionalGateway
except ImportError:
    print("WARNING: Constitutional Gateway not found. Governance disabled.")
    ConstitutionalGateway = None

# Ensure we can find the sibling constitutional-llm package
# Assuming orchestrator.py is in hive/queen/ and constitutional-llm is in root
ROOT_DIR = Path(__file__).parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

try:
    from constitutional_llm.src.constitutional_gateway import ConstitutionalGateway
except ImportError:
    print("WARNING: Constitutional Gateway not found. Governance disabled.")
    ConstitutionalGateway = None

class QueenOrchestrator:
    """
    The Queen - orchestrates the entire hive operation.
    """

    def __init__(self, hive_path: Optional[str] = None):
        """Initialize the Queen."""
        if hive_path is None:
            hive_path = Path(__file__).parent.parent
        self.hive_path = Path(hive_path)
        self.honeycomb_path = self.hive_path / "honeycomb"

        # Initialize the Governance Layer
        if ConstitutionalGateway:
            self.gateway = ConstitutionalGateway(bee_type="QUEEN")
            self.log("Constitutional Gateway: ONLINE")
        else:
            self.gateway = None
            self.log("Constitutional Gateway: OFFLINE (Security Risk)", level="warning")

        # Registered bees
        self.bee_registry: Dict[str, Type] = {}
        self.event_queue: queue.Queue = queue.Queue()
        self.running = False
        self.last_heartbeat = None
        self._state_cache = {}  # {filepath: {'mtime': float, 'content': dict}}

        # Health Tracking
        self.bee_failures = {}  # {bee_type: failure_count}
        self.MAX_BEE_FAILURES = 3

        # Load configuration
        self.config = self._load_config()
        self._register_default_bees()

    def spawn_bee(self, bee_type: str, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Spawn a bee to do work."""
        if bee_type not in self.bee_registry:
            return {"error": f"Unknown bee type: {bee_type}"}

        if self.bee_failures.get(bee_type, 0) >= self.MAX_BEE_FAILURES:
             self.log(f"Spawn blocked: {bee_type} is exiled due to failure rate.", level="error")
             return {"error": "bee_exiled"}

        self.log(f"Spawning {bee_type} bee...")

        try:
            # Get bee class info
            bee_info = self.bee_registry[bee_type]

            if isinstance(bee_info, tuple):
                module_path, class_name = bee_info
                module = importlib.import_module(f"hive.{module_path}")
                BeeClass = getattr(module, class_name)
            else:
                BeeClass = bee_info

            # INJECT GATEWAY HERE
            bee = BeeClass(hive_path=self.hive_path, gateway=self.gateway)
            result = bee.run(task)

            if result.get("success"):
                self.bee_failures[bee_type] = 0
            else:
                self._record_failure(bee_type)

            return result

        except Exception as e:
            self.log(f"Error spawning {bee_type}: {e}", level="error")
            self._record_failure(bee_type)
            return {"error": str(e)}

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
                # Daily
                "sponsor_hunter": {"interval_minutes": 1440, "enabled": True},
                # Radio Physics
                "radio_physics": {"interval_minutes": 5, "enabled": True}
            },
            "event_triggers": {
                "donation": ["engagement", "social_poster", "payout_processor"],
                "mention": ["engagement", "listener_intel"],
                "trend_alert": ["show_prep", "social_poster"],
                "vip_detected": ["engagement"],
                # Refund on fail
                "stream_issue": ["payout_processor", "radio_physics"]
            }
        }

    def _register_default_bees(self) -> None:
        """Register all default bee types."""

        # Import and register bees
        bee_mappings = {
            "show_prep": ("bees.content.show_prep_bee", "ShowPrepBee"),
            "dj": ("bees.content.dj_bee", "DjBee"),
            "clip_cutter": ("bees.content.clip_cutter_bee", "ClipCutterBee"),
            "trend_scout": ("bees.research.trend_scout_bee", "TrendScoutBee"),
            "listener_intel": ("bees.research.listener_intel_bee", "ListenerIntelBee"),
            "social_poster": ("bees.marketing.social_poster_bee", "SocialPosterBee"),
            "sponsor_hunter": ("bees.monetization.sponsor_hunter_bee", "SponsorHunterBee"),
            "engagement": ("bees.community.engagement_bee", "EngagementBee"),
            "stream_monitor": ("bees.technical.stream_monitor_bee", "StreamMonitorBee"),
            "radio_physics": ("bees.technical.radio_physics_bee", "RadioPhysicsBee"),
            "payout_processor": ("bees.monetization.payout_processor_bee", "PayoutProcessorBee"),
            "weather": ("bees.research.weather_bee", "WeatherBee"),
            "traffic_sponsor": ("bees.monetization.traffic_sponsor_bee", "TrafficSponsorBee"),
            "dao_update": ("bees.marketing.dao_update_bee", "DAOUpdateBee"),
            "sports_tracker": ("bees.research.sports_tracker_bee", "SportsTrackerBee")
        }

        for bee_type, (module_path, class_name) in bee_mappings.items():
            try:
                # Dynamic import
                full_path = f"hive.{module_path}"
                # For now, just store the mapping - actual import happens when
                # spawning
                self.bee_registry[bee_type] = (module_path, class_name)
            except Exception as e:
                self.log(
                    f"Failed to register {bee_type}: {e}",
                    level="warning")

    def register_bee(self, bee_type: str, bee_class: Type) -> None:
        """Register a bee type."""
        self.bee_registry[bee_type] = bee_class
        self.log(f"Registered bee type: {bee_type}")

    def spawn_bee(self, bee_type: str,
                  task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Spawn a bee to do work."""

        if bee_type not in self.bee_registry:
            return {"error": f"Unknown bee type: {bee_type}"}

        # Check Exorcism Protocol Status
        if self.bee_failures.get(bee_type, 0) >= self.MAX_BEE_FAILURES:
            self.log(
                f"Spawn blocked: {bee_type} is currently exiled due to failure rate.",
                level="error")
            return {"error": "bee_exiled"}

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
                # Simplified loader
                module_parts = module_path.split('.')
                # e.g., bees.content.show_prep_bee -> show_prep_bee
                # This assumes standard structure

                # Import via importlib
                module = importlib.import_module(module_path)
                BeeClass = getattr(module, class_name)

            else:
                BeeClass = bee_info

            # Instantiate and run
            # INJECT GATEWAY HERE
            bee = BeeClass(hive_path=self.hive_path, gateway=self.gateway)
            result = bee.run(task)

            # Record success (reset failures)
            if result.get("success"):
                self.bee_failures[bee_type] = 0
            else:
                self._record_failure(bee_type)

            return result

        except Exception as e:
            self.log(f"Error spawning {bee_type}: {e}", level="error")
            self._record_failure(bee_type)
            return {"error": str(e)}

    def _record_failure(self, bee_type: str):
        """Record a failure for a bee type."""
        current = self.bee_failures.get(bee_type, 0)
        self.bee_failures[bee_type] = current + 1

        if self.bee_failures[bee_type] >= self.MAX_BEE_FAILURES:
            self._robot_exorcism_protocol(bee_type)

    def _robot_exorcism_protocol(self, bee_type: str):
        """
        The Robot Exorcism Protocol.
        Invoked when a bee fails repeatedly.
        """
        self.log(
            f"⚠ EXORCISM PROTOCOL INITIATED for {bee_type} ⚠",
            level="critical")
        self.log(
            f"Bee {bee_type} has failed {
                self.MAX_BEE_FAILURES} times consecutively.")

        # 1. Post Critical Alert
        self._update_state({
            "alerts": {
                "priority": [{
                    "id": f"exorcism_{int(time.time())}",
                    "message": f"Bee {bee_type} has been exiled due to critical instability.",
                    "from": "QueenOrchestrator",
                    "at": datetime.now(timezone.utc).isoformat()
                }]
            }
        })

        # 2. Logic to "Review and Revise" (Stub for self-healing)
        # In a full system, this would trigger an Agentic Code Reviewer to inspect the bee's code.
        # For now, we just log it and potentially reset the counter after a
        # cooldown.

        # 3. Temporary Exile (Cooldown)
        # We don't actually delete the file, but we stop spawning it.
        # The counter remains high until manual intervention or auto-reset.

    def trigger_event(self, event_type: str,
                      data: Dict[str, Any]) -> List[Dict[str, Any]]:
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
                try:
                    last_run_dt = datetime.fromisoformat(
                        last_run.replace('Z', '+00:00'))
                    minutes_since = (now - last_run_dt).total_seconds() / 60
                    should_run = minutes_since >= interval_minutes
                except ValueError:
                    # If format is bad, run it
                    should_run = True

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
            "broadcast_status": state.get(
                "broadcast", {}).get(
                "status", "unknown"), "pending_tasks": len(
                tasks.get(
                    "pending", [])), "in_progress_tasks": len(
                        tasks.get(
                            "in_progress", [])), "failed_tasks": len(
                                tasks.get(
                                    "failed", [])), "alerts_pending": len(
                                        state.get(
                                            "alerts", {}).get(
                                                "priority", []))}

    def run(self, once: bool = False) -> None:
        """
        Run the Queen's main loop.

        Args:
            once: If True, run one cycle and exit. If False, run continuously.
        """
        # Ensure station identity cache is fresh
        # Note: BacklinkCacheManager import was removed in User's provided snippet?
        # User snippet imports: json, time, copy, importlib, sys, datetime, pathlib, typing, queue.
        # Original had BacklinkCacheManager.
        # The user says "Keep the rest of your existing methods...".
        # I removed BacklinkCacheManager import because it was not in the user's snippet,
        # but I should probably keep it if run() uses it.
        # However, I can't import it if I don't import it.
        # The user's snippet provided full imports, so maybe I should stick to that.
        # But if run() uses it, it will crash.
        # I'll check if I included BacklinkCacheManager in the imports I prepared.
        # I did NOT. I should add it back if I keep the run() method.
        # Wait, I am overwriting the file. I am writing the file content I prepared above.
        # In the content above, I did NOT include `from hive.utils.cache_manager import BacklinkCacheManager`.
        # I should add it.
        # Let me add it now.

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
                    self.log(
                        f"Processed {
                            queue_result['processed']} queued tasks")

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

    def _read_json_cached(self, filename: str) -> Dict[str, Any]:
        """Read a JSON file with mtime caching."""
        filepath = self.honeycomb_path / filename
        if not filepath.exists():
            return {}

        try:
            mtime = filepath.stat().st_mtime
            path_str = str(filepath)

            cache_entry = self._state_cache.get(path_str)
            if cache_entry and cache_entry['mtime'] == mtime:
                # Deep copy to prevent mutation of cache
                return copy.deepcopy(cache_entry['content'])

            with open(filepath, 'r') as f:
                content = json.load(f)

            self._state_cache[path_str] = {
                'mtime': mtime,
                'content': content
            }
            return copy.deepcopy(content)
        except Exception as e:
            self.log(f"Error reading {filename}: {e}", level="error")
            return {}

    def _read_state(self) -> Dict[str, Any]:
        """Read current state."""
        return self._read_json_cached("state.json")

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
        return self._read_json_cached("tasks.json")

    def _deep_merge(self, base: Dict, updates: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in updates.items():
            if key in result and isinstance(
                    result[key],
                    dict) and isinstance(
                    value,
                    dict):
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

    parser = argparse.ArgumentParser(
        description="Backlink Broadcast - Queen Orchestrator")
    parser.add_argument(
        "command",
        choices=[
            "run",
            "once",
            "spawn",
            "status",
            "trigger"],
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
