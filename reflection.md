# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The initial design uses 8 classes organized around a pet care workflow.

**Owner** holds the user's contact info and a list of their pets. It acts as the entry point — you add pets through it and can retrieve all tasks across all pets.

**Pet** stores the animal's profile (name, species, age, weight, breed, health conditions) and owns a list of `CareTask` objects. It can sort tasks by priority.

**CareTask** is the base class for all tasks. It defines shared fields — title, duration, priority, preferred time, recurrence — and shared methods like `get_priority_score()` and `is_due_today()`.

Four subclasses extend `CareTask` with type-specific data:
- **FeedingTask** — food amount, type, meal time
- **WalkTask** — distance, route, energy level
- **MedicationTask** — medication name, dosage, administration route
- **AppointmentTask** — vet name, clinic, appointment type, confirmation status

**Scheduler** takes a pet's tasks and produces a `DayPlan`. It handles prioritization, conflict detection, and ordering.

**DayPlan** represents one day's schedule — a list of `ScheduledTask` objects plus any skipped tasks with reasons.

**ScheduledTask** wraps a `CareTask` with a time slot and completion status, keeping the original task definition clean and reusable.


**b. Design changes**

After reviewing the skeleton with AI assistance, several gaps emerged:

**Change 1 — Added `owner` parameter to `Scheduler.generate_daily_plan`**
The original design passed only a `Pet` to the scheduler. The review flagged that `Owner.preferred_walk_time` would be silently ignored. Updating the signature to accept an optional `Owner` lets the scheduler respect user preferences without breaking existing callers.

**Change 2 — Linked `MedicationTask` to a preceding `FeedingTask` via `required_before_task_id`**
`MedicationTask.requires_food` was a boolean with no enforcement path. The scheduler had no way to know *which* feeding task should precede the medication. Adding a `required_before_task_id: str = ""` field on `MedicationTask` gives the scheduler an explicit dependency edge to act on during `optimize_order`.

**Change 3 — Clarified `Scheduler.task_queue` lifecycle**
The queue was initialized empty but never populated before `generate_daily_plan` ran. Documented (and will implement) that `generate_daily_plan` is responsible for loading `pet.tasks` into `self.task_queue` at the start of each call, then clearing it on exit, making the flow explicit.

**Change 4 — Added `date: str` parameter to `CareTask.is_due_today`**
Without a date argument the method cannot be unit-tested or used for future-date planning. Changed the signature to `is_due_today(self, date: str) -> bool` so callers always pass the date explicitly.

---
- Identify three core actions a user should be able to perform
1. See and monitor thier pets health
2. Be able to create a schedule that can be easily modified
3. Allow a pet to be added


## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three layered constraints:

1. **Time budget** — `available_minutes_per_day` (default 480 min / 8 hours). Tasks that would exceed the remaining budget are moved to `skipped_tasks` rather than dropped silently. This is the hardest constraint: there is no point assigning a task the owner cannot physically reach.

2. **Priority** — `CareTask.get_priority_score()` maps "high/medium/low" to 3/2/1. High-priority tasks (medications, vet appointments) are sorted to the front of the queue so they are scheduled first and are least likely to be bumped by the time budget cap.

3. **Preferred time / owner preferences** — `preferred_time` on each task and `Owner.preferred_walk_time` are used to set time slots. These are soft constraints: if a WalkTask has no preferred time, the owner's walk preference fills it in; otherwise the task's own value wins.

4. **Task dependencies** — `MedicationTask.required_before_task_id` creates an ordering dependency: the linked `FeedingTask` must precede the medication. This is enforced by `_resolve_medication_order` before prioritization, so it cannot be overridden by priority sorting alone.

The time budget was treated as the most critical constraint because violating it produces an impossible schedule. Priority came second because it determines *which* tasks survive when the budget is tight. Preferred times and dependencies are applied last because they shape order without changing what is included.

**b. Tradeoffs**

The scheduler detects conflicts by comparing each task's `preferred_time` (start time) against the *end time* of the preceding task (`start + duration_minutes`). It checks adjacent pairs after sorting by start time — it does not check every possible pair combination.

**The tradeoff:** This approach catches the most common conflict two tasks whose windows overlap but it can miss a conflict where a long task spans over a much shorter task that starts and ends in its middle. For example, if Task A runs 07:00–08:00 (60 min) and Task C starts at 07:45, the check compares A→B and B→C in sorted order. If Task B starts at 07:30 and ends at 07:35, the A→B overlap is caught, but the A→C overlap may not be, because once B is flagged the loop moves on to B→C rather than re-checking A against all later tasks.

**Why it is reasonable here:** PawPal+ is a personal pet-care tool, not a hospital scheduling system. Tasks are typically short (5–30 minutes) and owners set them at distinct times. The adjacent-pair strategy covers the realistic daily schedule two breakfasts booked at the same time, a walk and a vet appointment that run into each other — without the O(n²) cost of comparing every pair. If the app scaled to many pets or complex overlapping routines, a full interval-overlap scan (e.g., a sweep-line algorithm) would be worth the added complexity.

---

## 3. AI Collaboration

**a. How you used AI**

AI tools (VS Code Copilot and Claude) were used across three distinct phases, each with a different role:

**Design phase:** Copilot Chat was used to stress-test the UML class diagram before any code was written. Prompts like *"Given this class diagram, what edge cases would the Scheduler miss?"* surfaced the missing `owner` parameter and the unenforced `requires_food` boolean — both became real design changes (see Section 1b). Asking about edge cases rather than asking "is this good?" pushed the AI toward critique rather than validation.

**Implementation phase:** Copilot's inline autocomplete was most effective for filling in boilerplate dataclass fields and `execute()` method bodies. It correctly inferred the pattern from the first subclass and reproduced it consistently across `WalkTask`, `MedicationTask`, and `AppointmentTask`. The `_time_to_minutes` helper was also suggested verbatim and accepted without modification after verifying it handled the `ValueError` case.

**Testing phase:** Copilot Chat helped draft the initial test skeletons when given the prompt *"Write pytest tests for `check_conflicts` covering: overlap detected, no overlap, same start time, and warning contains task title."* It produced four correctly structured tests. The assertions needed minor tuning (see 3b below) but the structure was sound.

The most effective prompt pattern throughout was **specificity + constraint**: naming the exact method, describing the scenario, and stating what the output format should be. Vague prompts like "improve this" produced generic suggestions; precise prompts produced targeted, usable code.

**VS Code Copilot features most effective for this project:**

- **Inline autocomplete** — fastest for repetitive dataclass patterns and helper functions. Zero context-switching cost.
- **Copilot Chat (panel)** — best for design critique and generating test scaffolds where a multi-turn conversation was needed to refine the output.
- **Inline chat (`Ctrl+I`)** — useful for quick, focused refactors on a selected block without leaving the editor.

**b. Judgment and verification**

When Copilot generated the initial `check_conflicts` tests, it wrote the overlap assertion as:

```python
assert conflicts[0] == "WARNING: 'Task a' overlaps with 'Task b'."
```

This was rejected because it hardcoded the exact warning string format. If the warning message were ever reformatted say, to include the duration or time — the test would fail for the wrong reason. The fix was to replace the equality check with a membership check:

```python
assert any("Task a" in msg or "Task b" in msg for msg in conflicts)
```

This tests the meaningful invariant (the warning names the involved tasks) without coupling the test to formatting details. The evaluation method was to ask: *"What is this test actually asserting, and would it still be true if I changed something irrelevant?"* If the answer was no, the assertion was too tight.

A second suggestion that was modified: Copilot initially generated `_resolve_medication_order` using a two-pass approach one pass to collect all FeedingTask IDs, a second pass to reorder. This was simplified to a single-pass insertion approach (the version in the final code) because the two-pass version created an intermediate dict that wasn't needed and made the control flow harder to follow at a glance.

**How separate chat sessions helped stay organized:**

Starting a new Copilot Chat session for each phase (design review → implementation → testing) prevented the conversation history from mixing concerns. A single long session drifts: later questions get colored by earlier context, and the AI starts making assumptions based on intermediate states that no longer reflect the code. Fresh sessions forced each phase to be self-contained: the design session produced a spec, the implementation session consumed that spec, and the testing session treated the final code as its only input. This mirrors how a human team would hand off between phases and keeps each AI conversation focused enough to produce reliable output.

---

## 4. Testing and Verification

**a. What you tested**

The test suite covers five behavioral areas, each chosen because it corresponds to a decision point in the scheduler where a bug would silently corrupt a user's day plan:

1. **Task completion status** — `mark_complete()` and `mark_skipped()` on `ScheduledTask`. These are the state transitions an owner relies on to know what actually happened. A status that doesn't change would make the day plan untrustworthy.

2. **Pet task list management** — `add_task()` and `remove_task()` on `Pet`. The scheduler reads `pet.tasks` directly; if add/remove had off-by-one errors or removed the wrong task, every generated plan would be wrong.

3. **Chronological sorting** — `sort_by_time()` on `Scheduler`. Three sub-cases: general ordering, immutability of the original list, and tasks with no preferred time going last. Sorting is foundational — the conflict detector and `optimize_order` both depend on it.

4. **Recurrence logic** — `mark_task_complete()` for daily and weekly tasks, non-recurring tasks, and status side-effects. Recurring tasks are the feature most likely to have off-by-one errors in date arithmetic, and a wrong next-due-date would silently drop care from a pet's future schedule.

5. **Conflict detection** — `check_conflicts()` for overlap present, no overlap, same start time, and warning content. Conflict detection is the only safety net between the scheduler and an impossible plan handed to the owner.

**b. Confidence**

Confidence is moderate-to-high for the behaviors under test, and intentionally lower for two areas:

- **`generate_daily_plan` integration** — the method is tested indirectly (its sub-steps are all covered), but there is no end-to-end test that builds a full `DayPlan` and checks the resulting `scheduled_tasks` list. An integration test here would catch wiring bugs between `prioritize_tasks`, `_resolve_medication_order`, and the budget loop.

- **The adjacent-pair conflict gap** — documented in Section 2b. A task that spans over a shorter task in its middle will not always be caught. A test with three tasks exhibiting that pattern would formally confirm the known limitation.

Edge cases to test next:
- Two pets whose tasks conflict with each other (cross-pet conflict `check_all_conflicts`)
- A pet with zero tasks (empty plan, no crash)
- A task whose `duration_minutes` equals the remaining budget exactly (boundary: should be scheduled, not skipped)
- `mark_task_complete` called twice on the same recurring task (should not add duplicate entries to `recurring_queue`)

---

## 5. Reflection

**a. What went well**

The part of the project I am most satisfied with is the layered constraint resolution in `generate_daily_plan`. The method handles four concerns — dependency ordering, priority sorting, time-based optimization, and budget capping — in a clear pipeline where each step has a single responsibility. When I had to debug the medication ordering, I could isolate `_resolve_medication_order` without touching the rest. That separation made both the implementation and the testing easier than I expected going in.

The decision to add `required_before_task_id` to `MedicationTask` also went well. It replaced an unenforceable boolean flag (`requires_food: bool`) with an explicit dependency that the scheduler can act on. That change came from an AI critique session and turned out to be the most structurally important design improvement in the project.

**b. What you would improve**

The `is_due_today` method is a stub — it always returns `True`, which means the scheduler currently has no way to filter tasks by actual date or recurrence pattern. If I had another iteration, I would implement real recurrence logic there: non-recurring tasks would have an explicit `scheduled_date` field and only be due on that date; daily tasks would always return `True`; weekly tasks would check whether `for_date` falls on the correct day of the week. Without this, the recurrence system built around `mark_task_complete` and `recurring_queue` is not fully connected to plan generation.

I would also add a full integration test for `generate_daily_plan` that sets up a realistic mix of task types, runs the scheduler, and asserts on the ordered output — verifying that the pipeline as a whole produces a plan that matches the declared constraints.

**c. Key takeaway**

The most important thing I learned is that being the "lead architect" when working with AI means owning the *invariants*, not the *implementation details*. The AI can write correct-looking code quickly, but it does not know which correctness properties matter to your system. My job was to decide: "what must always be true here, and what would a bug in this method silently break?" Once I held that frame, I could evaluate AI suggestions not by whether they ran, but by whether they preserved the right invariants — and reject or modify the ones that did not, even when the code looked fine at first glance. That discipline — staying in the role of the person who knows *why* the system exists, not just *how* it should be implemented — is what kept the design coherent despite using AI acceleration throughout.
