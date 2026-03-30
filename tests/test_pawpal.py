"""
Basic tests for PawPal+ logic layer.
Run: python -m pytest
"""

import pytest
from datetime import date, timedelta
from pawpal_system import (
    CareTask, FeedingTask, WalkTask, ScheduledTask, Pet, Scheduler,
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


# ---------------------------------------------------------------------------
# Test 3 — Sorting correctness: tasks come back in chronological order
# ---------------------------------------------------------------------------

def make_timed_task(task_id: str, preferred_time: str, priority: str = "medium") -> CareTask:
    return CareTask(
        task_id=task_id,
        title=f"Task {task_id}",
        duration_minutes=15,
        priority=priority,
        preferred_time=preferred_time,
    )


def test_sort_by_time_chronological_order():
    """sort_by_time() must return tasks ordered from earliest to latest time."""
    scheduler = Scheduler()
    tasks = [
        make_timed_task("t3", "14:00"),
        make_timed_task("t1", "08:00"),
        make_timed_task("t2", "11:30"),
    ]
    sorted_tasks = scheduler.sort_by_time(tasks)
    times = [t.preferred_time for t in sorted_tasks]
    assert times == ["08:00", "11:30", "14:00"]


def test_sort_by_time_does_not_mutate_original():
    """sort_by_time() must return a new list and leave the original unchanged."""
    scheduler = Scheduler()
    tasks = [
        make_timed_task("t2", "14:00"),
        make_timed_task("t1", "07:00"),
    ]
    original_order = [t.task_id for t in tasks]
    scheduler.sort_by_time(tasks)
    assert [t.task_id for t in tasks] == original_order


def test_sort_by_time_tasks_without_time_go_last():
    """Tasks with no preferred_time should appear after all timed tasks."""
    scheduler = Scheduler()
    no_time = CareTask(task_id="no_time", title="No time", duration_minutes=10,
                       priority="high", preferred_time="")
    tasks = [
        no_time,
        make_timed_task("t1", "09:00"),
        make_timed_task("t2", "06:00"),
    ]
    sorted_tasks = scheduler.sort_by_time(tasks)
    assert sorted_tasks[-1].task_id == "no_time"


# ---------------------------------------------------------------------------
# Test 4 — Recurrence logic: completing a daily task schedules the next day
# ---------------------------------------------------------------------------

def make_recurring_task(task_id: str = "r1", interval: str = "daily") -> CareTask:
    return CareTask(
        task_id=task_id,
        title="Daily Walk",
        duration_minutes=30,
        priority="high",
        preferred_time="08:00",
        is_recurring=True,
        recurrence_interval=interval,
    )


def test_mark_complete_daily_creates_next_occurrence():
    """Completing a daily recurring task must add one entry to recurring_queue."""
    scheduler = Scheduler()
    task = make_recurring_task("r1", "daily")
    scheduled = ScheduledTask(task=task, time_slot="08:00")

    next_task = scheduler.mark_task_complete(scheduled)

    assert next_task is not None
    assert len(scheduler.recurring_queue) == 1


def test_mark_complete_daily_next_date_is_tomorrow():
    """The queued next-occurrence date must be exactly today + 1 day."""
    scheduler = Scheduler()
    task = make_recurring_task("r1", "daily")
    scheduled = ScheduledTask(task=task, time_slot="08:00")

    scheduler.mark_task_complete(scheduled)

    expected_date = str(date.today() + timedelta(days=1))
    next_due_date, _ = scheduler.recurring_queue[0]
    assert next_due_date == expected_date


def test_mark_complete_weekly_next_date_is_seven_days():
    """The queued next-occurrence date for weekly tasks must be today + 7 days."""
    scheduler = Scheduler()
    task = make_recurring_task("r1", "weekly")
    scheduled = ScheduledTask(task=task, time_slot="08:00")

    scheduler.mark_task_complete(scheduled)

    expected_date = str(date.today() + timedelta(weeks=1))
    next_due_date, _ = scheduler.recurring_queue[0]
    assert next_due_date == expected_date


def test_mark_complete_non_recurring_returns_none():
    """Completing a non-recurring task must return None and leave queue empty."""
    scheduler = Scheduler()
    task = make_care_task("one_off")  # is_recurring defaults to False
    scheduled = ScheduledTask(task=task, time_slot="09:00")

    result = scheduler.mark_task_complete(scheduled)

    assert result is None
    assert len(scheduler.recurring_queue) == 0


def test_mark_complete_sets_status_to_complete():
    """mark_task_complete() must also flip the ScheduledTask status to 'complete'."""
    scheduler = Scheduler()
    task = make_recurring_task("r1", "daily")
    scheduled = ScheduledTask(task=task, time_slot="08:00")

    scheduler.mark_task_complete(scheduled)
    assert scheduled.status == "complete"


# ---------------------------------------------------------------------------
# Test 5 — Conflict detection: overlapping tasks are flagged
# ---------------------------------------------------------------------------

def make_conflict_task(task_id: str, preferred_time: str, duration_minutes: int) -> CareTask:
    return CareTask(
        task_id=task_id,
        title=f"Task {task_id}",
        duration_minutes=duration_minutes,
        priority="medium",
        preferred_time=preferred_time,
    )


def test_check_conflicts_detects_overlap():
    """check_conflicts() must return at least one warning when tasks overlap."""
    scheduler = Scheduler()
    tasks = [
        make_conflict_task("a", "09:00", 60),   # 09:00–10:00
        make_conflict_task("b", "09:30", 30),   # 09:30–10:00 — overlaps with 'a'
    ]
    conflicts = scheduler.check_conflicts(tasks)
    assert len(conflicts) >= 1


def test_check_conflicts_no_overlap_returns_empty():
    """check_conflicts() must return an empty list when no tasks overlap."""
    scheduler = Scheduler()
    tasks = [
        make_conflict_task("a", "08:00", 30),   # 08:00–08:30
        make_conflict_task("b", "09:00", 30),   # 09:00–09:30 — gap, no overlap
    ]
    conflicts = scheduler.check_conflicts(tasks)
    assert conflicts == []


def test_check_conflicts_same_start_time_is_conflict():
    """Two tasks at the exact same start time should be flagged as a conflict."""
    scheduler = Scheduler()
    tasks = [
        make_conflict_task("x", "10:00", 20),
        make_conflict_task("y", "10:00", 15),
    ]
    conflicts = scheduler.check_conflicts(tasks)
    assert len(conflicts) >= 1


def test_check_conflicts_warning_contains_task_title():
    """Conflict warnings must name the involved tasks so owners can act on them."""
    scheduler = Scheduler()
    tasks = [
        make_conflict_task("a", "09:00", 60),
        make_conflict_task("b", "09:30", 30),
    ]
    conflicts = scheduler.check_conflicts(tasks)
    assert any("Task a" in msg or "Task b" in msg for msg in conflicts)
