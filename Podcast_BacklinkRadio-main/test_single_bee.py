#!/usr/bin/env python3
"""Test single bee spawn for debugging."""
import sys
sys.path.insert(0, 'hive/queen')
sys.path.insert(0, 'hive/bees')

from orchestrator import QueenOrchestrator

queen = QueenOrchestrator()
print("=" * 60)
print("Testing analytics bee spawn:")
print("=" * 60)
result = queen.spawn_bee('analytics')
print("=" * 60)
print("FINAL RESULT:", result)
