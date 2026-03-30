"""
Basic tests for PawPal+ logic layer.
Run: python -m pytest
"""

import pytest
from pawpal_system import (
    CareTask, FeedingTask, WalkTask, ScheduledTask, Pet,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def make_care_task(task_id: str = "t1", priority: str = "medium") -> CareTask:
    return CareTask(
        task_id=task_id,
        title="Test Task",
        duration_minutes=15,
        priority=priority,
        preferred_time="09:00",
    )


def make_pet() -> Pet:
    return Pet(name="Buddy", species="Dog", age=2, weight_kg=10.0)


# ---------------------------------------------------------------------------
# Test 1 — Task completion changes status
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    """mark_complete() should set the ScheduledTask status to 'complete'."""
    task = make_care_task()
    scheduled = ScheduledTask(task=task, time_slot="09:00")

    assert scheduled.status == "pending"
    scheduled.mark_complete()
    assert scheduled.status == "complete"


def test_mark_skipped_sets_status_and_reason():
    """mark_skipped() should set status to 'skipped' and store the reason."""
    task = make_care_task()
    scheduled = ScheduledTask(task=task, time_slot="09:00")

    scheduled.mark_skipped("owner unavailable")
    assert scheduled.status == "skipped"
    assert scheduled.skip_reason == "owner unavailable"


# ---------------------------------------------------------------------------
# Test 2 — Adding a task to a Pet increases task count
# ---------------------------------------------------------------------------

def test_add_task_increases_count():
    """add_task() should append the task and increase the pet's task list length."""
    pet = make_pet()
    assert len(pet.tasks) == 0

    pet.add_task(make_care_task("t1"))
    assert len(pet.tasks) == 1

    pet.add_task(make_care_task("t2"))
    assert len(pet.tasks) == 2


def test_remove_task_decreases_count():
    """remove_task() should remove the correct task by ID."""
    pet = make_pet()
    pet.add_task(make_care_task("t1"))
    pet.add_task(make_care_task("t2"))

    pet.remove_task("t1")
    assert len(pet.tasks) == 1
    assert pet.tasks[0].task_id == "t2"
