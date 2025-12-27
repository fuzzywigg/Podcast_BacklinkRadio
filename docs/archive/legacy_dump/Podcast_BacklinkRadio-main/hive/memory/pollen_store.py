"""
Pollen Store - Memory substrate for successful patterns.

Pollen represents high-value experience traces that future bee generations
can recall. Not all experience is stored - only successful, high-signal
episodes become "pollen sites":
- Specific tool configs that worked
- External data sources that produced strong results
- Conversation patterns that led to resolution
- Known-good workflows

This implements the Model-First Reasoning (MFR) memory layer.
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
import threading


@dataclass
class PollenEntry:
    """A single pollen memory entry."""
    id: str
    bee_type: str
    task_type: str
    model: Dict[str, Any]  # The explicit problem model (MFR Phase 1)
    result_summary: Dict[str, Any]
    success_score: float  # 0.0 to 1.0
    timestamp: str
    lineage_version: str
    tags: List[str]
    recall_count: int = 0
    last_recalled: Optional[str] = None


class PollenStore:
    """
    Pollen memory storage and retrieval system.
    
    Implements the "hivemind memory" where successful patterns are
    stored and can be recalled by future bee generations.
    """
    
    def __init__(self, hive_path: Optional[str] = None):
        """Initialize pollen store."""
        if hive_path is None:
            hive_path = Path(__file__).parent.parent
        self.hive_path = Path(hive_path)
        self.pollen_file = self.hive_path / "honeycomb" / "pollen.json"
        self._lock = threading.Lock()
        self._cache: Dict[str, PollenEntry] = {}
        self._index: Dict[str, List[str]] = {}  # tag -> [pollen_ids]
        
        # Ensure pollen file exists
        self._ensure_pollen_file()
        self._load_cache()
    
    def _ensure_pollen_file(self) -> None:
        """Ensure pollen.json exists with proper structure."""
        if not self.pollen_file.exists():
            initial = {
                "_meta": {
                    "version": "1.0.0",
                    "description": "Pollen memory - successful patterns for bee generations",
                    "created": datetime.now(timezone.utc).isoformat()
                },
                "entries": [],
                "index": {
                    "by_bee_type": {},
                    "by_task_type": {},
                    "by_tag": {}
                },
                "stats": {
                    "total_entries": 0,
                    "total_recalls": 0,
                    "top_patterns": []
                }
            }
            self.pollen_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.pollen_file, 'w') as f:
                json.dump(initial, f, indent=2)
    
    def _load_cache(self) -> None:
        """Load pollen entries into memory cache."""
        with self._lock:
            try:
                with open(self.pollen_file, 'r') as f:
                    data = json.load(f)
                
                self._cache = {}
                for entry_dict in data.get("entries", []):
                    entry = PollenEntry(**entry_dict)
                    self._cache[entry.id] = entry
                
                self._index = data.get("index", {}).get("by_tag", {})
            except Exception:
                self._cache = {}
                self._index = {}
    
    def _generate_id(self, model: Dict, bee_type: str) -> str:
        """Generate unique ID for pollen entry."""
        content = f"{bee_type}:{json.dumps(model, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def store(
        self,
        bee_type: str,
        task_type: str,
        model: Dict[str, Any],
        result_summary: Dict[str, Any],
        success_score: float,
        tags: Optional[List[str]] = None,
        lineage_version: str = "1.0.0"
    ) -> str:
        """
        Store a successful pattern as pollen.
        
        Args:
            bee_type: Type of bee that created this pattern
            task_type: Type of task this pattern solves
            model: The explicit problem model (MFR Phase 1 output)
            result_summary: Summary of successful result
            success_score: How successful (0.0 to 1.0)
            tags: Optional tags for retrieval
            lineage_version: Version of bee lineage
        
        Returns:
            Pollen entry ID
        """
        if success_score < 0.5:
            # Don't store low-quality patterns
            return ""
        
        tags = tags or []
        tags.extend([bee_type, task_type])  # Auto-tag
        tags = list(set(tags))  # Dedupe
        
        pollen_id = self._generate_id(model, bee_type)
        
        entry = PollenEntry(
            id=pollen_id,
            bee_type=bee_type,
            task_type=task_type,
            model=model,
            result_summary=result_summary,
            success_score=success_score,
            timestamp=datetime.now(timezone.utc).isoformat(),
            lineage_version=lineage_version,
            tags=tags
        )
        
        with self._lock:
            # Check if this pattern already exists
            if pollen_id in self._cache:
                # Update existing entry with higher score if applicable
                existing = self._cache[pollen_id]
                if success_score > existing.success_score:
                    entry.recall_count = existing.recall_count
                    self._cache[pollen_id] = entry
            else:
                self._cache[pollen_id] = entry
            
            # Update index
            for tag in tags:
                if tag not in self._index:
                    self._index[tag] = []
                if pollen_id not in self._index[tag]:
                    self._index[tag].append(pollen_id)
            
            self._persist()
        
        return pollen_id
    
    def recall(
        self,
        task_type: Optional[str] = None,
        bee_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_score: float = 0.7,
        limit: int = 5
    ) -> List[PollenEntry]:
        """
        Recall pollen patterns matching criteria.
        
        This is how new bee generations "remember where previous
        generations found pollen."
        
        Args:
            task_type: Filter by task type
            bee_type: Filter by bee type
            tags: Filter by tags (any match)
            min_score: Minimum success score
            limit: Maximum entries to return
        
        Returns:
            List of matching pollen entries, sorted by score
        """
        matches = []
        
        with self._lock:
            for entry in self._cache.values():
                # Apply filters
                if task_type and entry.task_type != task_type:
                    continue
                if bee_type and entry.bee_type != bee_type:
                    continue
                if entry.success_score < min_score:
                    continue
                if tags:
                    if not any(tag in entry.tags for tag in tags):
                        continue
                
                matches.append(entry)
            
            # Sort by score (highest first)
            matches.sort(key=lambda e: e.success_score, reverse=True)
            
            # Update recall counts
            now = datetime.now(timezone.utc).isoformat()
            for entry in matches[:limit]:
                entry.recall_count += 1
                entry.last_recalled = now
            
            self._persist()
        
        return matches[:limit]
    
    def get_pollen_sources(self, task: Dict[str, Any]) -> List[Dict]:
        """
        Get relevant pollen sources for a given task.
        
        This is called during MFR Phase 1 to help bees
        identify known-good patterns.
        """
        # Extract potential tags from task
        tags = []
        if "type" in task:
            tags.append(task["type"])
        if "action" in task.get("payload", {}):
            tags.append(task["payload"]["action"])
        
        entries = self.recall(tags=tags, limit=3)
        
        return [
            {
                "id": e.id,
                "model": e.model,
                "success_score": e.success_score,
                "bee_type": e.bee_type
            }
            for e in entries
        ]
    def _persist(self) -> None:
        """Persist pollen cache to disk."""
        # Build index structures
        by_bee_type: Dict[str, List[str]] = {}
        by_task_type: Dict[str, List[str]] = {}
        
        for pollen_id, entry in self._cache.items():
            if entry.bee_type not in by_bee_type:
                by_bee_type[entry.bee_type] = []
            by_bee_type[entry.bee_type].append(pollen_id)
            
            if entry.task_type not in by_task_type:
                by_task_type[entry.task_type] = []
            by_task_type[entry.task_type].append(pollen_id)
        
        # Calculate top patterns
        top_patterns = sorted(
            self._cache.values(),
            key=lambda e: (e.success_score, e.recall_count),
            reverse=True
        )[:10]
        
        data = {
            "_meta": {
                "version": "1.0.0",
                "description": "Pollen memory - successful patterns for bee generations",
                "last_updated": datetime.now(timezone.utc).isoformat()
            },
            "entries": [asdict(e) for e in self._cache.values()],
            "index": {
                "by_bee_type": by_bee_type,
                "by_task_type": by_task_type,
                "by_tag": self._index
            },
            "stats": {
                "total_entries": len(self._cache),
                "total_recalls": sum(e.recall_count for e in self._cache.values()),
                "top_patterns": [
                    {"id": e.id, "bee_type": e.bee_type, "score": e.success_score}
                    for e in top_patterns
                ]
            }
        }
        
        with open(self.pollen_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pollen store statistics."""
        with self._lock:
            return {
                "total_entries": len(self._cache),
                "total_recalls": sum(e.recall_count for e in self._cache.values()),
                "by_bee_type": {
                    bee_type: len(ids)
                    for bee_type, ids in self._index.items()
                    if bee_type.endswith("Bee")
                },
                "avg_success_score": (
                    sum(e.success_score for e in self._cache.values()) / len(self._cache)
                    if self._cache else 0.0
                )
            }
    
    def prune(self, max_age_days: int = 90, min_score: float = 0.6) -> int:
        """
        Prune old or low-quality pollen entries.
        
        Returns number of entries removed.
        """
        from datetime import timedelta
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        removed = 0
        
        with self._lock:
            to_remove = []
            for pollen_id, entry in self._cache.items():
                entry_time = datetime.fromisoformat(entry.timestamp.replace('Z', '+00:00'))
                
                # Remove if old AND low score AND not recently recalled
                if entry_time < cutoff and entry.success_score < min_score:
                    if entry.recall_count < 3:
                        to_remove.append(pollen_id)
            
            for pollen_id in to_remove:
                del self._cache[pollen_id]
                # Clean up index
                for tag_ids in self._index.values():
                    if pollen_id in tag_ids:
                        tag_ids.remove(pollen_id)
                removed += 1
            
            if removed > 0:
                self._persist()
        
        return removed
