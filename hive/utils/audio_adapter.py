
import os
import requests
import logging
from typing import Dict, Any, Optional

class AudioStreamAdapter:
    """
    Adapter for interacting with the station's Audio Streaming Provider (Live365).
    Handles metadata updates (Now Playing) and stream status checks.
    """

    def __init__(self):
        self.logger = logging.getLogger("AudioStreamAdapter")
        self.station_id = os.environ.get("LIVE365_STATION_ID")
        self.api_key = os.environ.get("LIVE365_API_KEY") # Often 'handle' in legacy APIs
        self.api_url = os.environ.get("LIVE365_API_URL", "https://tools.live365.com/api/stations")

        if not self.station_id or not self.api_key:
            self.logger.warning("Live365 credentials not found. Audio adapter running in OFFLINE/SIMULATION mode.")
            self.online = False
        else:
            self.online = True

    def update_metadata(self, track: Dict[str, Any]) -> bool:
        """
        Push 'Now Playing' metadata to the stream.
        
        Args:
            track: Dict containing 'title', 'artist', 'album', 'duration'.
        """
        if not self.online:
            self.logger.info(f"[SIMULATION] Updated Metadata: {track.get('artist')} - {track.get('title')}")
            return True

        title = track.get("title", "Unknown")
        artist = track.get("artist", "Unknown")
        album = track.get("album", "")
        
        # Construct Live365-compatible payload/query
        # Note: Actual endpoint varies by integration method (Icecast inject vs Web API)
        # This implementation assumes the standard History/Metadata API
        
        try:
            # Example API call structure
            params = {
                "station_id": self.station_id,
                "method": "update",
                "handle": self.api_key,
                "song": title,
                "artist": artist,
                "album": album,
                "seconds": track.get("duration", 180) 
            }
            
            # Using verify=False if strictly needed for legacy certs, but default to True
            response = requests.get(f"{self.api_url}/{self.station_id}/history", params=params, timeout=5)
            
            if response.status_code == 200:
                self.logger.info(f"Metadata Pushed: {artist} - {title}")
                return True
            else:
                self.logger.error(f"Metadata Push Failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            self.logger.error(f"Metadata Push Error: {e}")
            return False

    def get_stream_status(self) -> Dict[str, Any]:
        """Check if the stream is currently live."""
        if not self.online:
            return {"status": "offline_simulation"}
            
        # Placeholder for status check logic
        return {"status": "unknown"}
