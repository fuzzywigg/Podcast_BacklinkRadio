"""
MusicDiscoveryBee - Finds new tracks, deep cuts, and emerging artists.

A Scout bee that explores music sources to discover fresh content
for the radio station playlist.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class MusicDiscoveryBee:
    """
    MusicDiscoveryBee - Music exploration and curation.
    
    Responsibilities:
    - Discover new releases from various sources
    - Find emerging artists before they blow up
    - Curate deep cuts and b-sides
    - Track genre trends
    - Build playlist recommendations
    
    Outputs:
    - Track recommendations
    - Artist profiles
    - Genre trend reports
    - Playlist suggestions
    """
    
    BEE_TYPE = "scout"
    PRIORITY = "normal"
    
    # Music sources (would integrate with actual APIs)
    SOURCES = [
        "spotify_new_releases",
        "bandcamp_trending",
        "soundcloud_discover",
        "youtube_music",
        "radio_submissions",
        "label_promos"
    ]
    
    # Genre categories
    GENRES = [
        "electronic", "hip_hop", "rock", "pop", "indie",
        "r_and_b", "jazz", "classical", "world", "experimental"
    ]
    
    def __init__(self, hive_path: Optional[str] = None):
        """Initialize MusicDiscoveryBee."""
        if hive_path is None:
            hive_path = Path(__file__).parent.parent.parent
        self.hive_path = Path(hive_path)
        self.honeycomb_path = self.hive_path / "honeycomb"
        
        # Music catalog storage
        self.music_path = self.honeycomb_path / "music_catalog.json"
        self._ensure_music_file()
    
    def _ensure_music_file(self) -> None:
        """Ensure music catalog file exists."""
        if not self.music_path.exists():
            initial_data = {
                "discovered_tracks": [],
                "artist_profiles": {},
                "genre_trends": {},
                "playlists": {},
                "last_scan": None
            }
            with open(self.music_path, 'w') as f:
                json.dump(initial_data, f, indent=2)
    
    def _load_catalog(self) -> Dict[str, Any]:
        """Load music catalog."""
        with open(self.music_path, 'r') as f:
            return json.load(f)
    
    def _save_catalog(self, data: Dict[str, Any]) -> None:
        """Save music catalog."""
        with open(self.music_path, 'w') as f:
            json.dump(data, f, indent=2)

    
    def run(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute music discovery task.
        
        Actions:
        - scan: Scan sources for new music
        - add_track: Add a discovered track
        - add_artist: Add/update artist profile
        - get_recommendations: Get playlist recommendations
        - genre_trends: Analyze genre trends
        - search: Search catalog
        - get_stats: Get discovery statistics
        """
        if task is None:
            task = {}
        
        action = task.get("action", "scan")
        
        actions = {
            "scan": self._scan_sources,
            "add_track": self._add_track,
            "add_artist": self._add_artist,
            "get_recommendations": self._get_recommendations,
            "genre_trends": self._analyze_genre_trends,
            "search": self._search_catalog,
            "get_stats": self._get_stats
        }
        
        handler = actions.get(action)
        if handler:
            return handler(task)
        
        return {"error": f"Unknown action: {action}"}
    
    def _scan_sources(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Scan music sources for new discoveries."""
        sources = task.get("sources", self.SOURCES[:3])
        genre_filter = task.get("genre")
        limit = task.get("limit", 10)
        
        # Simulated discovery - in production would call actual APIs
        discoveries = []
        for source in sources:
            # Each source would return tracks
            mock_tracks = self._simulate_source_scan(source, genre_filter, limit // len(sources))
            discoveries.extend(mock_tracks)
        
        # Save discoveries
        catalog = self._load_catalog()
        for track in discoveries:
            track["discovered_at"] = datetime.now(timezone.utc).isoformat()
            track["status"] = "pending_review"
            catalog["discovered_tracks"].append(track)
        
        catalog["last_scan"] = datetime.now(timezone.utc).isoformat()
        self._save_catalog(catalog)
        
        return {
            "success": True,
            "sources_scanned": sources,
            "discoveries": len(discoveries),
            "tracks": discoveries,
            "scan_time": catalog["last_scan"]
        }
    
    def _simulate_source_scan(self, source: str, genre: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """Simulate scanning a music source."""
        # In production, this would call actual APIs
        # Returns placeholder structure showing expected format
        tracks = []
        for i in range(min(limit, 3)):
            tracks.append({
                "id": f"{source}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{i}",
                "source": source,
                "title": f"[Track from {source}]",
                "artist": "[Artist Name]",
                "album": "[Album Name]",
                "genre": genre or "unknown",
                "release_date": None,
                "duration_seconds": 0,
                "preview_url": None,
                "metadata": {
                    "bpm": None,
                    "key": None,
                    "energy": None
                }
            })
        return tracks
    
    def _add_track(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Manually add a discovered track."""
        required = ["title", "artist"]
        for field in required:
            if field not in task:
                return {"error": f"Missing required field: {field}"}
        
        track = {
            "id": f"manual_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "source": "manual_entry",
            "title": task["title"],
            "artist": task["artist"],
            "album": task.get("album"),
            "genre": task.get("genre", "unknown"),
            "release_date": task.get("release_date"),
            "duration_seconds": task.get("duration_seconds", 0),
            "preview_url": task.get("preview_url"),
            "discovered_at": datetime.now(timezone.utc).isoformat(),
            "status": task.get("status", "approved"),
            "notes": task.get("notes"),
            "metadata": task.get("metadata", {})
        }
        
        catalog = self._load_catalog()
        catalog["discovered_tracks"].append(track)
        self._save_catalog(catalog)
        
        return {
            "success": True,
            "track_id": track["id"],
            "track": track
        }

    
    def _add_artist(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Add or update an artist profile."""
        artist_name = task.get("artist_name")
        if not artist_name:
            return {"error": "artist_name required"}
        
        profile = {
            "name": artist_name,
            "genres": task.get("genres", []),
            "location": task.get("location"),
            "bio": task.get("bio"),
            "social_links": task.get("social_links", {}),
            "label": task.get("label"),
            "monthly_listeners": task.get("monthly_listeners"),
            "emerging": task.get("emerging", True),
            "first_discovered": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "notes": task.get("notes")
        }
        
        catalog = self._load_catalog()
        
        # Check if artist exists
        artist_key = artist_name.lower().replace(" ", "_")
        existing = catalog["artist_profiles"].get(artist_key)
        
        if existing:
            # Update existing
            profile["first_discovered"] = existing.get("first_discovered", profile["first_discovered"])
            profile["play_count"] = existing.get("play_count", 0)
        
        catalog["artist_profiles"][artist_key] = profile
        self._save_catalog(catalog)
        
        return {
            "success": True,
            "artist_key": artist_key,
            "profile": profile,
            "is_new": existing is None
        }
    
    def _get_recommendations(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get playlist recommendations based on criteria."""
        genre = task.get("genre")
        mood = task.get("mood")  # energetic, chill, upbeat, mellow
        limit = task.get("limit", 10)
        include_emerging = task.get("include_emerging", True)
        
        catalog = self._load_catalog()
        tracks = catalog.get("discovered_tracks", [])
        
        # Filter by criteria
        filtered = []
        for track in tracks:
            if track.get("status") != "approved":
                continue
            if genre and track.get("genre") != genre:
                continue
            filtered.append(track)
        
        # Sort by discovery date (newest first)
        filtered.sort(key=lambda x: x.get("discovered_at", ""), reverse=True)
        
        # Build playlist
        playlist = {
            "id": f"rec_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "criteria": {
                "genre": genre,
                "mood": mood,
                "include_emerging": include_emerging
            },
            "tracks": filtered[:limit],
            "total_duration_seconds": sum(t.get("duration_seconds", 0) for t in filtered[:limit])
        }
        
        return {
            "success": True,
            "playlist": playlist,
            "track_count": len(playlist["tracks"])
        }
    
    def _analyze_genre_trends(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze genre trends from discovered music."""
        catalog = self._load_catalog()
        tracks = catalog.get("discovered_tracks", [])
        
        # Count by genre
        genre_counts = {}
        genre_recent = {}  # Last 30 days
        
        now = datetime.now(timezone.utc)
        
        for track in tracks:
            genre = track.get("genre", "unknown")
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
            
            # Check if recent
            discovered = track.get("discovered_at")
            if discovered:
                try:
                    disc_date = datetime.fromisoformat(discovered.replace('Z', '+00:00'))
                    days_ago = (now - disc_date).days
                    if days_ago <= 30:
                        genre_recent[genre] = genre_recent.get(genre, 0) + 1
                except:
                    pass
        
        # Calculate trends
        trends = []
        for genre in self.GENRES:
            total = genre_counts.get(genre, 0)
            recent = genre_recent.get(genre, 0)
            if total > 0:
                trends.append({
                    "genre": genre,
                    "total_tracks": total,
                    "recent_discoveries": recent,
                    "momentum": "rising" if recent > total * 0.3 else "stable"
                })
        
        trends.sort(key=lambda x: x["recent_discoveries"], reverse=True)
        
        # Save trends
        catalog["genre_trends"] = {
            "analyzed_at": now.isoformat(),
            "trends": trends
        }
        self._save_catalog(catalog)
        
        return {
            "success": True,
            "total_tracks_analyzed": len(tracks),
            "trends": trends,
            "hot_genres": [t["genre"] for t in trends[:3] if t["momentum"] == "rising"]
        }
    
    def _search_catalog(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Search the music catalog."""
        query = task.get("query", "").lower()
        search_type = task.get("type", "all")  # all, tracks, artists
        limit = task.get("limit", 20)
        
        catalog = self._load_catalog()
        results = {"tracks": [], "artists": []}
        
        if search_type in ["all", "tracks"]:
            for track in catalog.get("discovered_tracks", []):
                if query in track.get("title", "").lower() or \
                   query in track.get("artist", "").lower() or \
                   query in track.get("genre", "").lower():
                    results["tracks"].append(track)
        
        if search_type in ["all", "artists"]:
            for key, profile in catalog.get("artist_profiles", {}).items():
                if query in profile.get("name", "").lower() or \
                   query in str(profile.get("genres", [])).lower():
                    results["artists"].append(profile)
        
        return {
            "success": True,
            "query": query,
            "tracks_found": len(results["tracks"][:limit]),
            "artists_found": len(results["artists"][:limit]),
            "tracks": results["tracks"][:limit],
            "artists": results["artists"][:limit]
        }
    
    def _get_stats(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get music discovery statistics."""
        catalog = self._load_catalog()
        tracks = catalog.get("discovered_tracks", [])
        artists = catalog.get("artist_profiles", {})
        
        # Status breakdown
        by_status = {}
        for track in tracks:
            status = track.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1
        
        # Source breakdown
        by_source = {}
        for track in tracks:
            source = track.get("source", "unknown")
            by_source[source] = by_source.get(source, 0) + 1
        
        # Emerging artists
        emerging_count = sum(1 for a in artists.values() if a.get("emerging", False))
        
        return {
            "success": True,
            "total_tracks": len(tracks),
            "total_artists": len(artists),
            "emerging_artists": emerging_count,
            "by_status": by_status,
            "by_source": by_source,
            "last_scan": catalog.get("last_scan"),
            "genres_tracked": self.GENRES
        }
