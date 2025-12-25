"""
Configuration Management for Backlink Broadcast Hive.

Provides centralized, type-safe configuration loading with environment variable
support and validation.
"""

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class HiveConfig(BaseModel):
    """Core hive configuration."""

    name: str = "Backlink Broadcast Hive"
    heartbeat_interval_seconds: int = 60
    max_concurrent_bees: int = 10
    log_level: str = "info"


class BroadcastTimingConfig(BaseModel):
    """Broadcast timing configuration."""

    max_talk_window_seconds: int = 60
    required_next_track_announcement: bool = True
    weather_update_minutes: list[int] = Field(default_factory=lambda: [8, 38])
    traffic_update_minute: int = 0
    status_tweet_hours: list[int] = Field(
        default_factory=lambda: [0, 6, 12, 18])


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: str = "google"
    model: str = "gemini-2.0-flash-exp"
    temperature: float = 0.3
    api_key_env: str = "GOOGLE_API_KEY"
    use_for_bees: list[str] = Field(
        default_factory=lambda: [
            "show_prep",
            "social_poster",
            "engagement",
            "trend_scout"])

    @property
    def api_key(self) -> str | None:
        """Get API key from environment."""
        return os.environ.get(self.api_key_env)


class TwitterConfig(BaseModel):
    """Twitter/X integration configuration."""

    enabled: bool = True
    api_key_env: str = "TWITTER_API_KEY"
    api_secret_env: str = "TWITTER_API_SECRET"
    access_token_env: str = "TWITTER_ACCESS_TOKEN"
    access_token_secret_env: str = "TWITTER_ACCESS_TOKEN_SECRET"
    handle: str = "@BacklinkRadio"

    @property
    def api_key(self) -> str | None:
        return os.environ.get(self.api_key_env)

    @property
    def api_secret(self) -> str | None:
        return os.environ.get(self.api_secret_env)

    @property
    def access_token(self) -> str | None:
        return os.environ.get(self.access_token_env)

    @property
    def access_token_secret(self) -> str | None:
        return os.environ.get(self.access_token_secret_env)


class PlausibleConfig(BaseModel):
    """Plausible Analytics configuration."""

    enabled: bool = True
    domain: str = "andonlabs.com"
    api_host: str = "https://plausible.io"


class BrowserUseConfig(BaseModel):
    """Browser Use cloud automation configuration."""

    enabled: bool = True
    api_key_env: str = "BROWSER_USE_API_KEY"

    @property
    def api_key(self) -> str | None:
        return os.environ.get(self.api_key_env)


class IntegrationsConfig(BaseModel):
    """External integrations configuration."""

    twitter: TwitterConfig = Field(default_factory=TwitterConfig)
    plausible: PlausibleConfig = Field(default_factory=PlausibleConfig)
    browser_use: BrowserUseConfig = Field(default_factory=BrowserUseConfig)


class ScheduleConfig(BaseModel):
    """Bee schedule configuration."""

    interval_minutes: int
    enabled: bool = True
    description: str = ""


class EventTriggerConfig(BaseModel):
    """Event trigger configuration."""

    bees: list[str] = Field(default_factory=list)
    priority: str = "normal"
    description: str = ""


class Config(BaseModel):
    """
    Main configuration container.

    Loads configuration from hive/config.json and environment variables.
    Environment variables take precedence over file values.
    """

    hive: HiveConfig = Field(default_factory=HiveConfig)
    broadcast_timing: BroadcastTimingConfig = Field(
        default_factory=BroadcastTimingConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    integrations: IntegrationsConfig = Field(
        default_factory=IntegrationsConfig)
    schedules: dict[str, ScheduleConfig] = Field(default_factory=dict)
    event_triggers: dict[str, EventTriggerConfig] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        extra = "allow"  # Allow additional fields from JSON


@lru_cache(maxsize=1)
def get_config(config_path: str | None = None) -> Config:
    """
    Load and cache the configuration.

    Args:
        config_path: Optional path to config.json. Defaults to hive/config.json.

    Returns:
        Validated Config object.
    """
    if config_path is None:
        # Default to hive/config.json relative to this file
        config_path = str(Path(__file__).parent.parent / "config.json")

    config_data: dict[str, Any] = {}

    # Load from file if exists
    path = Path(config_path)
    if path.exists():
        with open(path) as f:
            config_data = json.load(f)
            # Remove meta field if present
            config_data.pop("_meta", None)

    # Apply environment overrides
    if log_level := os.environ.get("LOG_LEVEL"):
        if "hive" not in config_data:
            config_data["hive"] = {}
        config_data["hive"]["log_level"] = log_level

    return Config(**config_data)


def reload_config() -> Config:
    """
    Force reload the configuration (clear cache).

    Returns:
        Fresh Config object.
    """
    get_config.cache_clear()
    return get_config()


# ─────────────────────────────────────────────────────────────────────────────────
# Convenience Functions
# ─────────────────────────────────────────────────────────────────────────────────


def get_llm_config() -> LLMConfig:
    """Get LLM configuration."""
    return get_config().llm


def get_twitter_config() -> TwitterConfig:
    """Get Twitter configuration."""
    return get_config().integrations.twitter


def get_schedule(bee_type: str) -> ScheduleConfig | None:
    """Get schedule configuration for a specific bee type."""
    return get_config().schedules.get(bee_type)


def is_bee_enabled(bee_type: str) -> bool:
    """Check if a bee is enabled in the schedule."""
    schedule = get_schedule(bee_type)
    return schedule.enabled if schedule else False
