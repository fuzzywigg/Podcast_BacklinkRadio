"""
ScriptWriterBee - Writes comedy bits, recurring segments, and show scripts.

An Employed bee that creates engaging content scripts for the radio station,
including comedy bits, segment outlines, and recurring show elements.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class ScriptWriterBee:
    """
    ScriptWriterBee - Content creation for comedy and segments.
    
    Responsibilities:
    - Write comedy bits and jokes
    - Create recurring segment scripts
    - Generate show outlines
    - Adapt content to station voice/brand
    - Track script performance for iteration
    
    Outputs:
    - Segment scripts
    - Comedy bit outlines
    - Recurring segment templates
    """
    
    BEE_TYPE = "employed"
    PRIORITY = "normal"
    
    # Script types
    SCRIPT_TYPES = [
        "comedy_bit",
        "recurring_segment", 
        "interview_questions",
        "transition",
        "promo_read",
        "station_id",
        "show_intro",
        "show_outro"
    ]
    
    # Target durations (seconds)
    DURATION_TARGETS = {
        "comedy_bit": 60,
        "recurring_segment": 180,
        "interview_questions": 300,
        "transition": 15,
        "promo_read": 30,
        "station_id": 10,
        "show_intro": 45,
        "show_outro": 30
    }
    
    def __init__(self, hive_path: Optional[str] = None):
        """Initialize ScriptWriterBee."""
        if hive_path is None:
            hive_path = Path(__file__).parent.parent.parent
        self.hive_path = Path(hive_path)
        self.honeycomb_path = self.hive_path / "honeycomb"
        
        # Script storage
        self.scripts_path = self.honeycomb_path / "scripts.json"
        self._ensure_scripts_file()
    
    def _ensure_scripts_file(self) -> None:
        """Ensure scripts storage file exists."""
        if not self.scripts_path.exists():
            initial_data = {
                "scripts": [],
                "templates": {},
                "performance": {},
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            with open(self.scripts_path, 'w') as f:
                json.dump(initial_data, f, indent=2)
    
    def _load_scripts(self) -> Dict[str, Any]:
        """Load scripts data."""
        with open(self.scripts_path, 'r') as f:
            return json.load(f)
    
    def _save_scripts(self, data: Dict[str, Any]) -> None:
        """Save scripts data."""
        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.scripts_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_intel(self) -> Dict[str, Any]:
        """Load intel for context."""
        intel_path = self.honeycomb_path / "intel.json"
        if intel_path.exists():
            with open(intel_path, 'r') as f:
                return json.load(f)
        return {}
    
    def run(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute script writing task.
        
        Actions:
        - write_bit: Write a comedy bit
        - write_segment: Write a recurring segment
        - write_promo: Write a promo/ad read
        - generate_outline: Generate show outline
        - list_scripts: List existing scripts
        - get_template: Get a script template
        - track_performance: Log script performance
        """
        if task is None:
            task = {}
        
        action = task.get("action", "write_bit")
        
        actions = {
            "write_bit": self._write_comedy_bit,
            "write_segment": self._write_segment,
            "write_promo": self._write_promo,
            "generate_outline": self._generate_outline,
            "list_scripts": self._list_scripts,
            "get_template": self._get_template,
            "track_performance": self._track_performance,
            "get_stats": self._get_stats
        }
        
        handler = actions.get(action)
        if handler:
            return handler(task)
        
        return {"error": f"Unknown action: {action}"}
    
    def _write_comedy_bit(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Write a comedy bit script."""
        topic = task.get("topic", "")
        style = task.get("style", "observational")  # observational, satirical, absurdist
        duration = task.get("duration_seconds", 60)
        
        # Load current trends for topical humor
        intel = self._load_intel()
        trends = intel.get("trends", {}).get("topics", [])
        
        # Generate script structure
        script = {
            "id": f"bit_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "type": "comedy_bit",
            "topic": topic,
            "style": style,
            "target_duration_seconds": duration,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "draft",
            "content": {
                "setup": f"[SETUP - Establish premise about {topic}]",
                "build": "[BUILD - Escalate with 2-3 observations]",
                "punch": "[PUNCH - Deliver unexpected twist/callback]",
                "tag": "[TAG - Optional extra laugh]"
            },
            "notes": {
                "trends_considered": trends[:3] if trends else [],
                "energy_level": "medium",
                "requires_sound_effect": False
            }
        }
        
        # Save to storage
        data = self._load_scripts()
        data["scripts"].append(script)
        self._save_scripts(data)
        
        return {
            "success": True,
            "script_id": script["id"],
            "script": script,
            "message": f"Comedy bit draft created for topic: {topic}"
        }
    
    def _write_segment(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Write a recurring segment script."""
        segment_name = task.get("segment_name", "Untitled Segment")
        format_type = task.get("format", "interview")  # interview, quiz, review, discussion
        duration = task.get("duration_seconds", 180)
        
        script = {
            "id": f"seg_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "type": "recurring_segment",
            "segment_name": segment_name,
            "format": format_type,
            "target_duration_seconds": duration,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "draft",
            "content": {
                "intro": f"[INTRO - Segment jingle + '{segment_name}' announce]",
                "body": self._generate_segment_body(format_type),
                "outro": "[OUTRO - Segment wrap + tease next time]"
            },
            "recurring": True,
            "frequency": task.get("frequency", "weekly")
        }
        
        data = self._load_scripts()
        data["scripts"].append(script)
        self._save_scripts(data)
        
        return {
            "success": True,
            "script_id": script["id"],
            "script": script
        }

    
    def _generate_segment_body(self, format_type: str) -> Dict[str, str]:
        """Generate segment body structure based on format."""
        formats = {
            "interview": {
                "warmup": "[WARMUP - 2-3 quick getting-to-know questions]",
                "main_topic": "[MAIN - Deep dive on guest's expertise/story]",
                "rapid_fire": "[RAPID FIRE - Quick fun questions]"
            },
            "quiz": {
                "rules": "[RULES - Explain how to play]",
                "questions": "[QUESTIONS - 5-7 themed questions]",
                "reveal": "[REVEAL - Announce winner/score]"
            },
            "review": {
                "intro": "[INTRO - What we're reviewing today]",
                "breakdown": "[BREAKDOWN - Pros, cons, key points]",
                "verdict": "[VERDICT - Final rating/recommendation]"
            },
            "discussion": {
                "topic_intro": "[TOPIC - Frame the discussion]",
                "perspectives": "[PERSPECTIVES - Multiple viewpoints]",
                "audience": "[AUDIENCE - Incorporate listener input]"
            }
        }
        return formats.get(format_type, {"content": "[SEGMENT CONTENT]"})
    
    def _write_promo(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Write a promotional read script."""
        sponsor = task.get("sponsor", "")
        product = task.get("product", "")
        talking_points = task.get("talking_points", [])
        read_type = task.get("read_type", "host_read")  # host_read, live_read, produced
        duration = task.get("duration_seconds", 30)
        
        script = {
            "id": f"promo_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "type": "promo_read",
            "sponsor": sponsor,
            "product": product,
            "read_type": read_type,
            "target_duration_seconds": duration,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "draft",
            "content": {
                "hook": f"[HOOK - Attention grabber for {product}]",
                "body": self._format_talking_points(talking_points),
                "cta": "[CTA - Call to action with URL/code]",
                "disclaimer": "[DISCLAIMER - If required]"
            },
            "compliance": {
                "ftc_disclosure": True,
                "required_language": task.get("required_language", "")
            }
        }
        
        data = self._load_scripts()
        data["scripts"].append(script)
        self._save_scripts(data)
        
        return {
            "success": True,
            "script_id": script["id"],
            "script": script
        }
    
    def _format_talking_points(self, points: List[str]) -> str:
        """Format talking points for promo."""
        if not points:
            return "[TALKING POINTS - Benefits and features]"
        return "\n".join([f"  - {point}" for point in points])
    
    def _generate_outline(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a show outline."""
        show_name = task.get("show_name", "The Show")
        duration_minutes = task.get("duration_minutes", 60)
        theme = task.get("theme", "")
        
        # Standard show structure
        outline = {
            "id": f"outline_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "type": "show_outline",
            "show_name": show_name,
            "total_duration_minutes": duration_minutes,
            "theme": theme,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "segments": self._generate_show_segments(duration_minutes),
            "status": "draft"
        }
        
        data = self._load_scripts()
        data["scripts"].append(outline)
        self._save_scripts(data)
        
        return {
            "success": True,
            "outline_id": outline["id"],
            "outline": outline
        }
    
    def _generate_show_segments(self, duration_minutes: int) -> List[Dict[str, Any]]:
        """Generate standard show segment breakdown."""
        segments = [
            {"name": "Cold Open", "duration_minutes": 2, "type": "intro"},
            {"name": "Welcome + Headlines", "duration_minutes": 5, "type": "intro"},
        ]
        
        # Calculate remaining time for content
        remaining = duration_minutes - 7 - 3  # minus intro and outro
        
        # Add content segments
        segment_count = remaining // 15  # ~15 min segments
        for i in range(segment_count):
            segments.append({
                "name": f"Segment {i+1}",
                "duration_minutes": 12,
                "type": "content",
                "notes": "[Topic TBD]"
            })
            segments.append({
                "name": f"Break {i+1}",
                "duration_minutes": 3,
                "type": "break"
            })
        
        segments.append({"name": "Wrap Up + Preview", "duration_minutes": 3, "type": "outro"})
        
        return segments

    
    def _list_scripts(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """List existing scripts with optional filters."""
        data = self._load_scripts()
        scripts = data.get("scripts", [])
        
        # Apply filters
        script_type = task.get("type")
        status = task.get("status")
        limit = task.get("limit", 20)
        
        if script_type:
            scripts = [s for s in scripts if s.get("type") == script_type]
        if status:
            scripts = [s for s in scripts if s.get("status") == status]
        
        # Sort by created_at descending
        scripts = sorted(scripts, key=lambda x: x.get("created_at", ""), reverse=True)
        
        return {
            "success": True,
            "total": len(scripts),
            "scripts": scripts[:limit],
            "types": self.SCRIPT_TYPES
        }
    
    def _get_template(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get a script template."""
        template_type = task.get("template_type", "comedy_bit")
        
        templates = {
            "comedy_bit": {
                "structure": ["setup", "build", "punch", "tag"],
                "timing": "Setup: 15s, Build: 30s, Punch: 10s, Tag: 5s",
                "tips": [
                    "Start with relatable observation",
                    "Use rule of three for build",
                    "Punch should subvert expectations",
                    "Tag is optional callback"
                ]
            },
            "interview_questions": {
                "structure": ["opener", "background", "expertise", "personal", "closer"],
                "timing": "5-7 questions for 10-minute segment",
                "tips": [
                    "Research guest beforehand",
                    "Start with easy warmup",
                    "Have follow-up questions ready",
                    "End with memorable closer"
                ]
            },
            "promo_read": {
                "structure": ["hook", "problem", "solution", "proof", "cta"],
                "timing": "30s = ~75 words, 60s = ~150 words",
                "tips": [
                    "Sound natural, not salesy",
                    "Include personal endorsement",
                    "Repeat CTA/code",
                    "FTC disclosure if required"
                ]
            },
            "transition": {
                "structure": ["acknowledge", "bridge", "preview"],
                "timing": "10-15 seconds",
                "tips": [
                    "Keep energy consistent",
                    "Reference what just happened",
                    "Tease what's coming"
                ]
            }
        }
        
        template = templates.get(template_type)
        if template:
            return {
                "success": True,
                "template_type": template_type,
                "template": template
            }
        
        return {
            "success": False,
            "error": f"Unknown template type: {template_type}",
            "available_types": list(templates.keys())
        }
    
    def _track_performance(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Track script performance metrics."""
        script_id = task.get("script_id")
        if not script_id:
            return {"error": "script_id required"}
        
        metrics = {
            "used_at": datetime.now(timezone.utc).isoformat(),
            "audience_reaction": task.get("reaction", "neutral"),  # positive, neutral, negative
            "laugh_count": task.get("laugh_count", 0),
            "engagement_boost": task.get("engagement_boost", 0.0),
            "notes": task.get("notes", "")
        }
        
        data = self._load_scripts()
        performance = data.get("performance", {})
        
        if script_id not in performance:
            performance[script_id] = []
        performance[script_id].append(metrics)
        
        data["performance"] = performance
        self._save_scripts(data)
        
        return {
            "success": True,
            "script_id": script_id,
            "performance_logged": metrics,
            "total_uses": len(performance[script_id])
        }
    
    def _get_stats(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get script statistics."""
        data = self._load_scripts()
        scripts = data.get("scripts", [])
        performance = data.get("performance", {})
        
        # Count by type
        by_type = {}
        for script in scripts:
            stype = script.get("type", "unknown")
            by_type[stype] = by_type.get(stype, 0) + 1
        
        # Count by status
        by_status = {}
        for script in scripts:
            status = script.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1
        
        # Top performers
        top_performers = []
        for script_id, uses in performance.items():
            positive_count = sum(1 for u in uses if u.get("audience_reaction") == "positive")
            if positive_count > 0:
                top_performers.append({
                    "script_id": script_id,
                    "total_uses": len(uses),
                    "positive_reactions": positive_count
                })
        
        top_performers.sort(key=lambda x: x["positive_reactions"], reverse=True)
        
        return {
            "success": True,
            "total_scripts": len(scripts),
            "by_type": by_type,
            "by_status": by_status,
            "scripts_with_performance_data": len(performance),
            "top_performers": top_performers[:5],
            "last_updated": data.get("last_updated")
        }
