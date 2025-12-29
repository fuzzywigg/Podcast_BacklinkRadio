"""Queen module - The hive orchestrator."""

print("DEBUG: Loading hive.queen package")
try:
    from .orchestrator import QueenOrchestrator
except Exception as e:
    import traceback

    traceback.print_exc()
    print(f"CRITICAL ERROR IMPORTING QUEEN: {e}")
    raise e

__all__ = ["QueenOrchestrator"]
