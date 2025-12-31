"""
AudioEngineerBee - Audio Processing Bee

Processes audio files, normalizes levels, applies effects,
and ensures broadcast-ready audio quality.
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


class AudioEngineerBee(BaseBee):
    """
    Handles audio processing and quality control.
    
    Type: Employed bee
    Priority: High
    Schedule: On-demand / Batch processing
    """
    
    BEE_TYPE = "audio_engineer"
    BEE_NAME = "AudioEngineerBee"
    CATEGORY = "technical"
    LINEAGE_VERSION = "1.0.0"
    
    def __init__(self, hive_path: Optional[Path] = None):
        super().__init__(hive_path=hive_path)
        self.audio_file = self.honeycomb_path / "audio_processing.json"
        self._ensure_audio_file()
    
    def _ensure_audio_file(self):
        """Initialize audio processing storage."""
        if not self.audio_file.exists():
            initial = {
                "jobs": [],
                "presets": {
                    "broadcast_standard": {
                        "normalize_lufs": -16,
                        "peak_limit": -1,
                        "sample_rate": 44100,
                        "bit_depth": 16,
                        "format": "mp3",
                        "bitrate": 192
                    },
                    "podcast": {
                        "normalize_lufs": -19,
                        "peak_limit": -1,
                        "sample_rate": 44100,
                        "bit_depth": 16,
                        "format": "mp3",
                        "bitrate": 128
                    },
                    "high_quality": {
                        "normalize_lufs": -14,
                        "peak_limit": -0.5,
                        "sample_rate": 48000,
                        "bit_depth": 24,
                        "format": "wav",
                        "bitrate": None
                    },
                    "voice_only": {
                        "normalize_lufs": -18,
                        "peak_limit": -1,
                        "eq_preset": "voice_clarity",
                        "noise_reduction": True,
                        "format": "mp3",
                        "bitrate": 96
                    }
                },
                "queue": [],
                "stats": {
                    "total_processed": 0,
                    "total_duration_seconds": 0,
                    "by_preset": {}
                }
            }
            self.audio_file.write_text(json.dumps(initial, indent=2))
    
    def _load_data(self) -> Dict:
        return json.loads(self.audio_file.read_text())
    
    def _save_data(self, data: Dict):
        self.audio_file.write_text(json.dumps(data, indent=2))
    
    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process queued audio jobs."""
        return self._batch_process(task or {})
    
    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute audio engineering tasks."""
        action = task.get("action", "queue_job")
        
        actions = {
            "queue_job": self._queue_job,
            "process": self._process_job,
            "batch_process": self._batch_process,
            "list_jobs": self._list_jobs,
            "get_presets": self._get_presets,
            "add_preset": self._add_preset,
            "analyze": self._analyze_audio,
            "get_queue": self._get_queue,
            "clear_queue": self._clear_queue,
            "get_stats": self._get_stats
        }
        
        if action not in actions:
            return {"error": f"Unknown action: {action}"}
        
        return self.safe_action(actions[action], task)
    
    def _queue_job(self, task: Dict) -> Dict:
        """Add audio processing job to queue."""
        data = self._load_data()
        
        job = {
            "id": str(uuid.uuid4())[:8],
            "input_file": task.get("input_file"),
            "output_file": task.get("output_file"),
            "preset": task.get("preset", "broadcast_standard"),
            "custom_settings": task.get("custom_settings", {}),
            "priority": task.get("priority", "normal"),
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        data["queue"].append(job)
        data["jobs"].append(job)
        self._save_data(data)
        
        return {"success": True, "job": job, "queue_position": len(data["queue"])}
    
    def _process_job(self, task: Dict) -> Dict:
        """Process a specific job."""
        job_id = task.get("job_id")
        data = self._load_data()
        
        job = None
        for j in data["jobs"]:
            if j["id"] == job_id:
                job = j
                break
        
        if not job:
            return {"error": f"Job not found: {job_id}"}
        
        # Get preset settings
        preset = data["presets"].get(job.get("preset", "broadcast_standard"), {})
        settings = {**preset, **job.get("custom_settings", {})}
        
        # Simulate processing
        result = {
            "job_id": job_id,
            "input_file": job["input_file"],
            "output_file": job["output_file"],
            "settings_applied": settings,
            "processing_time_ms": 1500,  # Simulated
            "status": "completed"
        }
        
        # Update job status
        job["status"] = "completed"
        job["completed_at"] = datetime.now(timezone.utc).isoformat()
        job["result"] = result
        
        # Remove from queue
        data["queue"] = [q for q in data["queue"] if q["id"] != job_id]
        
        # Update stats
        data["stats"]["total_processed"] += 1
        preset_name = job.get("preset", "custom")
        data["stats"]["by_preset"][preset_name] = data["stats"]["by_preset"].get(preset_name, 0) + 1
        
        self._save_data(data)
        
        return {"success": True, "result": result}
    
    def _batch_process(self, task: Dict) -> Dict:
        """Process all queued jobs."""
        data = self._load_data()
        
        processed = []
        for job in data["queue"][:]:
            result = self._process_job({"job_id": job["id"]})
            if result.get("success"):
                processed.append(result["result"])
        
        return {
            "success": True,
            "processed_count": len(processed),
            "results": processed
        }
    
    def _list_jobs(self, task: Dict) -> Dict:
        """List processing jobs."""
        data = self._load_data()
        jobs = data["jobs"]
        
        status = task.get("status")
        if status:
            jobs = [j for j in jobs if j["status"] == status]
        
        return {
            "success": True,
            "count": len(jobs),
            "jobs": jobs[-50:]  # Last 50
        }
    
    def _get_presets(self, task: Dict) -> Dict:
        """Get available processing presets."""
        data = self._load_data()
        
        return {
            "success": True,
            "presets": data["presets"]
        }
    
    def _add_preset(self, task: Dict) -> Dict:
        """Add a custom preset."""
        data = self._load_data()
        
        preset_name = task.get("name")
        settings = task.get("settings", {})
        
        if not preset_name:
            return {"error": "Preset name required"}
        
        data["presets"][preset_name] = settings
        self._save_data(data)
        
        return {"success": True, "preset": {preset_name: settings}}
    
    def _analyze_audio(self, task: Dict) -> Dict:
        """Analyze audio file characteristics."""
        file_path = task.get("file_path")
        
        # Simulated analysis results
        analysis = {
            "file": file_path,
            "duration_seconds": 180,  # Simulated
            "sample_rate": 44100,
            "bit_depth": 16,
            "channels": 2,
            "peak_db": -3.2,
            "rms_db": -18.5,
            "lufs": -16.8,
            "dynamic_range_db": 12.5,
            "clipping_detected": False,
            "silence_ratio": 0.02,
            "recommendations": []
        }
        
        # Generate recommendations
        if analysis["lufs"] > -14:
            analysis["recommendations"].append("Audio may be too loud for broadcast")
        if analysis["lufs"] < -20:
            analysis["recommendations"].append("Consider normalizing - audio is quiet")
        if analysis["clipping_detected"]:
            analysis["recommendations"].append("Clipping detected - reduce gain")
        
        return {"success": True, "analysis": analysis}
    
    def _get_queue(self, task: Dict) -> Dict:
        """Get current processing queue."""
        data = self._load_data()
        
        return {
            "success": True,
            "queue_length": len(data["queue"]),
            "queue": data["queue"]
        }
    
    def _clear_queue(self, task: Dict) -> Dict:
        """Clear the processing queue."""
        data = self._load_data()
        
        cleared = len(data["queue"])
        data["queue"] = []
        self._save_data(data)
        
        return {"success": True, "cleared": cleared}
    
    def _get_stats(self, task: Dict) -> Dict:
        """Get audio engineering statistics."""
        data = self._load_data()
        
        pending = len([j for j in data["jobs"] if j["status"] == "queued"])
        
        return {
            "success": True,
            "stats": {
                **data["stats"],
                "pending_jobs": pending,
                "queue_length": len(data["queue"]),
                "presets_available": len(data["presets"])
            }
        }
