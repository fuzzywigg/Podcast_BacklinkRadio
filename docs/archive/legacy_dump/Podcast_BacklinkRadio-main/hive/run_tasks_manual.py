import json
import sys
import os
from pathlib import Path

# Add the hive directory to sys.path so we can import modules
current_dir = Path(__file__).parent
hive_dir = current_dir.parent
sys.path.append(str(hive_dir))

from hive.queen.orchestrator import QueenOrchestrator

def main():
    print("Initializing Queen Orchestrator...")
    queen = QueenOrchestrator()

    # Load tasks.json
    tasks_path = queen.honeycomb_path / "tasks.json"
    with open(tasks_path, 'r') as f:
        tasks_data = json.load(f)

    pending_tasks = tasks_data.get("pending", [])
    recurring_tasks = tasks_data.get("recurring", [])

    # Mapping for recurring tasks
    # social -> social_poster
    # research -> listener_intel
    # scout -> trend_scout
    # monetization -> sponsor_hunter
    bee_mapping = {
        "social": "social_poster",
        "research": "listener_intel",
        "scout": "trend_scout",
        "monetization": "sponsor_hunter"
    }

    print(f"\nFound {len(pending_tasks)} pending tasks and {len(recurring_tasks)} recurring tasks.")

    # 1. Execute Pending Tasks
    if pending_tasks:
        print("\n--- Executing Pending Tasks ---")
        for task in pending_tasks:
            bee_type = task.get("bee_type")
            # If bee_type matches our mapping keys, map it, otherwise assume it's a direct bee name
            mapped_bee = bee_mapping.get(bee_type, bee_type)

            print(f"Executing pending task: {task.get('id', 'unknown')} (Bee: {mapped_bee})")
            result = queen.spawn_bee(mapped_bee, task)
            print(f"Result: {result}")
    else:
        print("\nNo pending tasks to execute.")

    # 2. Execute Recurring Tasks
    print("\n--- Executing Recurring Tasks (Immediate) ---")
    for task in recurring_tasks:
        if not task.get("enabled", True):
            print(f"Skipping disabled task: {task.get('id')}")
            continue

        bee_short_type = task.get("bee_type")
        mapped_bee = bee_mapping.get(bee_short_type)

        if not mapped_bee:
            print(f"Warning: Could not map bee type '{bee_short_type}' for task '{task.get('id')}'. Skipping.")
            continue

        print(f"Executing recurring task: {task.get('id')} (Bee: {mapped_bee})")
        result = queen.spawn_bee(mapped_bee)
        print(f"Result: {result}")

    print("\nAll scheduled tasks execution attempt complete.")

if __name__ == "__main__":
    main()
