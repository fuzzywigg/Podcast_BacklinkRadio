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
    # UX Improvements: Colors and Formatting
    class Colors:
        HEADER = '\033[95m'
        BLUE = '\033[94m'
        CYAN = '\033[96m'
        GREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'

    def print_header(text):
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}\n {text}\n{'='*60}{Colors.ENDC}")

    def print_result(bee_type, task_id, result, duration=None):
        is_success = result.get("success", False)
        status_text = "✅ SUCCESS" if is_success else "❌ FAILED"
        color = Colors.GREEN if is_success else Colors.FAIL

        duration_str = ""
        if duration:
            duration_str = f" in {duration:.2f}s"

        print(f"{color}{status_text} {Colors.ENDC} {Colors.CYAN}{bee_type}{Colors.ENDC} -> Task: {task_id}{duration_str}")

        error = result.get("error")
        if not is_success and error:
            print(f"   {Colors.FAIL}Error: {error}{Colors.ENDC}")

    print(f"{Colors.BLUE}Initializing Queen Orchestrator...{Colors.ENDC}")
    queen = QueenOrchestrator()

    # Load tasks.json
    tasks_path = queen.honeycomb_path / "tasks.json"
    with open(tasks_path, 'r') as f:
        tasks_data = json.load(f)

    pending_tasks = tasks_data.get("pending", [])
    recurring_tasks = tasks_data.get("recurring", [])

    bee_mapping = {
        "social": "social_poster",
        "research": "listener_intel",
        "scout": "trend_scout",
        "monetization": "sponsor_hunter"
    }

    print(f"\n🔎 Found {Colors.BOLD}{len(pending_tasks)}{Colors.ENDC} pending tasks and {Colors.BOLD}{len(recurring_tasks)}{Colors.ENDC} recurring tasks.")

    stats = {"success": 0, "failed": 0, "skipped": 0}

    # 1. Execute Pending Tasks
    if pending_tasks:
        print_header("Executing Pending Tasks")
        for task in pending_tasks:
            bee_type = task.get("bee_type")
            mapped_bee = bee_mapping.get(bee_type, bee_type)
            task_id = task.get('id', 'unknown')

            print(f"\n{Colors.BOLD}▶ Executing:{Colors.ENDC} {task_id} ({mapped_bee})")
            result = queen.spawn_bee(mapped_bee, task)

            if result.get("success"):
                stats["success"] += 1
            else:
                stats["failed"] += 1

            print_result(mapped_bee, task_id, result, result.get("duration_seconds"))
    else:
        print(f"\n{Colors.BLUE}ℹ️  No pending tasks to execute.{Colors.ENDC}")

    # 2. Execute Recurring Tasks
    print_header("Executing Recurring Tasks (Immediate)")
    for task in recurring_tasks:
        task_id = task.get('id')
        if not task.get("enabled", True):
            print(f"{Colors.WARNING}⚠️  Skipping disabled task: {task_id}{Colors.ENDC}")
            stats["skipped"] += 1
            continue

        bee_short_type = task.get("bee_type")
        mapped_bee = bee_mapping.get(bee_short_type)

        if not mapped_bee:
            print(f"{Colors.WARNING}⚠️  Warning: Could not map bee type '{bee_short_type}' for task '{task_id}'. Skipping.{Colors.ENDC}")
            stats["skipped"] += 1
            continue

        print(f"\n{Colors.BOLD}▶ Executing:{Colors.ENDC} {task_id} ({mapped_bee})")
        result = queen.spawn_bee(mapped_bee)

        if result.get("success"):
            stats["success"] += 1
        else:
            stats["failed"] += 1

        print_result(mapped_bee, task_id, result, result.get("duration_seconds"))

    # Summary
    print_header("Execution Summary")
    print(f"{Colors.GREEN}✅ Success: {stats['success']}{Colors.ENDC}")
    print(f"{Colors.FAIL}❌ Failed:  {stats['failed']}{Colors.ENDC}")
    print(f"{Colors.WARNING}⏭️  Skipped: {stats['skipped']}{Colors.ENDC}")
    print(f"\n{Colors.BLUE}All scheduled tasks execution attempt complete.{Colors.ENDC}")

if __name__ == "__main__":
    main()
