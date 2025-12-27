"""
Backlink Broadcast Hive

A swarm intelligence system for autonomous radio station operation.

The hive consists of:
- Queen: The orchestrator that schedules and coordinates bees
- Bees: Worker agents that perform specific tasks
- Honeycomb: Shared state that bees read from and write to

Usage:
    from hive import QueenOrchestrator

    queen = QueenOrchestrator()
    queen.run()  # Start the hive

Or from CLI:
    python -m hive.queen.orchestrator run
"""

from .queen import QueenOrchestrator

__version__ = "1.0.0"
__all__ = ["QueenOrchestrator"]
