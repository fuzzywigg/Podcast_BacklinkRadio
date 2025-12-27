"""
Revenue Analyst Bee - Tracks and analyzes revenue streams.

HIGH PRIORITY BEE - Financial visibility and insights.

Responsibilities:
- Track all revenue streams (donations, sponsors, merch)
- Generate revenue reports
- Identify optimization opportunities
- Forecast revenue trends
- Monitor financial health
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


class RevenueAnalystBee(OnlookerBee):
    """
    Analyzes revenue streams and provides financial insights.
    
    This bee observes financial data and identifies patterns,
    opportunities, and potential issues.
    """

    BEE_TYPE = "revenue_analyst"
    BEE_NAME = "Revenue Analyst Bee"
    CATEGORY = "monetization"

    # Revenue stream categories
    REVENUE_STREAMS = {
        "donations": {"color": "green", "priority": 1},
        "sponsorships": {"color": "blue", "priority": 2},
        "merch": {"color": "purple", "priority": 3},
        "premium": {"color": "gold", "priority": 4},
        "tips": {"color": "teal", "priority": 5}
    }

    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process revenue analysis tasks.

        Task payload actions:
        - daily_report: Generate daily revenue report
        - weekly_report: Generate weekly summary
        - monthly_report: Generate monthly analysis
        - stream_analysis: Analyze specific revenue stream
        - forecast: Generate revenue forecast
        - health_check: Assess financial health
        """
        self.log("Revenue Analyst activated...")

        if not task:
            return self._daily_analysis()

        action = task.get("payload", {}).get("action", "daily_report")

        if action == "daily_report":
            return self._generate_daily_report()
        elif action == "weekly_report":
            return self._generate_weekly_report()
        elif action == "monthly_report":
            return self._generate_monthly_report()
        elif action == "stream_analysis":
            return self._analyze_stream(task)
        elif action == "forecast":
            return self._generate_forecast(task)
        elif action == "health_check":
            return self._financial_health_check()
        elif action == "top_donors":
            return self._get_top_donors(task)

        return {"error": f"Unknown action: {action}"}

    def _daily_analysis(self) -> Dict[str, Any]:
        """Run daily revenue analysis routine."""
        self.log("Running daily revenue analysis...")

        # Gather data from all sources
        daily_data = self._collect_daily_data()
        
        # Calculate metrics
        metrics = self._calculate_metrics(daily_data)
        
        # Check for anomalies
        anomalies = self._detect_anomalies(daily_data)
        
        # Generate insights
        insights = self._generate_insights(daily_data, metrics)

        # Update state with analysis
        self._update_revenue_state(metrics)

        return {
            "action": "daily_analysis",
            "date": datetime.now(timezone.utc).date().isoformat(),
            "metrics": metrics,
            "anomalies": anomalies,
            "insights": insights
        }

    def _collect_daily_data(self) -> Dict[str, Any]:
        """Collect revenue data from all sources."""
        data = {
            "donations": [],
            "sponsorships": [],
            "economy_state": {},
            "intel": {}
        }

        # Read treasury events (append-only log)
        treasury_log = self.hive_path / "treasury_events.jsonl"
        if treasury_log.exists():
            today = datetime.now(timezone.utc).date().isoformat()
            with open(treasury_log, 'r') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        if event.get("timestamp", "").startswith(today):
                            if event.get("type") == "DONATION":
                                data["donations"].append(event)
                    except json.JSONDecodeError:
                        continue

        # Read current state
        state = self.read_state()
        data["economy_state"] = state.get("economy", {})

        # Read intel for donor/sponsor data
        intel = self.read_intel()
        data["intel"] = intel

        return data

    def _calculate_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate key revenue metrics."""
        donations = data.get("donations", [])
        economy = data.get("economy_state", {})

        # Daily donation metrics
        donation_amounts = [float(d.get("amount", 0)) for d in donations]
        total_donations = sum(donation_amounts)
        donation_count = len(donations)
        avg_donation = total_donations / donation_count if donation_count > 0 else 0

        # Tier breakdown
        tier_breakdown = defaultdict(int)
        for d in donations:
            tier = d.get("tier", "unknown")
            tier_breakdown[tier] += 1

        # Donor analysis
        unique_donors = len(set(d.get("donor", "") for d in donations))
        
        metrics = {
            "date": datetime.now(timezone.utc).date().isoformat(),
            "donations": {
                "total": total_donations,
                "count": donation_count,
                "average": round(avg_donation, 2),
                "unique_donors": unique_donors,
                "tier_breakdown": dict(tier_breakdown)
            },
            "cumulative": {
                "today": economy.get("total_donations_today", 0),
                "pending_shoutouts": len(economy.get("pending_shoutouts", []))
            }
        }

        return metrics

    def _detect_anomalies(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect unusual patterns in revenue data."""
        anomalies = []
        donations = data.get("donations", [])

        if not donations:
            return anomalies

        amounts = [float(d.get("amount", 0)) for d in donations]
        avg = sum(amounts) / len(amounts)
        
        # Check for unusually large donations
        for d in donations:
            amount = float(d.get("amount", 0))
            if amount > avg * 5 and amount > 50:  # 5x average and > $50
                anomalies.append({
                    "type": "large_donation",
                    "donor": d.get("donor"),
                    "amount": amount,
                    "threshold": avg * 5,
                    "note": "Unusually large donation - verify and celebrate!"
                })

        # Check for potential fraud patterns
        donor_counts = defaultdict(int)
        for d in donations:
            donor_counts[d.get("donor", "")] += 1

        for donor, count in donor_counts.items():
            if count > 10:  # More than 10 donations in a day
                anomalies.append({
                    "type": "high_frequency",
                    "donor": donor,
                    "count": count,
                    "note": "High donation frequency - could be superfan or fraud"
                })

        return anomalies

    def _generate_insights(self, data: Dict, metrics: Dict) -> List[str]:
        """Generate actionable insights from the data."""
        insights = []
        donations = metrics.get("donations", {})

        # Donation insights
        if donations.get("count", 0) == 0:
            insights.append("No donations today - consider engagement boost")
        elif donations.get("average", 0) > 20:
            insights.append(f"Strong average donation (${donations['average']}) - audience is engaged")
        
        # Tier insights
        tier_breakdown = donations.get("tier_breakdown", {})
        if tier_breakdown.get("mega", 0) > 0:
            insights.append(f"🏆 {tier_breakdown['mega']} MEGA donation(s) today!")
        
        if donations.get("unique_donors", 0) > 10:
            insights.append(f"Broad support: {donations['unique_donors']} unique donors")

        return insights

    def _generate_daily_report(self) -> Dict[str, Any]:
        """Generate formatted daily revenue report."""
        data = self._collect_daily_data()
        metrics = self._calculate_metrics(data)
        insights = self._generate_insights(data, metrics)

        report = {
            "type": "daily",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "date": datetime.now(timezone.utc).date().isoformat(),
            "summary": {
                "total_revenue": metrics["donations"]["total"],
                "transaction_count": metrics["donations"]["count"],
                "unique_supporters": metrics["donations"]["unique_donors"]
            },
            "breakdown_by_stream": {
                "donations": metrics["donations"]
            },
            "insights": insights,
            "metrics": metrics
        }

        return {"action": "daily_report", "report": report}

    def _generate_weekly_report(self) -> Dict[str, Any]:
        """Generate weekly revenue summary."""
        # Read last 7 days of data
        treasury_log = self.hive_path / "treasury_events.jsonl"
        weekly_data = defaultdict(list)
        
        if treasury_log.exists():
            week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            with open(treasury_log, 'r') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        if event.get("timestamp", "") >= week_ago:
                            date = event.get("timestamp", "")[:10]
                            weekly_data[date].append(event)
                    except json.JSONDecodeError:
                        continue

        # Calculate weekly totals
        daily_totals = {}
        week_total = 0
        for date, events in weekly_data.items():
            day_total = sum(float(e.get("amount", 0)) for e in events if e.get("type") == "DONATION")
            daily_totals[date] = day_total
            week_total += day_total

        report = {
            "type": "weekly",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period": {
                "start": (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat(),
                "end": datetime.now(timezone.utc).date().isoformat()
            },
            "total_revenue": week_total,
            "daily_breakdown": daily_totals,
            "average_daily": round(week_total / 7, 2) if week_total > 0 else 0,
            "transaction_count": sum(len(v) for v in weekly_data.values())
        }

        return {"action": "weekly_report", "report": report}

    def _generate_monthly_report(self) -> Dict[str, Any]:
        """Generate monthly revenue analysis."""
        # Similar to weekly but for 30 days
        treasury_log = self.hive_path / "treasury_events.jsonl"
        monthly_data = defaultdict(list)
        
        if treasury_log.exists():
            month_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            with open(treasury_log, 'r') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        if event.get("timestamp", "") >= month_ago:
                            date = event.get("timestamp", "")[:10]
                            monthly_data[date].append(event)
                    except json.JSONDecodeError:
                        continue

        # Calculate monthly totals
        month_total = 0
        unique_donors = set()
        tier_counts = defaultdict(int)

        for date, events in monthly_data.items():
            for event in events:
                if event.get("type") == "DONATION":
                    month_total += float(event.get("amount", 0))
                    unique_donors.add(event.get("donor", ""))
                    tier_counts[event.get("tier", "unknown")] += 1

        report = {
            "type": "monthly",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period": {
                "start": (datetime.now(timezone.utc) - timedelta(days=30)).date().isoformat(),
                "end": datetime.now(timezone.utc).date().isoformat()
            },
            "total_revenue": month_total,
            "unique_supporters": len(unique_donors),
            "tier_breakdown": dict(tier_counts),
            "average_daily": round(month_total / 30, 2) if month_total > 0 else 0,
            "days_with_donations": len(monthly_data)
        }

        return {"action": "monthly_report", "report": report}

    def _analyze_stream(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a specific revenue stream."""
        payload = task.get("payload", {})
        stream = payload.get("stream", "donations")

        if stream not in self.REVENUE_STREAMS:
            return {"error": f"Unknown stream: {stream}"}

        # For now, we mainly have donation data
        if stream == "donations":
            data = self._collect_daily_data()
            metrics = self._calculate_metrics(data)
            return {
                "action": "stream_analysis",
                "stream": stream,
                "analysis": metrics.get("donations", {})
            }

        return {
            "action": "stream_analysis",
            "stream": stream,
            "analysis": {"note": f"Stream {stream} analysis not yet implemented"}
        }

    def _generate_forecast(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate revenue forecast based on historical data."""
        payload = task.get("payload", {})
        days_ahead = payload.get("days", 30)

        # Get historical weekly average
        weekly_report = self._generate_weekly_report()
        weekly_avg = weekly_report.get("report", {}).get("average_daily", 0)

        # Simple forecast (in production, use more sophisticated models)
        forecast = {
            "period_days": days_ahead,
            "method": "simple_average",
            "predicted_daily": weekly_avg,
            "predicted_total": round(weekly_avg * days_ahead, 2),
            "confidence": "low",  # Simple average = low confidence
            "note": "Forecast based on 7-day rolling average"
        }

        return {"action": "forecast", "forecast": forecast}

    def _financial_health_check(self) -> Dict[str, Any]:
        """Assess overall financial health of the station."""
        weekly = self._generate_weekly_report().get("report", {})
        
        week_total = weekly.get("total_revenue", 0)
        daily_avg = weekly.get("average_daily", 0)
        
        # Simple health scoring
        health_score = 0
        health_notes = []

        if daily_avg >= 50:
            health_score += 40
            health_notes.append("Strong daily revenue")
        elif daily_avg >= 20:
            health_score += 25
            health_notes.append("Moderate daily revenue")
        elif daily_avg > 0:
            health_score += 10
            health_notes.append("Light daily revenue")
        else:
            health_notes.append("No revenue this week")

        if weekly.get("transaction_count", 0) >= 20:
            health_score += 30
            health_notes.append("Good transaction volume")
        elif weekly.get("transaction_count", 0) >= 5:
            health_score += 15
            health_notes.append("Moderate transaction volume")

        # Determine health status
        if health_score >= 60:
            status = "healthy"
        elif health_score >= 30:
            status = "fair"
        else:
            status = "needs_attention"

        return {
            "action": "health_check",
            "health": {
                "score": health_score,
                "status": status,
                "notes": health_notes,
                "week_total": week_total,
                "daily_avg": daily_avg
            }
        }

    def _get_top_donors(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get top donors by total contributions."""
        payload = task.get("payload", {})
        limit = payload.get("limit", 10)
        period = payload.get("period", "all")  # all, week, month

        intel = self.read_intel()
        known_nodes = intel.get("listeners", {}).get("known_nodes", {})

        donors = []
        for node_id, data in known_nodes.items():
            donation_total = float(data.get("donation_total", 0))
            if donation_total > 0:
                donors.append({
                    "node": node_id,
                    "total": donation_total,
                    "tier": data.get("vip_tier"),
                    "is_vip": data.get("is_vip", False)
                })

        # Sort by total donations
        donors.sort(key=lambda x: x["total"], reverse=True)

        return {
            "action": "top_donors",
            "period": period,
            "top_donors": donors[:limit]
        }

    def _update_revenue_state(self, metrics: Dict[str, Any]) -> None:
        """Update state with latest revenue metrics."""
        self.write_state({
            "revenue_metrics": {
                "last_analysis": datetime.now(timezone.utc).isoformat(),
                "today": metrics
            }
        })


if __name__ == "__main__":
    bee = RevenueAnalystBee()
    result = bee.run()
    print(result)
