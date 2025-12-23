"""
Stream Monitor Bee - Monitors broadcast health and quality.

Responsibilities:
- Monitor stream uptime and quality
- Detect dead air and technical issues
- Track listener counts
- Alert on problems
"""

from typing import Any, Dict, Optional
from datetime import datetime, timezone
import sys
import json
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_bee import OnlookerBee


class StreamMonitorBee(OnlookerBee):
    """
    Monitors broadcast stream health.

    Watches for technical issues and maintains
    stream quality metrics.
    """

    BEE_TYPE = "stream_monitor"
    BEE_NAME = "Stream Monitor Bee"
    CATEGORY = "technical"

    # Alert thresholds
    THRESHOLDS = {
        "dead_air_seconds": 10,
        "bitrate_min_kbps": 128,
        "listener_drop_percent": 20,
        "latency_max_ms": 5000
    }

    # Stream configuration
    STREAM_URL = "https://streaming.live365.com/a13541"

    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Monitor stream health.

        Task payload can include:
        - action: health_check|quality_check|listener_count
        """
        self.log("Running stream health check...")

        health_status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stream_online": False,
            "audio_ok": False,
            "latency_ok": False,
            "bitrate_ok": False,
            "listener_count": 0,
            "issues": []
        }

        # Check stream status
        stream_check = self._check_stream()
        health_status.update(stream_check)

        # Check audio levels
        audio_check = self._check_audio()
        health_status["audio_ok"] = audio_check.get("ok", False)
        if not audio_check.get("ok"):
            health_status["issues"].append(audio_check.get("issue"))

        # Check latency
        latency_check = self._check_latency()
        health_status["latency_ok"] = latency_check.get("ok", False)
        health_status["latency_ms"] = latency_check.get("latency_ms")

        # Get listener count
        listener_count = self._get_listener_count()
        health_status["listener_count"] = listener_count

        # Check bitrate
        bitrate_check = self._check_bitrate()
        health_status["bitrate_ok"] = bitrate_check.get("ok", False)
        health_status["bitrate_kbps"] = bitrate_check.get("bitrate_kbps", 0)

        if not bitrate_check.get("ok"):
            if bitrate_check.get("bitrate_kbps", 0) > 0:
                health_status["issues"].append(f"Low bitrate: {bitrate_check['bitrate_kbps']}kbps")

        # Update broadcast state
        self.write_state({
            "broadcast": {
                "status": "online" if health_status["stream_online"] else "offline",
                "listener_count": listener_count
            },
            "health": health_status
        })

        # Alert on critical issues
        if health_status["issues"]:
            for issue in health_status["issues"]:
                if issue:
                    self.post_alert(f"Stream issue: {issue}", priority=True)

        self.log(f"Health check complete. Online: {health_status['stream_online']}, "
                f"Listeners: {listener_count}, Issues: {len(health_status['issues'])}")

        return health_status

    def _check_stream(self) -> Dict[str, Any]:
        """Check if stream is online and accessible."""

        # Default fallback
        stream_url = "https://stream.backlink.radio/live"

        # Try to load from config
        try:
            config_path = self.hive_path / "config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    endpoint = config.get("integrations", {}).get("streaming", {}).get("endpoint")
                    if endpoint:
                        stream_url = endpoint
        except Exception as e:
            self.log(f"Error reading config for stream URL: {e}", level="warning")

        result = {
            "stream_online": False,
            "stream_url": stream_url,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "status_code": None,
            "error": None,
            "response_time_ms": 0
        }

        try:
            start_time = datetime.now()
            # 20s timeout as requested, stream=True to avoid downloading content
            response = requests.get(stream_url, stream=True, timeout=20)
            response.close()  # Close connection immediately
            duration = (datetime.now() - start_time).total_seconds() * 1000

            result["status_code"] = response.status_code
            result["response_time_ms"] = round(duration, 2)

            if response.status_code == 200:
                result["stream_online"] = True
            else:
                result["error"] = f"Status code {response.status_code}"

        except requests.exceptions.RequestException as e:
            result["error"] = str(e)

        return result

    def _check_audio(self) -> Dict[str, Any]:
        """Check audio levels for dead air."""

        # In production, would analyze audio levels
        # Placeholder

        return {
            "ok": True,
            "peak_db": -6.0,
            "avg_db": -18.0,
            "issue": None
        }

    def _check_latency(self) -> Dict[str, Any]:
        """Check stream latency."""
        start_time = time.perf_counter()

        try:
            # Measure time to first byte (connection + header receipt)
            with urllib.request.urlopen(self.STREAM_URL, timeout=10) as _:
                pass

            latency_ms = (time.perf_counter() - start_time) * 1000
            ok = True
        except (urllib.error.URLError, Exception) as e:
            self.log(f"Latency check failed: {str(e)}", level="warning")
            latency_ms = -1
            ok = False

        return {
            "ok": ok and (latency_ms > 0) and (latency_ms < self.THRESHOLDS["latency_max_ms"]),
            "latency_ms": round(latency_ms, 2) if latency_ms > 0 else 0
        }

    def _get_listener_count(self) -> int:
        """Get current listener count."""

        # In production, would query streaming server
        # Placeholder

        return 0

    def _get_stream_url(self) -> str:
        """Get stream URL from config or fallback."""
        fallback_url = "https://stream.backlink.radio/live"
        config_path = self.hive_path / "config.json"

        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    endpoint = config.get("integrations", {}).get("streaming", {}).get("endpoint")
                    if endpoint:
                        return endpoint
            except Exception as e:
                self.log(f"Error reading config: {e}", level="error")

        return fallback_url

    def _check_bitrate(self) -> Dict[str, Any]:
        """Check stream bitrate."""
        url = self._get_stream_url()
        bitrate_kbps = 0

        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                bitrate_header = response.getheader('icy-br')
                if bitrate_header:
                    bitrate_kbps = int(bitrate_header)
        except Exception as e:
            self.log(f"Bitrate check failed: {e}", level="warning")
            return {
                "ok": False,
                "bitrate_kbps": 0,
                "error": str(e)
            }

        return {
            "ok": bitrate_kbps >= self.THRESHOLDS["bitrate_min_kbps"],
            "bitrate_kbps": bitrate_kbps
        }


if __name__ == "__main__":
    bee = StreamMonitorBee()
    result = bee.run()
    print(result)
