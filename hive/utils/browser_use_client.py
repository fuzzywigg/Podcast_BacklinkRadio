"""
Browser Use Client - Wrapper for the Browser Use Cloud API.

API Reference: https://docs.cloud.browser-use.com/api-reference/v-2-api-current
"""

import time
import requests
import json
from typing import Dict, Any, Optional

class BrowserUseClient:
    """Client for interacting with Browser Use Cloud API."""

    API_BASE = "https://api.browser-use.com/api/v2"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "X-Browser-Use-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

    def create_task(self, task: str, llm: str = "gemini-2.5-flash") -> Dict[str, Any]:
        """
        Create a new browser task.

        Args:
            task: The instruction for the agent.
            llm: Model to use (default: gemini-2.5-flash as per repo preference).
        """
        url = f"{self.API_BASE}/tasks"
        payload = {
            "task": task,
            "llm": llm
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get details of a task."""
        url = f"{self.API_BASE}/tasks/{task_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def wait_for_completion(self, task_id: str, interval: int = 5, timeout: int = 600) -> Dict[str, Any]:
        """Poll task until completion."""
        start_time = time.time()

        while (time.time() - start_time) < timeout:
            result = self.get_task(task_id)
            if "error" in result:
                return result

            status = result.get("status")
            if status in ["finished", "stopped", "failed"]:
                return result

            time.sleep(interval)

        return {"error": "Timeout waiting for task completion"}

if __name__ == "__main__":
    # Test execution
    import sys

    # Simple test if run directly
    if len(sys.argv) > 1:
        key = sys.argv[1]
        client = BrowserUseClient(key)
        print("Creating task...")
        task = client.create_task("Go to example.com and tell me the title.")
        print(f"Task created: {task}")

        if "id" in task:
            task_id = task["id"]
            print(f"Waiting for task {task_id}...")
            final = client.wait_for_completion(task_id)
            print("Final result:", final)
