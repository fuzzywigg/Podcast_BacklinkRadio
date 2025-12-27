"""
LicensingBee - Music and Content Licensing Management
======================================================

Tracks music licenses, royalty obligations, content rights,
and compliance requirements.

Type: Employed bee (admin)
Priority: High
"""

import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys

current_dir = Path(__file__).parent
bees_dir = current_dir.parent
if str(bees_dir) not in sys.path:
    sys.path.insert(0, str(bees_dir))

from base_bee import BaseBee


class LicensingBee(BaseBee):
    """Manages licensing and royalty compliance."""
    
    BEE_TYPE = "licensing"
    BEE_NAME = "LicensingBee"
    CATEGORY = "admin"
    LINEAGE_VERSION = "1.0.0"
    
    LICENSE_TYPES = ["mechanical", "performance", "sync", "master", "blanket", "creative_commons"]
    PRO_ORGANIZATIONS = ["ASCAP", "BMI", "SESAC", "GMR", "SoundExchange"]
    
    def __init__(self, hive_path: Optional[Path] = None):
        super().__init__(hive_path)
        self.licensing_file = self.honeycomb_path / "licensing.json"
        self._ensure_file()
    
    def _ensure_file(self):
        if not self.licensing_file.exists():
            initial = {
                "licenses": [],
                "tracks": [],
                "royalty_reports": [],
                "compliance_checks": [],
                "stats": {"total_licenses": 0, "active_licenses": 0, "tracks_cleared": 0, "royalties_paid": 0}
            }
            self._save_data(initial)
    
    def _load_data(self) -> Dict:
        return json.loads(self.licensing_file.read_text())
    
    def _save_data(self, data: Dict):
        self.licensing_file.write_text(json.dumps(data, indent=2))
    
    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Daily compliance check."""
        return self._compliance_check(task or {})
    
    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action", "compliance_check")
        actions = {
            "add_license": self._add_license,
            "list_licenses": self._list_licenses,
            "renew_license": self._renew_license,
            "add_track": self._add_track,
            "clear_track": self._clear_track,
            "list_tracks": self._list_tracks,
            "compliance_check": self._compliance_check,
            "expiring_soon": self._get_expiring,
            "log_royalty": self._log_royalty,
            "royalty_report": self._royalty_report,
            "get_stats": self._get_stats
        }
        if action not in actions:
            return {"error": f"Unknown action: {action}"}
        return self.safe_action(actions[action], task)
    
    def _add_license(self, task: Dict) -> Dict:
        data = self._load_data()
        license_entry = {
            "id": str(uuid.uuid4())[:8],
            "type": task.get("type", "blanket"),
            "organization": task.get("organization"),
            "name": task.get("name"),
            "cost": task.get("cost", 0),
            "start_date": task.get("start_date"),
            "end_date": task.get("end_date"),
            "auto_renew": task.get("auto_renew", False),
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        data["licenses"].append(license_entry)
        data["stats"]["total_licenses"] = len(data["licenses"])
        data["stats"]["active_licenses"] = len([l for l in data["licenses"] if l["status"] == "active"])
        self._save_data(data)
        return {"success": True, "license": license_entry}
    
    def _list_licenses(self, task: Dict) -> Dict:
        data = self._load_data()
        licenses = data["licenses"]
        if task.get("status"):
            licenses = [l for l in licenses if l["status"] == task["status"]]
        return {"success": True, "count": len(licenses), "licenses": licenses}
    
    def _renew_license(self, task: Dict) -> Dict:
        license_id = task.get("license_id")
        new_end_date = task.get("new_end_date")
        data = self._load_data()
        for lic in data["licenses"]:
            if lic["id"] == license_id:
                lic["start_date"] = lic["end_date"]
                lic["end_date"] = new_end_date
                lic["status"] = "active"
                self._save_data(data)
                return {"success": True, "license": lic}
        return {"error": f"License not found: {license_id}"}
    
    def _add_track(self, task: Dict) -> Dict:
        data = self._load_data()
        track = {
            "id": str(uuid.uuid4())[:8],
            "title": task.get("title"),
            "artist": task.get("artist"),
            "isrc": task.get("isrc"),
            "pro_affiliation": task.get("pro_affiliation"),
            "cleared": False,
            "added_at": datetime.now(timezone.utc).isoformat()
        }
        data["tracks"].append(track)
        self._save_data(data)
        return {"success": True, "track": track}
    
    def _clear_track(self, task: Dict) -> Dict:
        track_id = task.get("track_id")
        data = self._load_data()
        for track in data["tracks"]:
            if track["id"] == track_id:
                track["cleared"] = True
                track["cleared_at"] = datetime.now(timezone.utc).isoformat()
                data["stats"]["tracks_cleared"] += 1
                self._save_data(data)
                return {"success": True, "track": track}
        return {"error": f"Track not found: {track_id}"}
    
    def _list_tracks(self, task: Dict) -> Dict:
        data = self._load_data()
        tracks = data["tracks"]
        if task.get("cleared") is not None:
            tracks = [t for t in tracks if t["cleared"] == task["cleared"]]
        return {"success": True, "count": len(tracks), "tracks": tracks[-100:]}
    
    def _compliance_check(self, task: Dict) -> Dict:
        data = self._load_data()
        issues, warnings = [], []
        today = datetime.now(timezone.utc).date()
        
        for lic in data["licenses"]:
            if lic["status"] == "active" and lic.get("end_date"):
                end = datetime.fromisoformat(lic["end_date"].replace("Z", "+00:00")).date()
                if end < today:
                    issues.append({"type": "expired", "license_id": lic["id"], "name": lic.get("name")})
                    lic["status"] = "expired"
                elif end < today + timedelta(days=30):
                    warnings.append({"type": "expiring_soon", "license_id": lic["id"], "expires": lic["end_date"]})
        
        uncleared = len([t for t in data["tracks"] if not t["cleared"]])
        if uncleared:
            warnings.append({"type": "uncleared_tracks", "count": uncleared})
        
        check = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "compliant": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }
        data["compliance_checks"].append(check)
        data["compliance_checks"] = data["compliance_checks"][-50:]
        self._save_data(data)
        return {"success": True, "compliance": check}
    
    def _get_expiring(self, task: Dict) -> Dict:
        data = self._load_data()
        days = task.get("days", 30)
        today = datetime.now(timezone.utc).date()
        cutoff = today + timedelta(days=days)
        expiring = []
        for lic in data["licenses"]:
            if lic["status"] == "active" and lic.get("end_date"):
                end = datetime.fromisoformat(lic["end_date"].replace("Z", "+00:00")).date()
                if end <= cutoff:
                    expiring.append({**lic, "days_until": (end - today).days})
        return {"success": True, "expiring": sorted(expiring, key=lambda x: x["days_until"])}
    
    def _log_royalty(self, task: Dict) -> Dict:
        data = self._load_data()
        report = {
            "id": str(uuid.uuid4())[:8],
            "organization": task.get("organization"),
            "period": task.get("period"),
            "amount": task.get("amount", 0),
            "paid_at": datetime.now(timezone.utc).isoformat()
        }
        data["royalty_reports"].append(report)
        data["stats"]["royalties_paid"] += report["amount"]
        self._save_data(data)
        return {"success": True, "report": report}
    
    def _royalty_report(self, task: Dict) -> Dict:
        data = self._load_data()
        by_org = {}
        for r in data["royalty_reports"]:
            org = r["organization"]
            if org not in by_org:
                by_org[org] = {"total": 0, "count": 0}
            by_org[org]["total"] += r["amount"]
            by_org[org]["count"] += 1
        return {"success": True, "total_paid": data["stats"]["royalties_paid"], "by_organization": by_org}
    
    def _get_stats(self, task: Dict) -> Dict:
        data = self._load_data()
        return {
            "success": True,
            "stats": {
                **data["stats"],
                "total_tracks": len(data["tracks"]),
                "pending_clearance": len([t for t in data["tracks"] if not t["cleared"]])
            }
        }


if __name__ == "__main__":
    bee = LicensingBee()
    print(bee.run({"action": "get_stats"}))
