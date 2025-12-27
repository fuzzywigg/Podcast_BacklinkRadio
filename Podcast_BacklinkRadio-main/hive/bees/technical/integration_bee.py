"""
IntegrationBee - API & Webhook Integration Bee

Manages external API connections, webhooks, and integrations.
Handles data sync between the hive and third-party services.
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


class IntegrationBee(BaseBee):
    """
    Manages API integrations and webhooks.
    
    Type: Employed bee
    Priority: Normal
    Schedule: On-demand / Health checks every 5 min
    """
    
    BEE_TYPE = "integration"
    BEE_NAME = "IntegrationBee"
    CATEGORY = "technical"
    LINEAGE_VERSION = "1.0.0"
    
    def __init__(self, hive_path: Optional[Path] = None):
        super().__init__(hive_path=hive_path)
        self.integrations_file = self.honeycomb_path / "integrations.json"
        self._ensure_integrations_file()
    
    def _ensure_integrations_file(self):
        """Initialize integrations storage."""
        if not self.integrations_file.exists():
            initial = {
                "connections": [],
                "webhooks": [],
                "sync_jobs": [],
                "api_keys": {},  # Encrypted reference only
                "health_checks": [],
                "stats": {
                    "total_connections": 0,
                    "active_connections": 0,
                    "total_syncs": 0,
                    "failed_syncs": 0
                }
            }
            self.integrations_file.write_text(json.dumps(initial, indent=2))
    
    def _load_data(self) -> Dict:
        return json.loads(self.integrations_file.read_text())
    
    def _save_data(self, data: Dict):
        self.integrations_file.write_text(json.dumps(data, indent=2))
    
    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run integration health checks."""
        return self._health_check(task or {})
    
    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute integration tasks."""
        action = task.get("action", "list_connections")
        
        actions = {
            "add_connection": self._add_connection,
            "remove_connection": self._remove_connection,
            "list_connections": self._list_connections,
            "test_connection": self._test_connection,
            "add_webhook": self._add_webhook,
            "remove_webhook": self._remove_webhook,
            "list_webhooks": self._list_webhooks,
            "trigger_webhook": self._trigger_webhook,
            "sync": self._sync_data,
            "health_check": self._health_check,
            "get_stats": self._get_stats
        }
        
        if action not in actions:
            return {"error": f"Unknown action: {action}"}
        
        return self.safe_action(actions[action], task)
    
    def _add_connection(self, task: Dict) -> Dict:
        """Add a new API connection."""
        data = self._load_data()
        
        connection = {
            "id": str(uuid.uuid4())[:8],
            "name": task.get("name"),
            "service": task.get("service"),  # spotify, twitter, discord, etc.
            "type": task.get("type", "oauth"),  # oauth, api_key, basic
            "endpoint": task.get("endpoint"),
            "scopes": task.get("scopes", []),
            "rate_limit": task.get("rate_limit", {"calls": 100, "period": 60}),
            "status": "configured",
            "last_used": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        data["connections"].append(connection)
        data["stats"]["total_connections"] = len(data["connections"])
        data["stats"]["active_connections"] = len([c for c in data["connections"] if c["status"] == "active"])
        
        self._save_data(data)
        
        return {"success": True, "connection": connection}
    
    def _remove_connection(self, task: Dict) -> Dict:
        """Remove an API connection."""
        connection_id = task.get("connection_id")
        data = self._load_data()
        
        original = len(data["connections"])
        data["connections"] = [c for c in data["connections"] if c["id"] != connection_id]
        
        if len(data["connections"]) == original:
            return {"error": f"Connection not found: {connection_id}"}
        
        data["stats"]["total_connections"] = len(data["connections"])
        self._save_data(data)
        
        return {"success": True, "message": f"Removed connection: {connection_id}"}
    
    def _list_connections(self, task: Dict) -> Dict:
        """List API connections."""
        data = self._load_data()
        
        service = task.get("service")
        status = task.get("status")
        connections = data["connections"]
        
        if service:
            connections = [c for c in connections if c["service"] == service]
        if status:
            connections = [c for c in connections if c["status"] == status]
        
        return {
            "success": True,
            "count": len(connections),
            "connections": connections
        }
    
    def _test_connection(self, task: Dict) -> Dict:
        """Test an API connection."""
        connection_id = task.get("connection_id")
        data = self._load_data()
        
        connection = next((c for c in data["connections"] if c["id"] == connection_id), None)
        if not connection:
            return {"error": f"Connection not found: {connection_id}"}
        
        # Simulated test
        test_result = {
            "connection_id": connection_id,
            "service": connection["service"],
            "status": "success",
            "latency_ms": 125,
            "tested_at": datetime.now(timezone.utc).isoformat()
        }
        
        connection["status"] = "active"
        connection["last_used"] = test_result["tested_at"]
        
        data["stats"]["active_connections"] = len([c for c in data["connections"] if c["status"] == "active"])
        self._save_data(data)
        
        return {"success": True, "test_result": test_result}
    
    def _add_webhook(self, task: Dict) -> Dict:
        """Add a webhook endpoint."""
        data = self._load_data()
        
        webhook = {
            "id": str(uuid.uuid4())[:8],
            "name": task.get("name"),
            "url": task.get("url"),
            "events": task.get("events", []),  # donation, new_listener, etc.
            "secret": f"whsec_{uuid.uuid4().hex[:16]}",
            "status": "active",
            "last_triggered": None,
            "trigger_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        data["webhooks"].append(webhook)
        self._save_data(data)
        
        return {"success": True, "webhook": webhook}
    
    def _remove_webhook(self, task: Dict) -> Dict:
        """Remove a webhook."""
        webhook_id = task.get("webhook_id")
        data = self._load_data()
        
        original = len(data["webhooks"])
        data["webhooks"] = [w for w in data["webhooks"] if w["id"] != webhook_id]
        
        if len(data["webhooks"]) == original:
            return {"error": f"Webhook not found: {webhook_id}"}
        
        self._save_data(data)
        
        return {"success": True, "message": f"Removed webhook: {webhook_id}"}
    
    def _list_webhooks(self, task: Dict) -> Dict:
        """List webhooks."""
        data = self._load_data()
        
        event = task.get("event")
        webhooks = data["webhooks"]
        
        if event:
            webhooks = [w for w in webhooks if event in w["events"]]
        
        return {
            "success": True,
            "count": len(webhooks),
            "webhooks": webhooks
        }
    
    def _trigger_webhook(self, task: Dict) -> Dict:
        """Trigger a webhook."""
        webhook_id = task.get("webhook_id")
        payload = task.get("payload", {})
        
        data = self._load_data()
        
        webhook = next((w for w in data["webhooks"] if w["id"] == webhook_id), None)
        if not webhook:
            return {"error": f"Webhook not found: {webhook_id}"}
        
        # Simulated trigger
        result = {
            "webhook_id": webhook_id,
            "url": webhook["url"],
            "status": "delivered",
            "response_code": 200,
            "triggered_at": datetime.now(timezone.utc).isoformat()
        }
        
        webhook["last_triggered"] = result["triggered_at"]
        webhook["trigger_count"] += 1
        self._save_data(data)
        
        return {"success": True, "result": result}
    
    def _sync_data(self, task: Dict) -> Dict:
        """Sync data with an integration."""
        connection_id = task.get("connection_id")
        sync_type = task.get("sync_type", "full")
        
        data = self._load_data()
        
        connection = next((c for c in data["connections"] if c["id"] == connection_id), None)
        if not connection:
            return {"error": f"Connection not found: {connection_id}"}
        
        sync_job = {
            "id": str(uuid.uuid4())[:8],
            "connection_id": connection_id,
            "service": connection["service"],
            "sync_type": sync_type,
            "status": "completed",
            "records_synced": 50,  # Simulated
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        
        data["sync_jobs"].append(sync_job)
        data["stats"]["total_syncs"] += 1
        
        connection["last_used"] = sync_job["completed_at"]
        self._save_data(data)
        
        return {"success": True, "sync_job": sync_job}
    
    def _health_check(self, task: Dict) -> Dict:
        """Check health of all integrations."""
        data = self._load_data()
        
        results = []
        for connection in data["connections"]:
            health = {
                "connection_id": connection["id"],
                "service": connection["service"],
                "status": connection["status"],
                "healthy": connection["status"] == "active",
                "last_used": connection["last_used"],
                "checked_at": datetime.now(timezone.utc).isoformat()
            }
            results.append(health)
        
        healthy_count = len([r for r in results if r["healthy"]])
        
        check = {
            "total_connections": len(results),
            "healthy": healthy_count,
            "unhealthy": len(results) - healthy_count,
            "results": results,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
        
        data["health_checks"].append(check)
        data["health_checks"] = data["health_checks"][-100:]  # Keep last 100
        self._save_data(data)
        
        return {"success": True, "health_check": check}
    
    def _get_stats(self, task: Dict) -> Dict:
        """Get integration statistics."""
        data = self._load_data()
        
        return {
            "success": True,
            "stats": {
                **data["stats"],
                "webhooks_count": len(data["webhooks"]),
                "recent_syncs": len(data["sync_jobs"])
            }
        }
