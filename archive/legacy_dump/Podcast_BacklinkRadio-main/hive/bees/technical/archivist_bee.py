"""
Archivist Bee - Manages content backup and archival.

BACKGROUND PRIORITY BEE - Preservation and organization.

Responsibilities:
- Backup broadcast content
- Maintain searchable archive
- Organize historical data
- Generate archive indexes
- Ensure content preservation
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
import json
import hashlib
import shutil

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from base_bee import EmployedBee


class ArchivistBee(EmployedBee):
    """
    Manages content archival and backup operations.
    
    This bee ensures all station content is properly
    preserved and organized for future reference.
    """

    BEE_TYPE = "archivist"
    BEE_NAME = "Archivist Bee"
    CATEGORY = "technical"

    # Archive categories
    ARCHIVE_CATEGORIES = {
        "broadcasts": {"retention_days": 365, "compress": True},
        "clips": {"retention_days": 180, "compress": True},
        "logs": {"retention_days": 90, "compress": True},
        "analytics": {"retention_days": 730, "compress": False},
        "intel": {"retention_days": 365, "compress": False}
    }

    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process archival tasks.

        Task payload actions:
        - daily_backup: Run daily backup routine
        - archive_content: Archive specific content
        - search_archive: Search archived content
        - generate_index: Generate archive index
        - cleanup: Clean up old archives
        - verify_integrity: Verify archive integrity
        """
        self.log("Archivist Bee activated...")

        if not task:
            return self._daily_backup()

        action = task.get("payload", {}).get("action", "daily_backup")

        if action == "daily_backup":
            return self._daily_backup()
        elif action == "archive_content":
            return self._archive_content(task)
        elif action == "search_archive":
            return self._search_archive(task)
        elif action == "generate_index":
            return self._generate_index()
        elif action == "cleanup":
            return self._cleanup_old_archives()
        elif action == "verify_integrity":
            return self._verify_integrity()
        elif action == "restore":
            return self._restore_from_archive(task)

        return {"error": f"Unknown action: {action}"}

    def _daily_backup(self) -> Dict[str, Any]:
        """Run daily backup routine."""
        self.log("Running daily backup...")

        backup_results = {
            "date": datetime.now(timezone.utc).date().isoformat(),
            "backed_up": [],
            "errors": []
        }

        # Backup honeycomb state files
        honeycomb_files = ["state.json", "tasks.json", "intel.json"]
        for filename in honeycomb_files:
            result = self._backup_file(
                self.honeycomb_path / filename,
                "honeycomb"
            )
            if result.get("success"):
                backup_results["backed_up"].append(filename)
            else:
                backup_results["errors"].append({
                    "file": filename,
                    "error": result.get("error")
                })

        # Backup treasury events
        treasury_log = self.hive_path / "treasury_events.jsonl"
        if treasury_log.exists():
            result = self._backup_file(treasury_log, "treasury")
            if result.get("success"):
                backup_results["backed_up"].append("treasury_events.jsonl")

        # Backup analytics history
        analytics_log = self.hive_path / "analytics_history.jsonl"
        if analytics_log.exists():
            result = self._backup_file(analytics_log, "analytics")
            if result.get("success"):
                backup_results["backed_up"].append("analytics_history.jsonl")

        # Update backup manifest
        self._update_manifest(backup_results)

        return {
            "action": "daily_backup",
            "results": backup_results
        }

    def _backup_file(self, source_path: Path, category: str) -> Dict[str, Any]:
        """Backup a single file to archive."""
        if not source_path.exists():
            return {"success": False, "error": "Source file not found"}

        try:
            # Create archive directory structure
            archive_base = self.hive_path / "archive"
            date_str = datetime.now(timezone.utc).strftime("%Y/%m/%d")
            archive_dir = archive_base / category / date_str
            archive_dir.mkdir(parents=True, exist_ok=True)

            # Generate backup filename with timestamp
            timestamp = datetime.now(timezone.utc).strftime("%H%M%S")
            backup_name = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            backup_path = archive_dir / backup_name

            # Copy file
            shutil.copy2(source_path, backup_path)

            # Calculate checksum
            checksum = self._calculate_checksum(backup_path)

            return {
                "success": True,
                "source": str(source_path),
                "backup": str(backup_path),
                "checksum": checksum,
                "size": backup_path.stat().st_size
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _calculate_checksum(self, filepath: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _archive_content(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Archive specific content."""
        payload = task.get("payload", {})
        content_type = payload.get("type", "general")
        content = payload.get("content")
        metadata = payload.get("metadata", {})

        if not content:
            return {"error": "No content provided"}

        # Create archive entry
        archive_base = self.hive_path / "archive" / content_type
        date_str = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        archive_dir = archive_base / date_str
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique ID
        content_id = hashlib.sha256(
            f"{content}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        # Create archive entry
        entry = {
            "id": content_id,
            "type": content_type,
            "archived_at": datetime.now(timezone.utc).isoformat(),
            "content": content,
            "metadata": metadata,
            "bee_id": self.bee_id
        }

        # Save to archive
        archive_path = archive_dir / f"{content_id}.json"
        with open(archive_path, "w") as f:
            json.dump(entry, f, indent=2)

        return {
            "action": "archive_content",
            "id": content_id,
            "path": str(archive_path),
            "success": True
        }

    def _search_archive(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Search archived content."""
        payload = task.get("payload", {})
        query = payload.get("query", "")
        content_type = payload.get("type")
        date_range = payload.get("date_range", {})
        limit = payload.get("limit", 20)

        results = []
        archive_base = self.hive_path / "archive"

        if not archive_base.exists():
            return {
                "action": "search_archive",
                "query": query,
                "results": [],
                "count": 0
            }

        # Determine which directories to search
        search_dirs = []
        if content_type:
            type_dir = archive_base / content_type
            if type_dir.exists():
                search_dirs.append(type_dir)
        else:
            search_dirs = [d for d in archive_base.iterdir() if d.is_dir()]

        # Search through archives
        for type_dir in search_dirs:
            for date_dir in type_dir.rglob("*"):
                if not date_dir.is_dir():
                    continue

                for archive_file in date_dir.glob("*.json"):
                    try:
                        with open(archive_file, "r") as f:
                            entry = json.load(f)

                        # Check if matches query
                        if query:
                            content_str = json.dumps(entry).lower()
                            if query.lower() not in content_str:
                                continue

                        results.append({
                            "id": entry.get("id"),
                            "type": entry.get("type"),
                            "archived_at": entry.get("archived_at"),
                            "path": str(archive_file),
                            "preview": str(entry.get("content", ""))[:100]
                        })

                        if len(results) >= limit:
                            break

                    except (json.JSONDecodeError, IOError):
                        continue

                if len(results) >= limit:
                    break

        return {
            "action": "search_archive",
            "query": query,
            "results": results,
            "count": len(results)
        }

    def _generate_index(self) -> Dict[str, Any]:
        """Generate comprehensive archive index."""
        self.log("Generating archive index...")

        archive_base = self.hive_path / "archive"
        index = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "categories": {},
            "total_items": 0,
            "total_size_bytes": 0
        }

        if not archive_base.exists():
            return {
                "action": "generate_index",
                "index": index
            }

        for category_dir in archive_base.iterdir():
            if not category_dir.is_dir():
                continue

            category_name = category_dir.name
            category_stats = {
                "item_count": 0,
                "size_bytes": 0,
                "oldest": None,
                "newest": None,
                "dates": []
            }

            for date_dir in category_dir.rglob("*"):
                if date_dir.is_file():
                    category_stats["item_count"] += 1
                    category_stats["size_bytes"] += date_dir.stat().st_size

            index["categories"][category_name] = category_stats
            index["total_items"] += category_stats["item_count"]
            index["total_size_bytes"] += category_stats["size_bytes"]

        # Save index
        index_path = archive_base / "INDEX.json"
        with open(index_path, "w") as f:
            json.dump(index, f, indent=2)

        return {
            "action": "generate_index",
            "index": index,
            "index_path": str(index_path)
        }

    def _cleanup_old_archives(self) -> Dict[str, Any]:
        """Clean up archives past retention period."""
        self.log("Cleaning up old archives...")

        archive_base = self.hive_path / "archive"
        cleanup_stats = {
            "deleted_files": 0,
            "freed_bytes": 0,
            "errors": []
        }

        if not archive_base.exists():
            return {
                "action": "cleanup",
                "stats": cleanup_stats
            }

        for category, config in self.ARCHIVE_CATEGORIES.items():
            retention_days = config["retention_days"]
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
            category_dir = archive_base / category

            if not category_dir.exists():
                continue

            # Find and delete old files
            for item in category_dir.rglob("*"):
                if not item.is_file():
                    continue

                try:
                    # Check file age
                    mtime = datetime.fromtimestamp(item.stat().st_mtime, tz=timezone.utc)
                    if mtime < cutoff_date:
                        size = item.stat().st_size
                        item.unlink()
                        cleanup_stats["deleted_files"] += 1
                        cleanup_stats["freed_bytes"] += size

                except Exception as e:
                    cleanup_stats["errors"].append({
                        "file": str(item),
                        "error": str(e)
                    })

        return {
            "action": "cleanup",
            "stats": cleanup_stats
        }

    def _verify_integrity(self) -> Dict[str, Any]:
        """Verify integrity of archived files."""
        self.log("Verifying archive integrity...")

        archive_base = self.hive_path / "archive"
        manifest_path = archive_base / "MANIFEST.json"

        verification = {
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "files_checked": 0,
            "files_valid": 0,
            "files_corrupted": [],
            "files_missing": []
        }

        if not manifest_path.exists():
            return {
                "action": "verify_integrity",
                "verification": verification,
                "note": "No manifest found - run daily_backup first"
            }

        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        for entry in manifest.get("backups", []):
            backup_path = Path(entry.get("path", ""))
            expected_checksum = entry.get("checksum")

            verification["files_checked"] += 1

            if not backup_path.exists():
                verification["files_missing"].append(str(backup_path))
                continue

            actual_checksum = self._calculate_checksum(backup_path)
            if actual_checksum == expected_checksum:
                verification["files_valid"] += 1
            else:
                verification["files_corrupted"].append({
                    "path": str(backup_path),
                    "expected": expected_checksum,
                    "actual": actual_checksum
                })

        return {
            "action": "verify_integrity",
            "verification": verification
        }

    def _restore_from_archive(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Restore content from archive."""
        payload = task.get("payload", {})
        archive_id = payload.get("id")
        archive_path = payload.get("path")
        restore_to = payload.get("restore_to")

        if not archive_path and not archive_id:
            return {"error": "archive_id or archive_path required"}

        # Find archive file
        if archive_id:
            search_result = self._search_archive({
                "payload": {"query": archive_id, "limit": 1}
            })
            if search_result.get("results"):
                archive_path = search_result["results"][0].get("path")

        if not archive_path or not Path(archive_path).exists():
            return {"error": "Archive file not found"}

        try:
            with open(archive_path, "r") as f:
                archived_content = json.load(f)

            return {
                "action": "restore",
                "id": archived_content.get("id"),
                "content": archived_content.get("content"),
                "metadata": archived_content.get("metadata"),
                "archived_at": archived_content.get("archived_at")
            }

        except Exception as e:
            return {"error": f"Failed to restore: {str(e)}"}

    def _update_manifest(self, backup_results: Dict[str, Any]) -> None:
        """Update the backup manifest."""
        archive_base = self.hive_path / "archive"
        archive_base.mkdir(parents=True, exist_ok=True)
        manifest_path = archive_base / "MANIFEST.json"

        # Load existing manifest
        if manifest_path.exists():
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
        else:
            manifest = {"created_at": datetime.now(timezone.utc).isoformat(), "backups": []}

        # Add new backup entry
        manifest["last_backup"] = datetime.now(timezone.utc).isoformat()
        manifest["backups"].append({
            "date": backup_results.get("date"),
            "files": backup_results.get("backed_up", []),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Keep only last 90 days of manifest entries
        cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
        manifest["backups"] = [
            b for b in manifest["backups"]
            if b.get("timestamp", "") >= cutoff
        ]

        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)


if __name__ == "__main__":
    bee = ArchivistBee()
    result = bee.run()
    print(result)
