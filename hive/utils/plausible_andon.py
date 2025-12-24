# plausible_andon.py
# Easy Plausible Analytics Integration for Andon Labs
# Drop-in module for AI DJ, Live365, and other services

import requests
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class EventType(Enum):
    """Standard event types for Andon Labs"""
    AI_DECISION_MADE = "AI Decision Made"
    SONG_REQUESTED = "Song Requested"
    SONG_QUEUED = "Song Queued"
    SONG_PURCHASED = "Song Purchased"
    SONG_RENTED = "Song Rented"
    REVENUE_GENERATED = "Revenue Generated"
    LISTENER_TIP = "Listener Tip"
    TREASURY_UPDATED = "Treasury Updated"
    BROADCAST_STARTED = "Broadcast Started"
    BROADCAST_ENDED = "Broadcast Ended"
    DECISION_DECLINED = "Decision Declined"
    METADATA_UPDATED = "Metadata Updated"


@dataclass
class PlausibleConfig:
    """Configuration for Plausible tracking"""
    domain: str
    api_host: str = "https://plausible.io"
    enabled: bool = True


class PlausibleAnalytics:
    """
    Andon Labs Plausible Analytics Integration

    Tracks AI DJ decisions, listener interactions, revenue, and broadcast metrics.
    """

    def __init__(self,
                 domain: str = None,
                 api_host: str = "https://plausible.io",
                 enabled: bool = True):
        """
        Initialize Plausible tracker

        Args:
            domain: Plausible domain (default from env: PLAUSIBLE_DOMAIN)
            api_host: Plausible API host (default: https://plausible.io)
            enabled: Enable/disable tracking globally
        """
        self.domain = domain or os.getenv('PLAUSIBLE_DOMAIN', 'andon-labs.local')
        self.api_host = api_host
        self.enabled = enabled
        self.endpoint = f"{api_host}/api/event"

        # Default user agent
        self.user_agent = "Andon-Labs-Tracker/1.0"

    def _build_payload(self,
                      event_name: str,
                      page_url: str,
                      props: Dict[str, Any] = None,
                      referrer: str = None) -> Dict[str, Any]:
        """Build event payload for Plausible API"""
        payload = {
            "name": event_name,
            "domain": self.domain,
            "url": page_url,
            "props": props or {}
        }

        if referrer:
            payload["referrer"] = referrer

        return payload

    def _send(self, payload: Dict[str, Any]) -> bool:
        """Send event to Plausible API"""
        if not self.enabled:
            return True

        headers = {
            "User-Agent": self.user_agent,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=5
            )
            return response.status_code in [200, 202]
        except Exception as e:
            print(f"[Plausible] Error tracking event: {e}")
            return False

    # AI DJ Events

    def track_ai_decision(self,
                         decision_type: str,
                         song: str,
                         cost: float = 0.0,
                         treasury_before: float = 0.0,
                         treasury_after: float = 0.0,
                         source: str = None,
                         has_tip: bool = False) -> bool:
        """
        Track an AI DJ decision (purchase, rent, decline)

        Args:
            decision_type: 'purchase', 'rent', or 'decline'
            song: Song title/name
            cost: Cost of the decision
            treasury_before: Treasury balance before decision
            treasury_after: Treasury balance after decision
            source: Request source ('twitter', 'web', 'phone', etc.)
            has_tip: Whether request included a tip

        Returns:
            True if tracking successful
        """
        props = {
            "decision_type": decision_type,
            "song": song,
            "cost": str(cost),
            "treasury_before": str(treasury_before),
            "treasury_after": str(treasury_after),
            "has_tip": str(has_tip)
        }

        if source:
            props["source"] = source

        payload = self._build_payload(
            event_name=EventType.AI_DECISION_MADE.value,
            page_url="app://andon-dj/ai-decision",
            props=props
        )

        return self._send(payload)

    def track_song_request(self,
                          song: str,
                          source: str,
                          tip_amount: float = 0.0) -> bool:
        """
        Track a song request from listener

        Args:
            song: Requested song title
            source: Source of request ('twitter', 'web', 'api', etc.)
            tip_amount: Tip amount if included

        Returns:
            True if tracking successful
        """
        props = {
            "song": song,
            "source": source,
            "tip_amount": str(tip_amount),
            "has_tip": str(tip_amount > 0)
        }

        payload = self._build_payload(
            event_name=EventType.SONG_REQUESTED.value,
            page_url="app://andon-dj/song-request",
            props=props
        )

        return self._send(payload)

    def track_song_acquired(self,
                           song: str,
                           acquisition_type: str,
                           cost: float,
                           treasury_remaining: float) -> bool:
        """
        Track when AI DJ acquires a song (purchase or rent)

        Args:
            song: Song title
            acquisition_type: 'purchase' or 'rent'
            cost: Cost of acquisition
            treasury_remaining: Treasury balance after transaction

        Returns:
            True if tracking successful
        """
        event_name = (EventType.SONG_PURCHASED.value
                     if acquisition_type == 'purchase'
                     else EventType.SONG_RENTED.value)

        props = {
            "song": song,
            "cost": str(cost),
            "treasury_remaining": str(treasury_remaining)
        }

        payload = self._build_payload(
            event_name=event_name,
            page_url="app://andon-dj/music-acquisition",
            props=props
        )

        return self._send(payload)

    # Broadcast Events

    def track_song_queued(self,
                         song_title: str,
                         artist: str = None,
                         duration: int = 0,
                         acquisition_type: str = None) -> bool:
        """
        Track when a song is queued to broadcast

        Args:
            song_title: Song title
            artist: Artist name
            duration: Song duration in seconds
            acquisition_type: 'free', 'purchase', or 'rent'

        Returns:
            True if tracking successful
        """
        props = {
            "song_title": song_title,
            "duration": str(duration)
        }

        if artist:
            props["artist"] = artist
        if acquisition_type:
            props["acquisition_type"] = acquisition_type

        payload = self._build_payload(
            event_name=EventType.SONG_QUEUED.value,
            page_url="app://live365/queue",
            props=props
        )

        return self._send(payload)

    def track_broadcast_status(self,
                              status: str) -> bool:
        """
        Track broadcast start/end

        Args:
            status: 'started' or 'ended'

        Returns:
            True if tracking successful
        """
        event_name = (EventType.BROADCAST_STARTED.value
                     if status == 'started'
                     else EventType.BROADCAST_ENDED.value)

        payload = self._build_payload(
            event_name=event_name,
            page_url="app://live365/broadcast",
            props={"timestamp": datetime.now().isoformat()}
        )

        return self._send(payload)

    # Revenue Events

    def track_tip_received(self,
                          amount: float,
                          source: str,
                          song_requested: str = None) -> bool:
        """
        Track listener tip

        Args:
            amount: Tip amount
            source: Source of tip ('twitter', 'web', 'cash_app', etc.)
            song_requested: Song that generated the tip (optional)

        Returns:
            True if tracking successful
        """
        props = {
            "amount": str(amount),
            "source": source,
            "currency": "USD"
        }

        if song_requested:
            props["song_requested"] = song_requested

        payload = self._build_payload(
            event_name=EventType.LISTENER_TIP.value,
            page_url="app://andon-dj/revenue",
            props=props
        )

        return self._send(payload)

    def track_revenue(self,
                     amount: float,
                     revenue_type: str,
                     source: str = None,
                     session_total: float = None) -> bool:
        """
        Track revenue (tips, donations, etc.)

        Args:
            amount: Revenue amount
            revenue_type: Type of revenue ('listener_tip', 'donation', etc.)
            source: Source of revenue
            session_total: Total revenue in session

        Returns:
            True if tracking successful
        """
        props = {
            "amount": str(amount),
            "revenue_type": revenue_type,
            "currency": "USD"
        }

        if source:
            props["source"] = source
        if session_total:
            props["session_total"] = str(session_total)

        payload = self._build_payload(
            event_name=EventType.REVENUE_GENERATED.value,
            page_url="app://andon-dj/revenue",
            props=props
        )

        return self._send(payload)

    # Treasury Events

    def track_treasury_updated(self,
                              balance_before: float,
                              balance_after: float,
                              change_amount: float,
                              change_reason: str) -> bool:
        """
        Track treasury balance changes

        Args:
            balance_before: Balance before change
            balance_after: Balance after change
            change_amount: Amount of change
            change_reason: Reason for change ('purchase', 'rent', 'tip', etc.)

        Returns:
            True if tracking successful
        """
        props = {
            "balance_before": str(balance_before),
            "balance_after": str(balance_after),
            "change_amount": str(change_amount),
            "change_reason": change_reason
        }

        payload = self._build_payload(
            event_name=EventType.TREASURY_UPDATED.value,
            page_url="app://andon-dj/treasury",
            props=props
        )

        return self._send(payload)

    # Generic Events

    def track_event(self,
                   event_name: str,
                   page_url: str = None,
                   props: Dict[str, Any] = None) -> bool:
        """
        Track a custom event

        Args:
            event_name: Name of the event
            page_url: URL where event occurred (default: app://andon-labs)
            props: Custom properties

        Returns:
            True if tracking successful
        """
        page_url = page_url or "app://andon-labs/event"

        payload = self._build_payload(
            event_name=event_name,
            page_url=page_url,
            props=props
        )

        return self._send(payload)


# Singleton instance for easy importing
analytics = PlausibleAnalytics()
