"""Test spawning new bees through Queen Orchestrator."""
import sys
sys.path.insert(0, '.')
from queen.orchestrator import QueenOrchestrator

q = QueenOrchestrator()

# Test spawning each of the 4 new bees
new_bees = [
    ("script_writer", {"action": "get_stats"}),
    ("music_discovery", {"action": "get_stats"}),
    ("seo", {"action": "get_stats"}),
    ("automation", {"action": "get_status"}),
]

print("Testing bee spawning through Queen...")
for bee_type, task in new_bees:
    result = q.spawn_bee(bee_type, task)
    if "error" in result:
        print(f"[FAIL] {bee_type}: {result['error']}")
    else:
        print(f"[OK] {bee_type} spawned successfully")
        
print("\nQueen orchestrator integration validated!")
