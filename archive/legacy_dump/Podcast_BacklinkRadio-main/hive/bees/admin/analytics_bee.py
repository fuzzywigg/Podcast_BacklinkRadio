"""
Analytics Bee - Aggregates metrics and generates insights.

NORMAL PRIORITY BEE - Data aggregation and visualization.

Responsibilities:
- Aggregate metrics from all bees
- Generate dashboard data
- Trend analysis
- Performance tracking
- KPI monitoring
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
import json
from collections import defaultdict

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from base_bee import OnlookerBee


class AnalyticsBee(OnlookerBee):
    """
    Aggregates and analyzes station metrics.
    
    This bee gathers data from all sources and provides
    unified analytics and insights.
    """

    BEE_TYPE = "analytics"
    BEE_NAME = "Analytics Bee"
    CATEGORY = "admin"

    # Key Performance Indicators
    KPIS = {
        "listener_retention": {"target": 0.7, "unit": "percentage"},
        "engagement_rate": {"target": 0.3, "unit": "percentage"},
        "donation_conversion": {"target": 0.05, "unit": "percentage"},
        "vip_percentage": {"target": 0.1, "unit": "percentage"},
        "content_frequency": {"target": 4, "unit": "posts_per_day"},
        "stream_uptime": {"target": 0.99, "unit": "percentage"}
    }

    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process analytics tasks.

        Task payload actions:
        - dashboard: Generate dashboard data
        - daily_metrics: Calculate daily metrics
        - weekly_summary: Generate weekly summary
        - kpi_check: Check KPI status
        - trend_analysis: Analyze trends
        - export_data: Export analytics data
        """
        self.log("Analytics Bee activated...")

        if not task:
            return self._generate_dashboard()

        action = task.get("payload", {}).get("action", "dashboard")

        if action == "dashboard":
            return self._generate_dashboard()
        elif action == "daily_metrics":
            return self._calculate_daily_metrics()
        elif action == "weekly_summary":
            return self._generate_weekly_summary()
        elif action == "kpi_check":
            return self._check_kpis()
        elif action == "trend_analysis":
            return self._analyze_trends(task)
        elif action == "export_data":
            return self._export_data(task)
        elif action == "listener_analytics":
            return self._listener_analytics()

        return {"error": f"Unknown action: {action}"}

    def _generate_dashboard(self) -> Dict[str, Any]:
        """Generate comprehensive dashboard data."""
        self.log("Generating dashboard data...")

        # Collect data from all sources
        state = self.read_state()
        intel = self.read_intel()

        # Build dashboard
        dashboard = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "station_status": self._get_station_status(state),
            "audience": self._get_audience_metrics(intel),
            "economy": self._get_economy_metrics(state),
            "content": self._get_content_metrics(intel),
            "kpis": self._calculate_kpis(state, intel),
            "alerts": self._get_active_alerts(state)
        }

        return {
            "action": "dashboard",
            "dashboard": dashboard
        }

    def _get_station_status(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get current station status."""
        broadcast = state.get("broadcast", {})
        health = state.get("health", {})

        return {
            "is_live": broadcast.get("is_live", False),
            "current_track": broadcast.get("current_track"),
            "persona_mode": broadcast.get("persona_mode", "day"),
            "stream_health": health.get("status", "unknown"),
            "uptime_percentage": health.get("uptime_percentage", 0),
            "last_heartbeat": state.get("_meta", {}).get("last_updated")
        }

    def _get_audience_metrics(self, intel: Dict[str, Any]) -> Dict[str, Any]:
        """Get audience/listener metrics."""
        listeners = intel.get("listeners", {})
        known_nodes = listeners.get("known_nodes", {})

        total_listeners = len(known_nodes)
        vip_count = sum(1 for n in known_nodes.values() if n.get("is_vip"))
        active_today = sum(
            1 for n in known_nodes.values()
            if n.get("last_seen", "").startswith(datetime.now(timezone.utc).date().isoformat())
        )

        # Calculate engagement metrics
        total_interactions = sum(
            int(n.get("interaction_count", 0)) for n in known_nodes.values()
        )

        return {
            "total_listeners": total_listeners,
            "vip_count": vip_count,
            "vip_percentage": round(vip_count / total_listeners * 100, 1) if total_listeners > 0 else 0,
            "active_today": active_today,
            "total_interactions": total_interactions,
            "avg_interactions_per_listener": round(total_interactions / total_listeners, 1) if total_listeners > 0 else 0
        }

    def _get_economy_metrics(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get economy/financial metrics."""
        economy = state.get("economy", {})

        return {
            "donations_today": economy.get("total_donations_today", 0),
            "donation_count_today": economy.get("donation_count_today", 0),
            "pending_shoutouts": len(economy.get("pending_shoutouts", [])),
            "last_donation_at": economy.get("last_donation_at")
        }

    def _get_content_metrics(self, intel: Dict[str, Any]) -> Dict[str, Any]:
        """Get content performance metrics."""
        content = intel.get("content_performance", {})
        trends = intel.get("trends", {})

        # Handle trends.current - can be a list of trend objects or a dict
        current_trends = trends.get("current", [])
        if isinstance(current_trends, list):
            # Extract titles from trend objects
            trending_topics = [t.get("title", "Unknown") for t in current_trends[:5]]
        else:
            # Legacy dict format - use keys
            trending_topics = list(current_trends.keys())[:5]
            
        return {
            "posts_today": content.get("posts_today", 0),
            "total_engagement": content.get("total_engagement", 0),
            "top_performing": content.get("top_performing", [])[:3],
            "trending_topics": trending_topics
        }

    def _calculate_kpis(self, state: Dict, intel: Dict) -> Dict[str, Any]:
        """Calculate KPI status."""
        kpi_results = {}
        listeners = intel.get("listeners", {}).get("known_nodes", {})
        total_listeners = len(listeners)

        # Listener retention (stub - would need historical data)
        kpi_results["listener_retention"] = {
            "current": 0.65,  # Placeholder
            "target": self.KPIS["listener_retention"]["target"],
            "status": "on_track"  # Would calculate based on current vs target
        }

        # VIP percentage
        vip_count = sum(1 for n in listeners.values() if n.get("is_vip"))
        vip_pct = vip_count / total_listeners if total_listeners > 0 else 0
        kpi_results["vip_percentage"] = {
            "current": round(vip_pct, 3),
            "target": self.KPIS["vip_percentage"]["target"],
            "status": "on_track" if vip_pct >= self.KPIS["vip_percentage"]["target"] else "below_target"
        }

        # Stream uptime
        health = state.get("health", {})
        uptime = health.get("uptime_percentage", 0)
        kpi_results["stream_uptime"] = {
            "current": uptime,
            "target": self.KPIS["stream_uptime"]["target"],
            "status": "on_track" if uptime >= self.KPIS["stream_uptime"]["target"] else "below_target"
        }

        return kpi_results

    def _get_active_alerts(self, state: Dict[str, Any]) -> List[Dict]:
        """Get active alerts."""
        alerts = state.get("alerts", {})
        priority = alerts.get("priority", [])
        normal = alerts.get("normal", [])

        return {
            "priority_count": len(priority),
            "normal_count": len(normal),
            "recent_priority": priority[:3],
            "recent_normal": normal[:3]
        }

    def _calculate_daily_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive daily metrics."""
        state = self.read_state()
        intel = self.read_intel()

        metrics = {
            "date": datetime.now(timezone.utc).date().isoformat(),
            "audience": self._get_audience_metrics(intel),
            "economy": self._get_economy_metrics(state),
            "content": self._get_content_metrics(intel),
            "health": state.get("health", {})
        }

        # Store metrics for historical analysis
        self._store_daily_metrics(metrics)

        return {
            "action": "daily_metrics",
            "metrics": metrics
        }

    def _store_daily_metrics(self, metrics: Dict[str, Any]) -> None:
        """Store daily metrics for historical analysis."""
        metrics_log = self.hive_path / "analytics_history.jsonl"

        with open(metrics_log, "a") as f:
            f.write(json.dumps(metrics) + "\n")

    def _generate_weekly_summary(self) -> Dict[str, Any]:
        """Generate weekly summary from stored metrics."""
        metrics_log = self.hive_path / "analytics_history.jsonl"

        week_data = []
        if metrics_log.exists():
            week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
            with open(metrics_log, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if data.get("date", "") >= week_ago:
                            week_data.append(data)
                    except json.JSONDecodeError:
                        continue

        # Aggregate weekly stats
        if not week_data:
            return {
                "action": "weekly_summary",
                "summary": {"note": "No data available for this week"}
            }

        summary = {
            "period": {
                "start": week_ago,
                "end": datetime.now(timezone.utc).date().isoformat()
            },
            "days_with_data": len(week_data),
            "totals": {
                "donations": sum(d.get("economy", {}).get("donations_today", 0) for d in week_data),
                "new_listeners": 0,  # Would calculate from delta
                "interactions": sum(d.get("audience", {}).get("total_interactions", 0) for d in week_data)
            },
            "averages": {
                "daily_donations": sum(d.get("economy", {}).get("donations_today", 0) for d in week_data) / len(week_data),
                "active_listeners": sum(d.get("audience", {}).get("active_today", 0) for d in week_data) / len(week_data)
            }
        }

        return {
            "action": "weekly_summary",
            "summary": summary
        }

    def _check_kpis(self) -> Dict[str, Any]:
        """Check all KPIs and generate alerts for issues."""
        state = self.read_state()
        intel = self.read_intel()

        kpis = self._calculate_kpis(state, intel)

        alerts = []
        for kpi_name, kpi_data in kpis.items():
            if kpi_data.get("status") == "below_target":
                alerts.append({
                    "kpi": kpi_name,
                    "current": kpi_data.get("current"),
                    "target": kpi_data.get("target"),
                    "message": f"{kpi_name} is below target ({kpi_data.get('current')} vs {kpi_data.get('target')})"
                })

        # Post alerts for critical KPIs
        for alert in alerts:
            if alert["kpi"] in ["stream_uptime", "listener_retention"]:
                self.post_alert(f"📊 KPI Alert: {alert['message']}", priority=True)

        return {
            "action": "kpi_check",
            "kpis": kpis,
            "alerts": alerts
        }

    def _analyze_trends(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trends over time."""
        payload = task.get("payload", {})
        metric = payload.get("metric", "donations")
        period_days = payload.get("period_days", 7)

        metrics_log = self.hive_path / "analytics_history.jsonl"

        data_points = []
        if metrics_log.exists():
            cutoff = (datetime.now(timezone.utc) - timedelta(days=period_days)).date().isoformat()
            with open(metrics_log, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if data.get("date", "") >= cutoff:
                            data_points.append(data)
                    except json.JSONDecodeError:
                        continue

        if len(data_points) < 2:
            return {
                "action": "trend_analysis",
                "metric": metric,
                "trend": "insufficient_data"
            }

        # Calculate trend (simple linear)
        values = []
        for dp in data_points:
            if metric == "donations":
                values.append(dp.get("economy", {}).get("donations_today", 0))
            elif metric == "listeners":
                values.append(dp.get("audience", {}).get("total_listeners", 0))
            elif metric == "interactions":
                values.append(dp.get("audience", {}).get("total_interactions", 0))

        # Simple trend detection
        first_half = sum(values[:len(values)//2]) / (len(values)//2) if values else 0
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2) if values else 0

        if second_half > first_half * 1.1:
            trend = "increasing"
        elif second_half < first_half * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"

        return {
            "action": "trend_analysis",
            "metric": metric,
            "period_days": period_days,
            "data_points": len(values),
            "trend": trend,
            "first_half_avg": round(first_half, 2),
            "second_half_avg": round(second_half, 2)
        }

    def _listener_analytics(self) -> Dict[str, Any]:
        """Detailed listener analytics."""
        intel = self.read_intel()
        listeners = intel.get("listeners", {}).get("known_nodes", {})

        # Segment listeners
        segments = {
            "vips": [],
            "donors": [],
            "active": [],
            "dormant": []
        }

        for node_id, data in listeners.items():
            if data.get("is_vip"):
                segments["vips"].append(node_id)
            if data.get("donation_total", 0) > 0:
                segments["donors"].append(node_id)
            if data.get("interaction_count", 0) > 5:
                segments["active"].append(node_id)
            else:
                segments["dormant"].append(node_id)

        return {
            "action": "listener_analytics",
            "total_listeners": len(listeners),
            "segments": {
                "vips": len(segments["vips"]),
                "donors": len(segments["donors"]),
                "active": len(segments["active"]),
                "dormant": len(segments["dormant"])
            },
            "engagement_distribution": self._calculate_engagement_distribution(listeners)
        }

    def _calculate_engagement_distribution(self, listeners: Dict) -> Dict[str, int]:
        """Calculate engagement score distribution."""
        distribution = {
            "high": 0,     # >0.7
            "medium": 0,   # 0.3-0.7
            "low": 0       # <0.3
        }

        for data in listeners.values():
            score = data.get("engagement_score", 0)
            if score > 0.7:
                distribution["high"] += 1
            elif score > 0.3:
                distribution["medium"] += 1
            else:
                distribution["low"] += 1

        return distribution

    def _export_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Export analytics data in specified format."""
        payload = task.get("payload", {})
        format_type = payload.get("format", "json")
        data_type = payload.get("data", "dashboard")

        if data_type == "dashboard":
            data = self._generate_dashboard().get("dashboard")
        elif data_type == "weekly":
            data = self._generate_weekly_summary().get("summary")
        else:
            data = self._calculate_daily_metrics().get("metrics")

        return {
            "action": "export_data",
            "format": format_type,
            "data_type": data_type,
            "data": data
        }


if __name__ == "__main__":
    bee = AnalyticsBee()
    result = bee.run()
    print(result)
