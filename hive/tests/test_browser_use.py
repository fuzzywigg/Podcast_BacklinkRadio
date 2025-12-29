import json
import os
from pathlib import Path

from hive.utils.browser_use_client import BrowserUseClient


def test_browser_client():
    # Load key from config
    config_path = Path("hive/config.json")
    with open(config_path) as f:
        config = json.load(f)

    # Try to get from env first, then config
    api_key = os.environ.get("BROWSER_USE_API_KEY")
    if not api_key:
        api_key_env = config["integrations"]["browser_use"].get("api_key_env")
        if api_key_env:
            api_key = os.environ.get(api_key_env)

    if not api_key:
        print("No API key found in env (BROWSER_USE_API_KEY). Skipping test.")
        return

    print(f"Testing with key: {api_key[:5]}...")

    client = BrowserUseClient(api_key)

    print("\n1. Create Task...")
    # Simple task to avoid login issues or side effects
    task_prompt = "Go to example.com and extract the page title. Return ONLY the title."
    task = client.create_task(task_prompt)

    if "error" in task:
        print(f"FAILED to create task: {task['error']}")
        return

    print(f"Task created: {task}")
    task_id = task.get("id")

    if not task_id:
        print("No task ID returned.")
        return

    print(f"\n2. Wait for Task {task_id}...")
    result = client.wait_for_completion(task_id, interval=2, timeout=60)

    print("\n3. Result:")
    print(json.dumps(result, indent=2))

    if result.get("status") == "finished":
        print("\nSUCCESS!")
    else:
        print("\nTask did not finish successfully.")


if __name__ == "__main__":
    test_browser_client()
