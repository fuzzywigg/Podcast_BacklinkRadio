"""
SEOBee - Optimizes discoverability and metadata for the radio station.

An Employed bee that manages SEO, metadata optimization, and search
visibility across all station content and platforms.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class SEOBee:
    """
    SEOBee - Search engine optimization and discoverability.
    
    Responsibilities:
    - Optimize content metadata
    - Generate SEO-friendly descriptions
    - Track keyword performance
    - Analyze search visibility
    - Suggest tag improvements
    
    Outputs:
    - SEO recommendations
    - Optimized metadata
    - Keyword reports
    - Tag suggestions
    """
    
    BEE_TYPE = "employed"
    PRIORITY = "low"
    
    # SEO content types
    CONTENT_TYPES = [
        "episode",
        "clip",
        "show_page",
        "artist_page",
        "blog_post",
        "social_post"
    ]
    
    def __init__(self, hive_path: Optional[str] = None):
        """Initialize SEOBee."""
        if hive_path is None:
            hive_path = Path(__file__).parent.parent.parent
        self.hive_path = Path(hive_path)
        self.honeycomb_path = self.hive_path / "honeycomb"
        
        # SEO data storage
        self.seo_path = self.honeycomb_path / "seo_data.json"
        self._ensure_seo_file()
    
    def _ensure_seo_file(self) -> None:
        """Ensure SEO data file exists."""
        if not self.seo_path.exists():
            initial_data = {
                "keywords": {},
                "content_analysis": [],
                "recommendations": [],
                "performance_tracking": {},
                "last_audit": None
            }
            with open(self.seo_path, 'w') as f:
                json.dump(initial_data, f, indent=2)
    
    def _load_seo_data(self) -> Dict[str, Any]:
        """Load SEO data."""
        with open(self.seo_path, 'r') as f:
            return json.load(f)
    
    def _save_seo_data(self, data: Dict[str, Any]) -> None:
        """Save SEO data."""
        with open(self.seo_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def run(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute SEO task.
        
        Actions:
        - audit: Run SEO audit on content
        - optimize: Generate optimized metadata
        - keywords: Analyze/suggest keywords
        - tags: Generate tag suggestions
        - track: Track keyword performance
        - report: Generate SEO report
        """
        if task is None:
            task = {}
        
        action = task.get("action", "audit")
        
        actions = {
            "audit": self._run_audit,
            "optimize": self._optimize_content,
            "keywords": self._analyze_keywords,
            "tags": self._suggest_tags,
            "track": self._track_performance,
            "report": self._generate_report,
            "get_stats": self._get_stats
        }
        
        handler = actions.get(action)
        if handler:
            return handler(task)
        
        return {"error": f"Unknown action: {action}"}
    
    def _run_audit(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run SEO audit on content."""
        content_id = task.get("content_id")
        content_type = task.get("content_type", "episode")
        content = task.get("content", {})
        
        issues = []
        score = 100
        
        # Check title
        title = content.get("title", "")
        if not title:
            issues.append({"field": "title", "issue": "Missing title", "severity": "critical"})
            score -= 30
        elif len(title) > 60:
            issues.append({"field": "title", "issue": "Title too long (>60 chars)", "severity": "warning"})
            score -= 10
        elif len(title) < 20:
            issues.append({"field": "title", "issue": "Title too short (<20 chars)", "severity": "warning"})
            score -= 5

        
        # Check description
        description = content.get("description", "")
        if not description:
            issues.append({"field": "description", "issue": "Missing description", "severity": "critical"})
            score -= 25
        elif len(description) < 100:
            issues.append({"field": "description", "issue": "Description too short", "severity": "warning"})
            score -= 10
        elif len(description) > 160:
            issues.append({"field": "description", "issue": "Meta description too long", "severity": "info"})
            score -= 5
        
        # Check keywords
        keywords = content.get("keywords", [])
        if not keywords:
            issues.append({"field": "keywords", "issue": "No keywords specified", "severity": "warning"})
            score -= 15
        
        # Check tags
        tags = content.get("tags", [])
        if len(tags) < 3:
            issues.append({"field": "tags", "issue": "Too few tags (<3)", "severity": "info"})
            score -= 5
        
        audit_result = {
            "content_id": content_id,
            "content_type": content_type,
            "score": max(0, score),
            "grade": self._score_to_grade(score),
            "issues": issues,
            "audited_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Save audit
        seo_data = self._load_seo_data()
        seo_data["content_analysis"].append(audit_result)
        seo_data["last_audit"] = audit_result["audited_at"]
        self._save_seo_data(seo_data)
        
        return {
            "success": True,
            "audit": audit_result,
            "recommendations": self._generate_recommendations(issues)
        }
    
    def _score_to_grade(self, score: int) -> str:
        """Convert score to letter grade."""
        if score >= 90: return "A"
        if score >= 80: return "B"
        if score >= 70: return "C"
        if score >= 60: return "D"
        return "F"
    
    def _generate_recommendations(self, issues: List[Dict]) -> List[str]:
        """Generate recommendations from issues."""
        recs = []
        for issue in issues:
            if issue["field"] == "title":
                recs.append("Optimize title to be 30-60 characters with primary keyword")
            elif issue["field"] == "description":
                recs.append("Add compelling meta description (120-160 chars) with keywords")
            elif issue["field"] == "keywords":
                recs.append("Add 3-5 relevant keywords targeting listener search terms")
            elif issue["field"] == "tags":
                recs.append("Add 5-10 descriptive tags including genre, mood, topics")
        return list(set(recs))
    
    def _optimize_content(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimized metadata for content."""
        content = task.get("content", {})
        content_type = task.get("content_type", "episode")
        
        title = content.get("title", "")
        description = content.get("description", "")
        
        # Generate optimized versions
        optimized = {
            "title": self._optimize_title(title, content_type),
            "description": self._optimize_description(description),
            "meta_title": title[:60] if len(title) > 60 else title,
            "meta_description": description[:160] if len(description) > 160 else description,
            "suggested_keywords": self._extract_keywords(title + " " + description),
            "suggested_tags": self._generate_tags(content),
            "social_title": self._generate_social_title(title),
            "social_description": description[:100] + "..." if len(description) > 100 else description
        }
        
        return {
            "success": True,
            "original": content,
            "optimized": optimized,
            "content_type": content_type
        }
    
    def _optimize_title(self, title: str, content_type: str) -> str:
        """Optimize title for SEO."""
        if not title:
            return f"[{content_type.title()}] - Backlink Broadcast"
        
        # Ensure reasonable length
        if len(title) > 60:
            title = title[:57] + "..."
        
        return title
    
    def _optimize_description(self, description: str) -> str:
        """Optimize description for SEO."""
        if not description:
            return "Listen to the latest from Backlink Broadcast - your source for fresh music and culture."
        
        # Trim to optimal length
        if len(description) > 160:
            description = description[:157] + "..."
        
        return description
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract potential keywords from text."""
        # Simple keyword extraction - would use NLP in production
        words = text.lower().split()
        # Filter common words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "is", "are", "was", "were"}
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        # Return top unique keywords
        return list(dict.fromkeys(keywords))[:10]
    
    def _generate_tags(self, content: Dict[str, Any]) -> List[str]:
        """Generate tag suggestions for content."""
        tags = []
        
        # Genre-based tags
        genre = content.get("genre")
        if genre:
            tags.append(genre.lower())
        
        # Topic-based tags
        topics = content.get("topics", [])
        tags.extend([t.lower() for t in topics])
        
        # Default radio tags
        tags.extend(["podcast", "radio", "music", "live"])
        
        return list(set(tags))[:10]
    
    def _generate_social_title(self, title: str) -> str:
        """Generate social media optimized title."""
        if len(title) > 50:
            return title[:47] + "..."
        return title

    
    def _analyze_keywords(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze keyword performance and suggestions."""
        target_keywords = task.get("keywords", [])
        
        seo_data = self._load_seo_data()
        keyword_data = seo_data.get("keywords", {})
        
        analysis = []
        for keyword in target_keywords:
            kw_lower = keyword.lower()
            existing = keyword_data.get(kw_lower, {})
            
            analysis.append({
                "keyword": keyword,
                "current_rank": existing.get("rank", "untracked"),
                "search_volume": existing.get("volume", "unknown"),
                "competition": existing.get("competition", "unknown"),
                "last_checked": existing.get("last_checked"),
                "trend": existing.get("trend", "stable")
            })
        
        # Suggest related keywords
        suggestions = self._suggest_related_keywords(target_keywords)
        
        return {
            "success": True,
            "analyzed_keywords": analysis,
            "suggestions": suggestions,
            "total_tracked": len(keyword_data)
        }
    
    def _suggest_related_keywords(self, keywords: List[str]) -> List[Dict[str, str]]:
        """Suggest related keywords."""
        # In production, would use keyword research API
        suggestions = []
        for kw in keywords[:3]:
            suggestions.extend([
                {"keyword": f"{kw} podcast", "type": "long_tail"},
                {"keyword": f"best {kw}", "type": "modifier"},
                {"keyword": f"{kw} radio", "type": "related"}
            ])
        return suggestions[:10]
    
    def _suggest_tags(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate tag suggestions for content."""
        content = task.get("content", {})
        content_type = task.get("content_type", "episode")
        
        tags = {
            "primary": [],
            "secondary": [],
            "trending": []
        }
        
        # Primary tags from content
        title = content.get("title", "")
        keywords = self._extract_keywords(title)
        tags["primary"] = keywords[:5]
        
        # Secondary tags based on type
        type_tags = {
            "episode": ["podcast", "episode", "audio", "show"],
            "clip": ["clip", "highlight", "snippet", "viral"],
            "blog_post": ["blog", "article", "read", "news"],
            "social_post": ["social", "update", "live"]
        }
        tags["secondary"] = type_tags.get(content_type, ["content"])
        
        # Would pull trending tags from intel in production
        tags["trending"] = ["trending", "viral", "musthear"]
        
        return {
            "success": True,
            "content_type": content_type,
            "suggested_tags": tags,
            "recommended_count": "8-12 total tags"
        }
    
    def _track_performance(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Track keyword/content performance."""
        keyword = task.get("keyword")
        content_id = task.get("content_id")
        metrics = task.get("metrics", {})
        
        seo_data = self._load_seo_data()
        
        if keyword:
            kw_lower = keyword.lower()
            if kw_lower not in seo_data["keywords"]:
                seo_data["keywords"][kw_lower] = {"history": []}
            
            seo_data["keywords"][kw_lower].update({
                "rank": metrics.get("rank"),
                "volume": metrics.get("volume"),
                "competition": metrics.get("competition"),
                "last_checked": datetime.now(timezone.utc).isoformat()
            })
            seo_data["keywords"][kw_lower]["history"].append({
                "date": datetime.now(timezone.utc).isoformat(),
                "rank": metrics.get("rank")
            })
        
        if content_id:
            if content_id not in seo_data["performance_tracking"]:
                seo_data["performance_tracking"][content_id] = {"history": []}
            
            seo_data["performance_tracking"][content_id]["history"].append({
                "date": datetime.now(timezone.utc).isoformat(),
                "impressions": metrics.get("impressions", 0),
                "clicks": metrics.get("clicks", 0),
                "ctr": metrics.get("ctr", 0)
            })
        
        self._save_seo_data(seo_data)
        
        return {
            "success": True,
            "tracked": {"keyword": keyword, "content_id": content_id},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _generate_report(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SEO performance report."""
        seo_data = self._load_seo_data()
        
        # Audit summary
        audits = seo_data.get("content_analysis", [])
        recent_audits = audits[-10:] if audits else []
        
        avg_score = 0
        if recent_audits:
            avg_score = sum(a.get("score", 0) for a in recent_audits) / len(recent_audits)
        
        grade_distribution = {}
        for audit in recent_audits:
            grade = audit.get("grade", "N/A")
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
        
        # Keyword summary
        keywords = seo_data.get("keywords", {})
        top_keywords = sorted(
            [(k, v.get("rank", 999)) for k, v in keywords.items()],
            key=lambda x: x[1] if isinstance(x[1], int) else 999
        )[:10]
        
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_audits": len(audits),
                "average_score": round(avg_score, 1),
                "grade_distribution": grade_distribution,
                "tracked_keywords": len(keywords)
            },
            "top_keywords": [{"keyword": k, "rank": r} for k, r in top_keywords],
            "recommendations": seo_data.get("recommendations", [])[-5:],
            "last_audit": seo_data.get("last_audit")
        }
        
        return {
            "success": True,
            "report": report
        }
    
    def _get_stats(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get SEO statistics."""
        seo_data = self._load_seo_data()
        
        return {
            "success": True,
            "total_audits": len(seo_data.get("content_analysis", [])),
            "tracked_keywords": len(seo_data.get("keywords", {})),
            "tracked_content": len(seo_data.get("performance_tracking", {})),
            "last_audit": seo_data.get("last_audit"),
            "content_types_supported": self.CONTENT_TYPES
        }
