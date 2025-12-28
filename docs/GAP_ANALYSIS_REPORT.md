# Ecosystem Gap Analysis Report

**Date**: 2025-12-28
**Scope**: Comparison of `Backlink Hive` v1 codebase against "Andon FM" Deep Research technical specifications.

## Executive Summary

The current `Backlink Hive` is a robust **Agentic Core** (Brain) but lacks the **Peripherals** (Sensors/Actuators) required to interact with the Andon FM ecosystem. It can "think" about payments and music, but cannot yet "receive" money or "control" the audio stream.

## Critical Gaps (Must-Haves for E2E Functionality)

### 1. Payment Processing (Stripe)

- **Requirement**: Real-time webhook handling with HMAC-SHA256 signature verification.
- **Current State**: `hive/utils/payment_gate.py` contains *refund* and *internal accounting* logic only.
- **Missing**:
  - `POST /webhook` endpoint in `main_service.py`.
  - `stripe` library dependency.
  - `STRIPE_WEBHOOK_SECRET` and `STRIPE_API_KEY` handling.
- **Impact**: The Hive cannot autonomusly process listener payments or "buy" music from the ecosystem.

### 2. Audio Streaming (Live365)

- **Requirement**: Icecast-compatible CBR audio stream control (`https://streaming.live365.com/a{stationID}`).
- **Current State**: `DjBee` (Simulated). It updates a JSON `now_playing` field but does not communicate with an encoder.
- **Missing**:
  - `Icecast` client or generic `shoutcast` integration.
  - Logic to push audio bytes or trigger server-side stream switches.
- **Impact**: The DJ is "miming" the broadcast.

### 3. File Storage (Supabase)

- **Requirement**: S3-compatible storage for large assets (music files, profile pics).
- **Current State**: `StorageAdapter` supports `FILE` (Local) and `FIRESTORE` (Metadata/Small Docs).
- **Missing**:
  - `SUPABASE` backend in `StorageAdapter`.
  - `SUPABASE_URL` and `SUPABASE_KEY` env vars.
- **Impact**: Agents cannot reliably store or retrieve large media files.

## Integration Plan (High Level)

These gaps should be addressed in **Phase 2**, immediately following the stabilization of the Cloud Run container.

1. **Stripe Webhook**: Add `main_service.py` endpoint -> decrypt payload -> inject into `EngagementBee` queue.
2. **Supabase Adapter**: Extend `StorageAdapter` to use `supabase-py` or `boto3`.
3. **Live365 Connector**: Create a new `StreamBee` or extend `DjBee` to handle encoder handshakes.
