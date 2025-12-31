"""
Queen Orchestrator - Central coordinator for the hive.

The Queen doesn't micromanage. She:
1. Wakes bees on schedules (cron-like)
2. Wakes bees on events (triggers)
3. Monitors hive health
4. Balances workload
5. Orchestrates Model-First Reasoning (MFR) workflow
6. Coordinates cognitive layer (coherence, evolution, distillation)

The Queen is the heartbeat of the operation.
"""

import json
import time
import copy
import importlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Tuple
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
        self._state_cache = {}  # {filepath: {'mtime': float, 'content': dict}}

        # MFR workflow settings
        self.mfr_enabled = True
        self.coherence_check_enabled = True
        self.experience_distillation_enabled = True

        # Cognitive layer instances (lazy-loaded)
        self._coherence_guardian = None
        self._evolution_governor = None
        self._experience_distiller = None

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
            # Content bees (4)
            "show_prep": ("bees.content.show_prep_bee", "ShowPrepBee"),
            "clip_cutter": ("bees.content.clip_cutter_bee", "ClipCutterBee"),
            "script_writer": ("bees.content.script_writer_bee", "ScriptWriterBee"),
            "jingle": ("bees.content.jingle_bee", "JingleBee"),
            # Research bees (4)
            "trend_scout": ("bees.research.trend_scout_bee", "TrendScoutBee"),
            "listener_intel": ("bees.research.listener_intel_bee", "ListenerIntelBee"),
            "music_discovery": ("bees.research.music_discovery_bee", "MusicDiscoveryBee"),
            "competitor_watch": ("bees.research.competitor_watch_bee", "CompetitorWatchBee"),
            # Marketing bees (4)
            "social_poster": ("bees.marketing.social_poster_bee", "SocialPosterBee"),
            "newsletter": ("bees.marketing.newsletter_bee", "NewsletterBee"),
            "seo": ("bees.marketing.seo_bee", "SEOBee"),
            "viral_analyst": ("bees.marketing.viral_analyst_bee", "ViralAnalystBee"),
            # Monetization bees (4)
            "sponsor_hunter": ("bees.monetization.sponsor_hunter_bee", "SponsorHunterBee"),
            "donation_processor": ("bees.monetization.donation_processor_bee", "DonationProcessorBee"),
            "revenue_analyst": ("bees.monetization.revenue_analyst_bee", "RevenueAnalystBee"),
            "merch": ("bees.monetization.merch_bee", "MerchBee"),
            # Community bees (5)
            "engagement": ("bees.community.engagement_bee", "EngagementBee"),
            "vip_manager": ("bees.community.vip_manager_bee", "VIPManagerBee"),
            "moderator": ("bees.community.moderator_bee", "ModeratorBee"),
            "giveaway": ("bees.community.giveaway_bee", "GiveawayBee"),
            "local_liaison": ("bees.community.local_liaison_bee", "LocalLiaisonBee"),
            # Technical bees (5)
            "stream_monitor": ("bees.technical.stream_monitor_bee", "StreamMonitorBee"),
            "archivist": ("bees.technical.archivist_bee", "ArchivistBee"),
            "automation": ("bees.technical.automation_bee", "AutomationBee"),
            "audio_engineer": ("bees.technical.audio_engineer_bee", "AudioEngineerBee"),
            "integration": ("bees.technical.integration_bee", "IntegrationBee"),
            # Admin bees (3)
            "analytics": ("bees.admin.analytics_bee", "AnalyticsBee"),
            "planner": ("bees.admin.planner_bee", "PlannerBee"),
            "licensing": ("bees.admin.licensing_bee", "LicensingBee"),
            # Cognitive bees (3)
            "coherence_guardian": ("bees.cognitive.coherence_guardian_bee", "CoherenceGuardianBee"),
            "evolution_governor": ("bees.cognitive.evolution_governor_bee", "EvolutionGovernorBee"),
            "experience_distiller": ("bees.cognitive.experience_distiller_bee", "ExperienceDistillerBee")
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

    # ─────────────────────────────────────────────────────────────
    # COGNITIVE LAYER ACCESSORS (Lazy-loaded)
    # ─────────────────────────────────────────────────────────────

    def _get_coherence_guardian(self):
        """Get or create CoherenceGuardianBee instance."""
        if self._coherence_guardian is None:
            try:
                import sys
                bees_path = str(self.hive_path / "bees")
                if bees_path not in sys.path:
                    sys.path.insert(0, bees_path)
                from cognitive.coherence_guardian_bee import CoherenceGuardianBee
                self._coherence_guardian = CoherenceGuardianBee(hive_path=self.hive_path)
            except Exception as e:
                self.log(f"Failed to load CoherenceGuardianBee: {e}", level="warning")
        return self._coherence_guardian

    def _get_evolution_governor(self):
        """Get or create EvolutionGovernorBee instance."""
        if self._evolution_governor is None:
            try:
                import sys
                bees_path = str(self.hive_path / "bees")
                if bees_path not in sys.path:
                    sys.path.insert(0, bees_path)
                from cognitive.evolution_governor_bee import EvolutionGovernorBee
                self._evolution_governor = EvolutionGovernorBee(hive_path=self.hive_path)
            except Exception as e:
                self.log(f"Failed to load EvolutionGovernorBee: {e}", level="warning")
        return self._evolution_governor

    def _get_experience_distiller(self):
        """Get or create ExperienceDistillerBee instance."""
        if self._experience_distiller is None:
            try:
                import sys
                bees_path = str(self.hive_path / "bees")
                if bees_path not in sys.path:
                    sys.path.insert(0, bees_path)
                from cognitive.experience_distiller_bee import ExperienceDistillerBee
                self._experience_distiller = ExperienceDistillerBee(hive_path=self.hive_path)
            except Exception as e:
                self.log(f"Failed to load ExperienceDistillerBee: {e}", level="warning")
        return self._experience_distiller

    # ─────────────────────────────────────────────────────────────
    # MFR WORKFLOW METHODS
    # ─────────────────────────────────────────────────────────────

    def run_coherence_check(self) -> Dict[str, Any]:
        """Run a full hive coherence check."""
        guardian = self._get_coherence_guardian()
        if guardian:
            return guardian.run({"action": "full_check"})
        return {"error": "CoherenceGuardianBee not available"}

    def run_evolution_governance(self) -> Dict[str, Any]:
        """Process pending evolution proposals."""
        governor = self._get_evolution_governor()
        if governor:
            return governor.run({"action": "review_all"})
        return {"error": "EvolutionGovernorBee not available"}

    def run_experience_distillation(self) -> Dict[str, Any]:
        """Distill experiences from completed tasks."""
        distiller = self._get_experience_distiller()
        if distiller:
            return distiller.run({"action": "distill"})
        return {"error": "ExperienceDistillerBee not available"}

    def check_model_coherence(self, model: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if a model is coherent with hive constraints."""
        guardian = self._get_coherence_guardian()
        if guardian:
            run_result = guardian.run({
                "payload": {
                    "action": "validate_model",
                    "model": model
                }
            })
            
            # BaseBee.run() wraps work() result under "result" key
            result = run_result.get("result", {})
            
            is_valid = result.get("valid", False)
            
            # Build reason from issues or missing fields
            if is_valid:
                reason = "Model validated successfully"
            else:
                issues = result.get("issues", [])
                missing = result.get("missing_fields", [])
                if missing:
                    reason = f"Missing fields: {', '.join(missing)}"
                elif issues:
                    reason = "; ".join(issues)
                else:
                    reason = result.get("recommendation", "Model validation failed")
            return is_valid, reason
        return True, "Coherence check skipped (guardian not available)"

    # ─────────────────────────────────────────────────────────────
    # BEE SPAWNING WITH MFR
    # ─────────────────────────────────────────────────────────────

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
                    elif "script_writer" in module_path:
                        from content.script_writer_bee import ScriptWriterBee as BeeClass
                    elif "jingle" in module_path:
                        from content.jingle_bee import JingleBee as BeeClass
                    else:
                        return {"error": f"Cannot import content bee: {bee_type}"}
                elif "research" in module_path:
                    if "trend_scout" in module_path:
                        from research.trend_scout_bee import TrendScoutBee as BeeClass
                    elif "listener_intel" in module_path:
                        from research.listener_intel_bee import ListenerIntelBee as BeeClass
                    elif "music_discovery" in module_path:
                        from research.music_discovery_bee import MusicDiscoveryBee as BeeClass
                    elif "competitor_watch" in module_path:
                        from research.competitor_watch_bee import CompetitorWatchBee as BeeClass
                    else:
                        return {"error": f"Cannot import research bee: {bee_type}"}
                elif "marketing" in module_path:
                    if "social_poster" in module_path:
                        from marketing.social_poster_bee import SocialPosterBee as BeeClass
                    elif "newsletter" in module_path:
                        from marketing.newsletter_bee import NewsletterBee as BeeClass
                    elif "seo" in module_path:
                        from marketing.seo_bee import SEOBee as BeeClass
                    elif "viral_analyst" in module_path:
                        from marketing.viral_analyst_bee import ViralAnalystBee as BeeClass
                    else:
                        return {"error": f"Cannot import marketing bee: {bee_type}"}
                elif "monetization" in module_path:
                    if "sponsor_hunter" in module_path:
                        from monetization.sponsor_hunter_bee import SponsorHunterBee as BeeClass
                    elif "donation_processor" in module_path:
                        from monetization.donation_processor_bee import DonationProcessorBee as BeeClass
                    elif "revenue_analyst" in module_path:
                        from monetization.revenue_analyst_bee import RevenueAnalystBee as BeeClass
                    elif "merch" in module_path:
                        from monetization.merch_bee import MerchBee as BeeClass
                    else:
                        return {"error": f"Cannot import monetization bee: {bee_type}"}
                elif "community" in module_path:
                    if "engagement" in module_path:
                        from community.engagement_bee import EngagementBee as BeeClass
                    elif "vip_manager" in module_path:
                        from community.vip_manager_bee import VIPManagerBee as BeeClass
                    elif "moderator" in module_path:
                        from community.moderator_bee import ModeratorBee as BeeClass
                    elif "giveaway" in module_path:
                        from community.giveaway_bee import GiveawayBee as BeeClass
                    elif "local_liaison" in module_path:
                        from community.local_liaison_bee import LocalLiaisonBee as BeeClass
                    else:
                        return {"error": f"Cannot import community bee: {bee_type}"}
                elif "technical" in module_path:
                    if "stream_monitor" in module_path:
                        from technical.stream_monitor_bee import StreamMonitorBee as BeeClass
                    elif "archivist" in module_path:
                        from technical.archivist_bee import ArchivistBee as BeeClass
                    elif "automation" in module_path:
                        from technical.automation_bee import AutomationBee as BeeClass
                    elif "audio_engineer" in module_path:
                        from technical.audio_engineer_bee import AudioEngineerBee as BeeClass
                    elif "integration" in module_path:
                        from technical.integration_bee import IntegrationBee as BeeClass
                    else:
                        return {"error": f"Cannot import technical bee: {bee_type}"}
                elif "admin" in module_path:
                    if "analytics" in module_path:
                        from admin.analytics_bee import AnalyticsBee as BeeClass
                    elif "planner" in module_path:
                        from admin.planner_bee import PlannerBee as BeeClass
                    elif "licensing" in module_path:
                        from admin.licensing_bee import LicensingBee as BeeClass
                    else:
                        return {"error": f"Cannot import admin bee: {bee_type}"}
                elif "cognitive" in module_path:
                    if "coherence_guardian" in module_path:
                        from cognitive.coherence_guardian_bee import CoherenceGuardianBee as BeeClass
                    elif "evolution_governor" in module_path:
                        from cognitive.evolution_governor_bee import EvolutionGovernorBee as BeeClass
                    elif "experience_distiller" in module_path:
                        from cognitive.experience_distiller_bee import ExperienceDistillerBee as BeeClass
                    else:
                        return {"error": f"Cannot import cognitive bee: {bee_type}"}
                else:
                    return {"error": f"Cannot import bee: {bee_type}"}
            else:
                BeeClass = bee_info

            # Instantiate bee
            bee = BeeClass(hive_path=self.hive_path)

            # MFR Workflow Integration
            if self.mfr_enabled and hasattr(bee, 'define_model'):
                return self._spawn_with_mfr(bee, bee_type, task)
            else:
                # Standard execution (non-MFR bees)
                result = bee.run(task)
                return result

        except Exception as e:
            self.log(f"Error spawning {bee_type}: {e}", level="error")
            return {"error": str(e)}

    def _spawn_with_mfr(self, bee, bee_type: str, task: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute bee with full MFR workflow.
        
        Steps:
        1. Define model (entities, actions, constraints)
        2. Validate coherence with hive
        3. Execute within model bounds
        4. Store successful patterns as pollen
        5. Track for evolution proposals
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Phase 1: Define Model
            model = bee.define_model(task)
            self.log(f"[MFR] {bee_type} defined model with {len(model.get('entities', []))} entities")
            
            # Phase 2: Coherence Check
            if self.coherence_check_enabled:
                is_coherent, reason = self.check_model_coherence(model)
                if not is_coherent:
                    self.log(f"[MFR] {bee_type} model rejected: {reason}", level="warning")
                    return {
                        "success": False,
                        "error": f"Model coherence check failed: {reason}",
                        "mfr_phase": "coherence_check"
                    }
            
            # Phase 3: Execute within model
            if hasattr(bee, 'execute_within_model'):
                result = bee.execute_within_model(model, task)
            else:
                result = bee.run(task)
            
            # Calculate success score
            success = result.get("success", True) if isinstance(result, dict) else True
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            success_score = self._calculate_success_score(result, duration)
            
            # Phase 4: Store pollen (if successful)
            if success and self.experience_distillation_enabled and hasattr(bee, 'store_pollen'):
                bee.store_pollen(model, result, success_score)
                self.log(f"[MFR] {bee_type} stored pollen (score: {success_score:.2f})")
            
            # Add MFR metadata to result
            if isinstance(result, dict):
                result["_mfr"] = {
                    "model_defined": True,
                    "coherence_checked": self.coherence_check_enabled,
                    "pollen_stored": success and self.experience_distillation_enabled,
                    "success_score": success_score,
                    "duration_seconds": duration
                }
            
            return result
            
        except Exception as e:
            self.log(f"[MFR] Error in MFR workflow for {bee_type}: {e}", level="error")
            return {
                "success": False,
                "error": str(e),
                "mfr_phase": "execution"
            }

    def _calculate_success_score(self, result: Any, duration: float) -> float:
        """Calculate success score for experience distillation."""
        score = 0.5  # Base score for completion
        
        if isinstance(result, dict):
            # Bonus for explicit success
            if result.get("success", False):
                score += 0.2
            # Bonus for fast execution
            if duration < 10:
                score += 0.2
            # Bonus for having output
            if result.get("output") or result.get("data"):
                score += 0.1
            # Penalty for errors
            if result.get("error") or result.get("errors"):
                score -= 0.3
        
        return max(0.0, min(1.0, score))

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

        health = {
            "broadcast_status": state.get("broadcast", {}).get("status", "unknown"),
            "pending_tasks": len(tasks.get("pending", [])),
            "in_progress_tasks": len(tasks.get("in_progress", [])),
            "failed_tasks": len(tasks.get("failed", [])),
            "alerts_pending": len(state.get("alerts", {}).get("priority", []))
        }
        
        # Add cognitive layer metrics
        health["mfr_enabled"] = self.mfr_enabled
        health["cognitive_layer"] = {
            "coherence_guardian": self._coherence_guardian is not None,
            "evolution_governor": self._evolution_governor is not None,
            "experience_distiller": self._experience_distiller is not None
        }
        
        # Check pollen store
        pollen_path = self.honeycomb_path / "pollen.json"
        if pollen_path.exists():
            try:
                with open(pollen_path, 'r') as f:
                    pollen = json.load(f)
                health["pollen_patterns"] = len(pollen.get("patterns", {}))
            except:
                health["pollen_patterns"] = 0
        
        # Check lineage
        lineage_path = self.honeycomb_path / "lineage.json"
        if lineage_path.exists():
            try:
                with open(lineage_path, 'r') as f:
                    lineage = json.load(f)
                health["pending_proposals"] = len(lineage.get("pending_updates", []))
            except:
                health["pending_proposals"] = 0
        
        return health

    def run(self, once: bool = False) -> None:
        """
        Run the Queen's main loop.

        Args:
            once: If True, run one cycle and exit. If False, run continuously.
        """
        self.running = True
        self.log("Queen is online. Hive is active.")
        self.log(f"MFR workflow: {'enabled' if self.mfr_enabled else 'disabled'}")

        cycle_count = 0

        while self.running:
            try:
                cycle_count += 1
                
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

                # Cognitive layer cycles (every 10th cycle)
                if cycle_count % 10 == 0:
                    self._run_cognitive_cycle()

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

    def _run_cognitive_cycle(self) -> None:
        """Run cognitive layer maintenance cycle."""
        self.log("[Cognitive] Running maintenance cycle...")
        
        try:
            # 1. Experience distillation - harvest patterns from completed tasks
            if self.experience_distillation_enabled:
                distill_result = self.run_experience_distillation()
                if distill_result.get("patterns_created", 0) > 0:
                    self.log(f"[Cognitive] Distilled {distill_result['patterns_created']} patterns")
            
            # 2. Evolution governance - process pending proposals
            gov_result = self.run_evolution_governance()
            approved = gov_result.get("approved", 0)
            rejected = gov_result.get("rejected", 0)
            if approved + rejected > 0:
                self.log(f"[Cognitive] Evolution: {approved} approved, {rejected} rejected")
            
            # 3. Coherence check - verify hive consistency
            if self.coherence_check_enabled:
                coherence_result = self.run_coherence_check()
                if not coherence_result.get("coherent", True):
                    self.log("[Cognitive] Coherence issues detected!", level="warning")
                    # Trigger coherence alert event
                    self.trigger_event("coherence_alert", coherence_result)
                    
        except Exception as e:
            self.log(f"[Cognitive] Error in maintenance cycle: {e}", level="error")

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
                return copy.deepcopy(cache_entry['content'])  # Deep copy to prevent mutation of cache

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
    parser.add_argument("command", choices=[
        "run", "once", "spawn", "status", "trigger",
        "coherence", "evolve", "distill", "cognitive"
    ], help="Command to execute")
    parser.add_argument("--bee", "-b", help="Bee type to spawn")
    parser.add_argument("--event", "-e", help="Event type to trigger")
    parser.add_argument("--data", "-d", help="JSON data for task/event")
    parser.add_argument("--no-mfr", action="store_true", help="Disable MFR workflow")

    args = parser.parse_args()

    queen = QueenOrchestrator()
    
    if args.no_mfr:
        queen.mfr_enabled = False

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
    
    elif args.command == "coherence":
        result = queen.run_coherence_check()
        print(json.dumps(result, indent=2))
    
    elif args.command == "evolve":
        result = queen.run_evolution_governance()
        print(json.dumps(result, indent=2))
    
    elif args.command == "distill":
        result = queen.run_experience_distillation()
        print(json.dumps(result, indent=2))
    
    elif args.command == "cognitive":
        print("Running full cognitive cycle...")
        queen._run_cognitive_cycle()
        print("Cognitive cycle complete.")


if __name__ == "__main__":
    main()
