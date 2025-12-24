"""
Unit tests for the BaseBee class and its subclasses.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from hive.bees.base_bee import BaseBee, EmployedBee, OnlookerBee, ScoutBee


class TestBaseBee:
    """Tests for BaseBee abstract class."""

    def test_cannot_instantiate_directly(self) -> None:
        """BaseBee is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseBee()  # type: ignore

    def test_bee_id_generation(self, temp_hive_dir: Path) -> None:
        """Bee IDs should be unique and follow the expected format."""

        class ConcreteBee(BaseBee):
            BEE_TYPE = "test_bee"

            def work(self, task: Any = None) -> Any:
                return {"status": "ok"}

        bee1 = ConcreteBee(hive_path=str(temp_hive_dir))
        bee2 = ConcreteBee(hive_path=str(temp_hive_dir))

        assert bee1.bee_id.startswith("test_bee_")
        assert bee2.bee_id.startswith("test_bee_")
        assert bee1.bee_id != bee2.bee_id
        assert len(bee1.bee_id.split("_")[-1]) == 8  # UUID is 8 chars

    def test_honeycomb_path_default(self, temp_hive_dir: Path) -> None:
        """Honeycomb path should be correctly set."""

        class ConcreteBee(BaseBee):
            BEE_TYPE = "test_bee"

            def work(self, task: Any = None) -> Any:
                return {}

        bee = ConcreteBee(hive_path=str(temp_hive_dir))
        assert bee.honeycomb_path == temp_hive_dir / "honeycomb"


class TestHoneycombAccess:
    """Tests for honeycomb read/write operations."""

    @pytest.fixture
    def concrete_bee(self, temp_hive_dir: Path) -> BaseBee:
        """Create a concrete bee for testing."""

        class ConcreteBee(BaseBee):
            BEE_TYPE = "test_bee"

            def work(self, task: Any = None) -> Any:
                return {}

        return ConcreteBee(hive_path=str(temp_hive_dir))

    def test_read_state(self, concrete_bee: BaseBee) -> None:
        """Should read state from honeycomb."""
        state = concrete_bee.read_state()
        assert "_meta" in state
        assert "alerts" in state

    def test_read_tasks(self, concrete_bee: BaseBee) -> None:
        """Should read tasks from honeycomb."""
        tasks = concrete_bee.read_tasks()
        assert "pending" in tasks
        assert "in_progress" in tasks
        assert "completed" in tasks
        assert "failed" in tasks

    def test_read_intel(self, concrete_bee: BaseBee) -> None:
        """Should read intel from honeycomb."""
        intel = concrete_bee.read_intel()
        assert "_meta" in intel

    def test_write_task(self, concrete_bee: BaseBee) -> None:
        """Should write a task to the queue."""
        task = {"type": "test", "payload": {"data": "value"}}
        task_id = concrete_bee.write_task(task)

        assert task_id is not None

        tasks = concrete_bee.read_tasks()
        pending_ids = [t["id"] for t in tasks["pending"]]
        assert task_id in pending_ids

    def test_claim_and_complete_task(self, concrete_bee: BaseBee) -> None:
        """Should be able to claim and complete a task."""
        # Write a task
        task = {"type": "test"}
        task_id = concrete_bee.write_task(task)

        # Claim it
        claimed = concrete_bee.claim_task(task_id)
        assert claimed is not None
        assert claimed["id"] == task_id
        assert claimed["status"] == "in_progress"

        # Complete it
        concrete_bee.complete_task(task_id, result={"success": True})

        tasks = concrete_bee.read_tasks()
        completed_ids = [t["id"] for t in tasks["completed"]]
        assert task_id in completed_ids

    def test_post_alert(self, concrete_bee: BaseBee) -> None:
        """Should post alerts to state."""
        concrete_bee.post_alert("Test alert", priority=False)
        concrete_bee.post_alert("Urgent alert", priority=True)

        state = concrete_bee.read_state()
        assert len(state["alerts"]["normal"]) >= 1
        assert len(state["alerts"]["priority"]) >= 1


class TestBeeLifecycle:
    """Tests for bee run lifecycle."""

    def test_successful_run(self, temp_hive_dir: Path) -> None:
        """Successful work should return success result."""

        class SuccessBee(BaseBee):
            BEE_TYPE = "success"

            def work(self, task: Any = None) -> dict:
                return {"data": "result"}

        bee = SuccessBee(hive_path=str(temp_hive_dir))
        result = bee.run()

        assert result["success"] is True
        assert result["result"] == {"data": "result"}
        assert "duration_seconds" in result
        assert result["bee_id"] == bee.bee_id

    def test_failed_run(self, temp_hive_dir: Path) -> None:
        """Failed work should return error result."""

        class FailBee(BaseBee):
            BEE_TYPE = "fail"

            def work(self, task: Any = None) -> None:
                raise ValueError("Something went wrong")

        bee = FailBee(hive_path=str(temp_hive_dir))
        result = bee.run()

        assert result["success"] is False
        assert "Something went wrong" in result["error"]
        assert result["bee_id"] == bee.bee_id


class TestBeeTypes:
    """Tests for bee type subclasses."""

    def test_scout_bee_attributes(self) -> None:
        """ScoutBee should have correct type and category."""
        assert ScoutBee.BEE_TYPE == "scout"
        assert ScoutBee.CATEGORY == "research"

    def test_employed_bee_attributes(self) -> None:
        """EmployedBee should have correct type and category."""
        assert EmployedBee.BEE_TYPE == "employed"
        assert EmployedBee.CATEGORY == "content"

    def test_onlooker_bee_attributes(self) -> None:
        """OnlookerBee should have correct type and category."""
        assert OnlookerBee.BEE_TYPE == "onlooker"
        assert OnlookerBee.CATEGORY == "research"
