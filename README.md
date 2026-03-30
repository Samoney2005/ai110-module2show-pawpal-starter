# PawPal+ (Module 2 Project)

PawPal+ is a Streamlit app that helps pet owners stay consistent with daily care by generating smart, conflict-free schedules for one or more pets.

---

## ✨ Features

- **Pet & Owner Profiles** — Register owner preferences (including a preferred walk time) and one or more pets with species, breed, age, weight, and health conditions.
- **Multiple Task Types** — The system layer defines four specialised subclasses (`FeedingTask`, `WalkTask`, `MedicationTask`, `AppointmentTask`), each with type-specific fields (food amount, distance, dosage, vet info, etc.). The current UI uses the base `CareTask` form to keep the interface simple.
- **Sorting by Time** — Tasks are always displayed and scheduled in chronological order using a minutes-since-midnight sort key, regardless of the order they were entered.
- **Priority-Based Scheduling** — A `high / medium / low` priority field ensures critical tasks (e.g., medication) are scheduled before lower-priority ones when time is tight.
- **Daily Budget Enforcement** — The scheduler allocates tasks within a configurable daily time budget; tasks that don't fit are automatically moved to a "skipped" list with an explanation.
- **Conflict Warnings** — An adjacent-pair sweep detects overlapping tasks before and after plan generation, surfacing human-readable warnings without crashing the app.
- **Cross-Pet Conflict Detection** — `check_all_conflicts` spans multiple pets' `DayPlan` objects, labelling each warning as `[same pet]` or `[cross-pet]` for immediate clarity. This is a system-layer capability; the current UI manages one pet at a time.
- **Daily & Weekly Recurrence** — Marking a recurring task complete automatically queues the next occurrence (+1 day or +7 days) using Python's `timedelta`.
- **Medication Ordering Constraint** — Feeding tasks linked to a medication are always placed first, preventing logical scheduling errors.
- **In-Place Task Editing** — An "Edit" panel lets the owner update any task's title, time, duration, priority, or recurrence without deleting and re-adding it. Saving invalidates the current plan so the next generation reflects the changes.
- **Task Status Tracking** — Each scheduled task moves through `pending → complete / skipped`, with skip reasons stored for user feedback.
- **Automated Test Suite** — 16 pytest tests cover sorting correctness, recurrence logic, conflict detection, and core task operations.

---

## 📸 Demo

<a href="/course_images/ai110/pawpal_screenshot.png" target="_blank"><img src='/course_images/ai110/pawpal_screenshot.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

---

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

## Testing PawPal+

### Running the test suite

```bash
python -m pytest
```

Add `-v` for verbose output that names each individual test:

```bash
python -m pytest -v
```

### What the tests cover

| Area | Tests | What is verified |
|---|---|---|
| **Sorting correctness** | 3 | `sort_by_time()` returns tasks in chronological order; the original list is not mutated; tasks without a preferred time sort last |
| **Recurrence logic** | 5 | Completing a daily task queues the next occurrence for tomorrow; weekly recurrence queues +7 days; non-recurring tasks return `None`; `ScheduledTask.status` flips to `"complete"` |
| **Conflict detection** | 4 | Overlapping tasks produce at least one warning; non-overlapping tasks produce none; identical start times are flagged; warning messages name the conflicting tasks |
| **Core task/pet operations** | 4 | `mark_complete`, `mark_skipped`, `add_task`, `remove_task` behave correctly |

### Confidence Level

**★★★★☆ (4/5)**

All 16 tests pass and cover the three most critical scheduling behaviors — ordering, recurrence, and conflict detection. The suite catches regressions in the core logic layer. One star is withheld because the tests do not yet exercise the full `generate_daily_plan` pipeline end-to-end or the Streamlit UI layer, so integration-level bugs could still slip through.

---

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
