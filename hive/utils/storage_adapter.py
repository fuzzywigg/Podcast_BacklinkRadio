import json
import logging
import os
from pathlib import Path
from typing import Any

try:
    from google.cloud import firestore
except ImportError:
    firestore = None


class StorageAdapter:
    """
    Abstracts storage operations to support both local file system and Firestore.
    """

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.storage_type = os.environ.get("STORAGE_TYPE", "FILE").upper()
        self.project_id = os.environ.get("GCP_PROJECT_ID")
        self.firestore_client = None
        self.logger = logging.getLogger("StorageAdapter")

        if self.storage_type == "FIRESTORE":
            if not firestore:
                self.logger.warning("google-cloud-firestore not installed. Falling back to FILE.")
                self.storage_type = "FILE"
            else:
                try:
                    self.firestore_client = firestore.Client(project=self.project_id)
                    self.logger.info(f"Firestore initialized with project {self.project_id}")
                except Exception as e:
                    self.logger.error(f"Failed to init Firestore: {e}. Falling back to FILE.")
                    self.storage_type = "FILE"

    def read(self, filename: str) -> dict[str, Any]:
        """Read data from storage."""
        if self.storage_type == "FIRESTORE" and self.firestore_client:
            return self._read_firestore(filename)
        return self._read_file(filename)

    def write(self, filename: str, data: dict[str, Any]) -> None:
        """Write data to storage."""
        if self.storage_type == "FIRESTORE" and self.firestore_client:
            self._write_firestore(filename, data)
        else:
            self._write_file(filename, data)

    # ─────────────────────────────────────────────────────────────
    # FILE SYSTEM IMPLEMENTATION
    # ─────────────────────────────────────────────────────────────

    def _read_file(self, filename: str) -> dict[str, Any]:
        file_path = (self.base_path / filename).resolve()

        # Security check
        if not str(file_path).startswith(str(self.base_path.resolve())):
            raise ValueError(f"Path traversal detected: {filename}")

        if not file_path.exists():
            return {}

        try:
            with open(file_path) as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"File read error {filename}: {e}")
            return {}

    def _write_file(self, filename: str, data: dict[str, Any]) -> None:
        file_path = (self.base_path / filename).resolve()

        # Security check
        if not str(file_path).startswith(str(self.base_path.resolve())):
            raise ValueError(f"Path traversal detected: {filename}")

        try:
            temp_path = file_path.with_suffix(".tmp")
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, file_path)
        except Exception as e:
            self.logger.error(f"File write error {filename}: {e}")

    # ─────────────────────────────────────────────────────────────
    # FIRESTORE IMPLEMENTATION
    # ─────────────────────────────────────────────────────────────

    def _get_doc_ref(self, filename: str):
        """Map filename to Firestore Clean collection/doc."""
        # e.g. "state.json" -> collection "hive_data", doc "state"
        doc_id = filename.replace(".json", "").replace(".jsonl", "")
        # We use a single root collection 'hive_data'
        return self.firestore_client.collection("hive_data").document(doc_id)

    def _read_firestore(self, filename: str) -> dict[str, Any]:
        try:
            doc_ref = self._get_doc_ref(filename)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return {}
        except Exception as e:
            self.logger.error(f"Firestore read error {filename}: {e}")
            return {}

    def _write_firestore(self, filename: str, data: dict[str, Any]) -> None:
        try:
            doc_ref = self._get_doc_ref(filename)
            doc_ref.set(data)
        except Exception as e:
            self.logger.error(f"Firestore write error {filename}: {e}")
