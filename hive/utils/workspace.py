"""
Workspace Client Utility.

Handles interactions with Google Workspace (Sheets, Docs) using a Service Account.
"""

from pathlib import Path
from typing import List, Any, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class WorkspaceClient:
    """Client for interacting with Google Sheets and Docs."""

    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive'
    ]

    def __init__(self, hive_path: Optional[str] = None):
        """
        Initialize the Workspace client.

        Args:
            hive_path: Path to the hive root directory.
        """
        if hive_path is None:
            # Assumes this file is in hive/utils/workspace.py
            # hive root is ../../
            hive_path = Path(__file__).parent.parent
        self.hive_path = Path(hive_path)

        # Look for the service account key defined in
        # WORKSPACE_REQUIREMENTS.json
        self.creds_path = self.hive_path / "google_workspace_key.json"
        self.creds = None
        self.sheets_service = None
        self.docs_service = None
        self.drive_service = None
        self.enabled = False

        self._authenticate()

    def _authenticate(self):
        """Load service account credentials."""
        if self.creds_path.exists():
            try:
                self.creds = service_account.Credentials.from_service_account_file(
                    str(self.creds_path), scopes=self.SCOPES)
                self.enabled = True
                # Build services lazily or upfront
                self.sheets_service = build(
                    'sheets', 'v4', credentials=self.creds)
                self.docs_service = build('docs', 'v1', credentials=self.creds)
                self.drive_service = build(
                    'drive', 'v3', credentials=self.creds)
                print(
                    f"[{self.__class__.__name__}] Successfully authenticated with Workspace.")
            except Exception as e:
                print(f"[{self.__class__.__name__}] Auth Error: {e}")
        else:
            print(
                f"[{self.__class__.__name__}] Warning: 'google_workspace_key.json' not found. Workspace features disabled.")

    # ─────────────────────────────────────────────────────────────
    # SHEETS METHODS (The Database)
    # ─────────────────────────────────────────────────────────────

    def append_row(self, spreadsheet_id: str, sheet_range: str,
                   values: List[Any]) -> bool:
        """
        Append a row of data to a Google Sheet.

        Args:
            spreadsheet_id: The long ID string in the URL.
            sheet_range: Range e.g., 'Sheet1!A1' (or just 'Sheet1').
            values: List of values to append (a single row).
        """
        if not self.enabled:
            return False

        try:
            body = {'values': [values]}
            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=sheet_range,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            return True
        except HttpError as err:
            print(f"[{self.__class__.__name__}] Sheet Append Error: {err}")
            return False

    def read_range(self, spreadsheet_id: str,
                   sheet_range: str) -> List[List[Any]]:
        """Read data from a range."""
        if not self.enabled:
            return []

        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=sheet_range
            ).execute()
            return result.get('values', [])
        except HttpError as err:
            print(f"[{self.__class__.__name__}] Sheet Read Error: {err}")
            return []

    # ─────────────────────────────────────────────────────────────
    # DOCS METHODS (The Report)
    # ─────────────────────────────────────────────────────────────

    def write_to_doc(self, document_id: str, text: str,
                     title_style: bool = False) -> bool:
        """
        Append text to the end of a Google Doc.

        Args:
            document_id: The long ID string in the URL.
            text: The text content to add.
            title_style: If True, applies 'HEADING_1' style (simplified).
        """
        if not self.enabled:
            return False

        try:
            # 1. Get current end index
            doc = self.docs_service.documents().get(documentId=document_id).execute()
            content = doc.get('body').get('content')
            end_index = content[-1].get('endIndex') - 1

            requests = [
                {
                    'insertText': {
                        'location': {'index': end_index},
                        'text': text + "\n"
                    }
                }
            ]

            self.docs_service.documents().batchUpdate(
                documentId=document_id, body={'requests': requests}
            ).execute()
            return True
        except HttpError as err:
            print(f"[{self.__class__.__name__}] Doc Write Error: {err}")
            return False

    def clear_doc(self, document_id: str) -> bool:
        """Wipes a document clean (useful for daily 'Show Prep' resets)."""
        if not self.enabled:
            return False

        try:
            doc = self.docs_service.documents().get(documentId=document_id).execute()
            content = doc.get('body').get('content')
            end_index = content[-1].get('endIndex') - 1

            if end_index <= 1:
                return True  # Already empty

            requests = [{
                'deleteContentRange': {
                    'range': {
                        'startIndex': 1,
                        'endIndex': end_index
                    }
                }
            }]
            self.docs_service.documents().batchUpdate(
                documentId=document_id, body={'requests': requests}
            ).execute()
            return True
        except HttpError as err:
            print(f"[{self.__class__.__name__}] Doc Clear Error: {err}")
            return False
