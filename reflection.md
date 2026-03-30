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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

The scheduler detects conflicts by comparing each task's `preferred_time` (start time) against the *end time* of the preceding task (`start + duration_minutes`). It checks adjacent pairs after sorting by start time — it does not check every possible pair combination.

**The tradeoff:** This approach catches the most common conflict two tasks whose windows overlap but it can miss a conflict where a long task spans over a much shorter task that starts and ends in its middle. For example, if Task A runs 07:00–08:00 (60 min) and Task C starts at 07:45, the check compares A→B and B→C in sorted order. If Task B starts at 07:30 and ends at 07:35, the A→B overlap is caught, but the A→C overlap may not be, because once B is flagged the loop moves on to B→C rather than re-checking A against all later tasks.

**Why it is reasonable here:** PawPal+ is a personal pet-care tool, not a hospital scheduling system. Tasks are typically short (5–30 minutes) and owners set them at distinct times. The adjacent-pair strategy covers the realistic daily schedule two breakfasts booked at the same time, a walk and a vet appointment that run into each other — without the O(n²) cost of comparing every pair. If the app scaled to many pets or complex overlapping routines, a full interval-overlap scan (e.g., a sweep-line algorithm) would be worth the added complexity.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
