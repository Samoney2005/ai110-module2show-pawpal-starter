# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

PawPal+ goes beyond a simple task list — the `Scheduler` class contains algorithmic logic that keeps daily pet-care plans accurate and conflict-free.

### Sorting by time

`Scheduler.sort_by_time(tasks)` orders any list of `CareTask` objects chronologically using a lambda key that converts `"HH:MM"` strings to minutes-since-midnight via `_time_to_minutes`. Tasks with no preferred time sort last. This means you can add tasks in any order and always get a clean, time-ordered view.

### Filtering tasks

`Scheduler.filter_tasks(scheduled_tasks, status, pet_name, pet)` narrows down a pet's scheduled tasks by:
- **Status** — show only `"pending"`, `"complete"`, or `"skipped"` tasks.
- **Pet name** — confirm that a set of tasks belongs to the expected pet before displaying or processing them.

Neither filter raises an exception on a mismatch; it simply returns an empty list, keeping the app resilient.

### Recurring task automation

`Scheduler.mark_task_complete(scheduled_task)` does two things at once: it marks the current task done *and* — for recurring tasks — uses Python's `timedelta` to calculate the next occurrence (`daily` → +1 day, `weekly` → +7 days). A shallow copy of the original task is queued in `Scheduler.recurring_queue` with a new ID and due date, ready to be picked up when the next day's plan is generated.

### Conflict detection

`Scheduler.check_conflicts(tasks)` and `Scheduler.check_all_conflicts(plans)` use a lightweight adjacent-pair sweep:

1. All tasks are sorted by start time.
2. Each task's end time (`start + duration_minutes`) is compared to the next task's start time.
3. Any overlap produces a human-readable `WARNING` string — no exceptions are raised.

`check_all_conflicts` extends this across multiple pets' `DayPlan` objects, labelling each warning as `[same pet]` or `[cross-pet]` so the source of the conflict is immediately clear.

---

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
