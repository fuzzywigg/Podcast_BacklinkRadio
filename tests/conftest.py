"""
Pytest configuration and fixtures for Backlink Broadcast tests.

This module provides shared fixtures and configuration for all tests.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest


# ─────────────────────────────────────────────────────────────────────────────────
# Environment Fixtures
# ─────────────────────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def mock_env_vars() -> Generator[None, None, None]:
    """
    Set up mock environment variables for testing.

    This fixture runs automatically for all tests.
    """
    test_env = {
        "GOOGLE_API_KEY": "test_google_api_key",
        "LOG_LEVEL": "DEBUG",
        "ENVIRONMENT": "test",
    }
    with patch.dict(os.environ, test_env):
        yield


@pytest.fixture
def temp_hive_dir() -> Generator[Path, None, None]:
    """
    Create a temporary hive directory with proper structure.

    Returns the path to the temporary hive directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        hive_path = Path(tmpdir) / "hive"
        honeycomb_path = hive_path / "honeycomb"
        honeycomb_path.mkdir(parents=True)

        # Create minimal honeycomb files
        state = {
            "_meta": {
                "version": "1.0.0",
                "last_updated": "2024-01-01T00:00:00Z"},
            "current_track": None,
            "persona": "evening",
            "alerts": {
                "priority": [],
                "normal": []},
            "shoutouts": [],
        }
        tasks = {
            "pending": [],
            "in_progress": [],
            "completed": [],
            "failed": [],
        }
        intel = {
            "_meta": {
                "version": "1.0.0",
                "last_updated": "2024-01-01T00:00:00Z"},
            "listeners": {
                "known_nodes": {}},
            "trends": {},
            "sponsors": {},
        }

        (honeycomb_path / "state.json").write_text(json.dumps(state, indent=2))
        (honeycomb_path / "tasks.json").write_text(json.dumps(tasks, indent=2))
        (honeycomb_path / "intel.json").write_text(json.dumps(intel, indent=2))

        # Create minimal config
        config = {
            "_meta": {"version": "1.0.0"},
            "hive": {
                "heartbeat_interval_seconds": 60,
                "max_concurrent_bees": 5,
                "log_level": "debug",
            },
            "schedules": {},
            "event_triggers": {},
        }
        (hive_path / "config.json").write_text(json.dumps(config, indent=2))

        yield hive_path


# ─────────────────────────────────────────────────────────────────────────────────
# Mock Fixtures
# ─────────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_llm_client() -> MagicMock:
    """Create a mock LLM client for testing."""
    mock = MagicMock()
    mock.generate.return_value = "This is a test response from the LLM."
    mock.generate_async.return_value = "This is an async test response."
    return mock


@pytest.fixture
def mock_requests() -> Generator[MagicMock, None, None]:
    """Mock the requests library for HTTP tests."""
    with patch("requests.get") as mock_get, patch("requests.post") as mock_post:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {}
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {}
        yield MagicMock(get=mock_get, post=mock_post)


@pytest.fixture
def mock_twitter_client() -> MagicMock:
    """Create a mock Twitter/X client for testing."""
    mock = MagicMock()
    mock.create_tweet.return_value = MagicMock(
        data={"id": "1234567890", "text": "Test tweet"}
    )
    return mock


# ─────────────────────────────────────────────────────────────────────────────────
# Sample Data Fixtures
# ─────────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_listener_data() -> dict[str, Any]:
    """Sample listener intel data for testing."""
    return {
        "node_id": "listener_12345",
        "location": {
            "city": "Indianapolis",
            "state": "IN",
            "country": "USA",
            "timezone": "America/Indiana/Indianapolis",
        },
        "first_seen": "2024-01-01T00:00:00Z",
        "last_seen": "2024-01-15T12:30:00Z",
        "interaction_count": 5,
        "dao_credits": 10.0,
        "notes": ["VIP listener", "Active in community"],
    }


@pytest.fixture
def sample_trend_data() -> dict[str, Any]:
    """Sample trend data for testing."""
    return {
        "id": "trend_12345",
        "topic": "#MusicMonday",
        "volume": 50000,
        "sentiment": "positive",
        "relevance_score": 0.85,
        "discovered_at": "2024-01-15T10:00:00Z",
        "source": "twitter",
    }


@pytest.fixture
def sample_track_data() -> dict[str, Any]:
    """Sample track/music data for testing."""
    return {
        "id": "track_12345",
        "title": "Test Song",
        "artist": "Test Artist",
        "album": "Test Album",
        "duration_seconds": 240,
        "genre": "indie",
        "year": 2024,
        "ownership": "licensed",
    }


# ─────────────────────────────────────────────────────────────────────────────────
# Bee Fixtures
# ─────────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def base_bee_config(temp_hive_dir: Path) -> dict[str, Any]:
    """Base configuration for creating test bees."""
    return {
        "hive_path": str(temp_hive_dir),
    }


# ─────────────────────────────────────────────────────────────────────────────────
# Markers
# ─────────────────────────────────────────────────────────────────────────────────


def pytest_configure(config: pytest.Config) -> None:
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line(
        "markers", "integration: marks tests requiring external services"
    )
    config.addinivalue_line("markers", "unit: marks unit tests")
