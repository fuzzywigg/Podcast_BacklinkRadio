"""
Unit tests for configuration management.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from hive.utils.config import (
    HiveConfig,
    LLMConfig,
    get_config,
    get_schedule,
    is_bee_enabled,
    reload_config,
)


class TestHiveConfig:
    """Tests for HiveConfig model."""

    def test_default_values(self) -> None:
        """Should have sensible defaults."""
        config = HiveConfig()
        assert config.name == "Backlink Broadcast Hive"
        assert config.heartbeat_interval_seconds == 60
        assert config.max_concurrent_bees == 10
        assert config.log_level == "info"

    def test_custom_values(self) -> None:
        """Should accept custom values."""
        config = HiveConfig(
            name="Test Hive",
            heartbeat_interval_seconds=30,
            max_concurrent_bees=5,
            log_level="debug",
        )
        assert config.name == "Test Hive"
        assert config.heartbeat_interval_seconds == 30


class TestLLMConfig:
    """Tests for LLMConfig model."""

    def test_default_values(self) -> None:
        """Should have correct defaults."""
        config = LLMConfig()
        assert config.provider == "google"
        assert config.model == "gemini-2.0-flash-exp"
        assert config.temperature == 0.3

    def test_api_key_from_env(self) -> None:
        """Should read API key from environment."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key_123"}):
            config = LLMConfig()
            assert config.api_key == "test_key_123"

    def test_api_key_missing(self) -> None:
        """Should return None if API key not set."""
        with patch.dict(os.environ, {}, clear=True):
            config = LLMConfig()
            # Don't clear all env vars, just check behavior
            if "GOOGLE_API_KEY" not in os.environ:
                assert config.api_key is None


class TestConfigLoading:
    """Tests for config loading and caching."""

    @pytest.fixture
    def temp_config_file(self) -> Path:
        """Create a temporary config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {
                "hive": {
                    "name": "Test Hive",
                    "heartbeat_interval_seconds": 30,
                    "max_concurrent_bees": 5,
                    "log_level": "debug",
                },
                "llm": {
                    "provider": "google",
                    "model": "gemini-test",
                    "temperature": 0.5,
                },
                "schedules": {
                    "trend_scout": {
                        "interval_minutes": 60,
                        "enabled": True,
                        "description": "Scout for trends",
                    },
                    "disabled_bee": {
                        "interval_minutes": 30,
                        "enabled": False,
                    },
                },
            }
            json.dump(config_data, f)
            return Path(f.name)

    def test_load_from_file(self, temp_config_file: Path) -> None:
        """Should load config from file."""
        # Clear cache first
        reload_config()

        config = get_config(str(temp_config_file))
        assert config.hive.name == "Test Hive"
        assert config.hive.heartbeat_interval_seconds == 30
        assert config.llm.model == "gemini-test"

    def test_config_caching(self, temp_config_file: Path) -> None:
        """Config should be cached after first load."""
        reload_config()

        config1 = get_config(str(temp_config_file))
        config2 = get_config(str(temp_config_file))
        assert config1 is config2

    def test_reload_config(self, temp_config_file: Path) -> None:
        """reload_config should clear cache."""
        config1 = get_config(str(temp_config_file))
        reload_config()
        config2 = get_config(str(temp_config_file))
        # Objects should be different after reload
        assert config1 is not config2


class TestScheduleHelpers:
    """Tests for schedule helper functions."""

    @pytest.fixture
    def config_with_schedules(self) -> Path:
        """Create config with schedules."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {
                "schedules": {
                    "trend_scout": {
                        "interval_minutes": 60,
                        "enabled": True,
                    },
                    "disabled_bee": {
                        "interval_minutes": 30,
                        "enabled": False,
                    },
                },
            }
            json.dump(config_data, f)
            return Path(f.name)

    def test_get_schedule_exists(self, config_with_schedules: Path) -> None:
        """Should return schedule for existing bee."""
        reload_config()
        get_config(str(config_with_schedules))

        schedule = get_schedule("trend_scout")
        assert schedule is not None
        assert schedule.interval_minutes == 60
        assert schedule.enabled is True

    def test_get_schedule_missing(self, config_with_schedules: Path) -> None:
        """Should return None for missing bee."""
        reload_config()
        get_config(str(config_with_schedules))

        schedule = get_schedule("nonexistent_bee")
        assert schedule is None

    def test_is_bee_enabled_true(self, config_with_schedules: Path) -> None:
        """Should return True for enabled bee."""
        reload_config()
        get_config(str(config_with_schedules))

        assert is_bee_enabled("trend_scout") is True

    def test_is_bee_enabled_false(self, config_with_schedules: Path) -> None:
        """Should return False for disabled bee."""
        reload_config()
        get_config(str(config_with_schedules))

        assert is_bee_enabled("disabled_bee") is False

    def test_is_bee_enabled_missing(self, config_with_schedules: Path) -> None:
        """Should return False for missing bee."""
        reload_config()
        get_config(str(config_with_schedules))

        assert is_bee_enabled("nonexistent") is False
