"""
JingleBee - Station Audio Identity Bee

Creates station IDs, drops, bumpers, and audio branding assets.
Manages the audio identity of the station.
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


class JingleBee(BaseBee):
    """
    Creates and manages station audio branding.
    
    Type: Employed bee
    Priority: Normal
    Schedule: On-demand / Weekly review
    """
    
    BEE_TYPE = "jingle"
    BEE_NAME = "JingleBee"
    CATEGORY = "content"
    LINEAGE_VERSION = "1.0.0"
    
    def __init__(self, hive_path: Optional[Path] = None):
        super().__init__(hive_path=hive_path)
        self.jingles_file = self.honeycomb_path / "jingles.json"
        self._ensure_jingles_file()
    
    def _ensure_jingles_file(self):
        """Initialize jingles storage if needed."""
        if not self.jingles_file.exists():
            initial = {
                "assets": [],
                "templates": {
                    "station_id": {
                        "duration_target": 10,
                        "elements": ["station_name", "tagline", "frequency"]
                    },
                    "bumper": {
                        "duration_target": 5,
                        "elements": ["transition_sound", "station_name"]
                    },
                    "drop": {
                        "duration_target": 3,
                        "elements": ["effect", "phrase"]
                    },
                    "sweeper": {
                        "duration_target": 8,
                        "elements": ["music_bed", "voiceover", "effect"]
                    },
                    "show_intro": {
                        "duration_target": 30,
                        "elements": ["theme_music", "host_intro", "show_name"]
                    },
                    "show_outro": {
                        "duration_target": 20,
                        "elements": ["theme_music", "credits", "cta"]
                    }
                },
                "brand_elements": {
                    "station_name": "Backlink Broadcast",
                    "tagline": "Your AI-Powered Radio",
                    "frequency": "Internet Radio",
                    "voice_style": "energetic, friendly, modern"
                },
                "stats": {
                    "total_created": 0,
                    "by_type": {}
                }
            }
            self.jingles_file.write_text(json.dumps(initial, indent=2))
    
    def _load_jingles(self) -> Dict:
        return json.loads(self.jingles_file.read_text())
    
    def _save_jingles(self, data: Dict):
        self.jingles_file.write_text(json.dumps(data, indent=2))
    
    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Review jingle library status."""
        return self._get_stats(task or {})
    
    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute jingle creation tasks."""
        action = task.get("action", "list")
        
        actions = {
            "create": self._create_asset,
            "list": self._list_assets,
            "get_template": self._get_template,
            "update_brand": self._update_brand,
            "get_stats": self._get_stats,
            "generate_script": self._generate_script,
            "archive": self._archive_asset
        }
        
        if action not in actions:
            return {"error": f"Unknown action: {action}"}
        
        return actions[action](task)
    
    def _create_asset(self, task: Dict) -> Dict:
        """Create a new jingle/audio asset."""
        asset_type = task.get("type", "station_id")
        name = task.get("name", f"{asset_type}_{datetime.now().strftime('%Y%m%d')}")
        
        data = self._load_jingles()
        template = data["templates"].get(asset_type, {})
        
        asset = {
            "id": str(uuid.uuid4())[:8],
            "type": asset_type,
            "name": name,
            "status": "draft",
            "duration_target": template.get("duration_target", 10),
            "elements": template.get("elements", []),
            "script": task.get("script", ""),
            "voice_notes": task.get("voice_notes", data["brand_elements"]["voice_style"]),
            "music_bed": task.get("music_bed"),
            "audio_file": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        data["assets"].append(asset)
        data["stats"]["total_created"] += 1
        data["stats"]["by_type"][asset_type] = data["stats"]["by_type"].get(asset_type, 0) + 1
        
        self._save_jingles(data)
        
        return {
            "success": True,
            "asset": asset,
            "message": f"Created {asset_type} asset: {name}"
        }
    
    def _list_assets(self, task: Dict) -> Dict:
        """List jingle assets with optional filtering."""
        data = self._load_jingles()
        assets = data["assets"]
        
        asset_type = task.get("type")
        status = task.get("status")
        
        if asset_type:
            assets = [a for a in assets if a["type"] == asset_type]
        if status:
            assets = [a for a in assets if a["status"] == status]
        
        return {
            "success": True,
            "count": len(assets),
            "assets": assets[-20:]  # Last 20
        }
    
    def _get_template(self, task: Dict) -> Dict:
        """Get template for asset type."""
        data = self._load_jingles()
        asset_type = task.get("type", "station_id")
        
        template = data["templates"].get(asset_type)
        if not template:
            return {"error": f"Unknown asset type: {asset_type}"}
        
        return {
            "success": True,
            "type": asset_type,
            "template": template,
            "brand": data["brand_elements"]
        }
    
    def _update_brand(self, task: Dict) -> Dict:
        """Update brand elements."""
        data = self._load_jingles()
        
        updates = task.get("updates", {})
        for key, value in updates.items():
            if key in data["brand_elements"]:
                data["brand_elements"][key] = value
        
        self._save_jingles(data)
        
        return {
            "success": True,
            "brand": data["brand_elements"]
        }
    
    def _generate_script(self, task: Dict) -> Dict:
        """Generate script for jingle type."""
        asset_type = task.get("type", "station_id")
        data = self._load_jingles()
        brand = data["brand_elements"]
        
        scripts = {
            "station_id": f"You're listening to {brand['station_name']}... {brand['tagline']}!",
            "bumper": f"{brand['station_name']}... we'll be right back!",
            "drop": f"{brand['station_name']}!",
            "sweeper": f"This is {brand['station_name']}, {brand['tagline']}. Stay tuned!"
        }
        
        return {
            "success": True,
            "type": asset_type,
            "script": scripts.get(asset_type, f"{brand['station_name']}"),
            "voice_style": brand["voice_style"]
        }
    
    def _archive_asset(self, task: Dict) -> Dict:
        """Archive an asset."""
        asset_id = task.get("asset_id")
        data = self._load_jingles()
        
        for asset in data["assets"]:
            if asset["id"] == asset_id:
                asset["status"] = "archived"
                asset["updated_at"] = datetime.now(timezone.utc).isoformat()
                self._save_jingles(data)
                return {"success": True, "message": f"Archived asset {asset_id}"}
        
        return {"error": f"Asset not found: {asset_id}"}
    
    def _get_stats(self, task: Dict) -> Dict:
        """Get jingle statistics."""
        data = self._load_jingles()
        
        active = [a for a in data["assets"] if a["status"] != "archived"]
        
        return {
            "success": True,
            "stats": {
                "total_created": data["stats"]["total_created"],
                "active_assets": len(active),
                "by_type": data["stats"]["by_type"],
                "templates_available": list(data["templates"].keys())
            }
        }
