"""
PawPal+ Logic Layer
Backend classes based on the UML class diagram.
"""

from __future__ import annotations
import copy
from dataclasses import dataclass, field
from datetime import date as _date, timedelta
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _time_to_minutes(t: str) -> int:
    """Convert 'HH:MM' to minutes since midnight. Returns -1 on parse failure."""
    try:
        h, m = t.split(":")
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError):
        return -1


# ---------------------------------------------------------------------------
# Data classes (simple value objects with no heavy behaviour)
# ---------------------------------------------------------------------------

@dataclass
class CareTask:
    task_id: str
    title: str
    duration_minutes: int
    priority: str                   # "high", "medium", "low"
    preferred_time: str             # "HH:MM"
    is_recurring: bool = False
    recurrence_interval: str = ""   # "daily", "weekly"
    notes: str = ""

    def get_priority_score(self) -> int:
        """Return a numeric score for sorting (higher = more urgent)."""
        return {"high": 3, "medium": 2, "low": 1}.get(self.priority.lower(), 0)

    def is_due_today(self, for_date: str = "") -> bool:
        """Return True if this task should be completed on for_date (YYYY-MM-DD).

        Simplified rules:
        - Non-recurring tasks are always considered due (no scheduled_date field).
        - "daily" recurring tasks are always due.
        - "weekly" recurring tasks are always due (caller can filter by weekday if needed).
        """
        return True


@dataclass
class FeedingTask(CareTask):
    food_amount_cups: float = 0.0
    food_type: str = ""
    meal_time: str = ""
    has_medication_mixed_in: bool = False

    def execute(self) -> None:
        """Carry out the feeding task."""
        print(
            f"[FeedingTask] Feeding {self.food_amount_cups} cups of {self.food_type}"
            f"{' (with medication mixed in)' if self.has_medication_mixed_in else ''}."
        )


@dataclass
class WalkTask(CareTask):
    distance_km: float = 0.0
    route_preference: str = ""
    energy_level_required: str = ""  # "low", "medium", "high"
    needs_leash: bool = True

    def execute(self) -> None:
        """Carry out the walk task."""
        leash = "on leash" if self.needs_leash else "off leash"
        print(
            f"[WalkTask] Walking {self.distance_km} km via '{self.route_preference}' "
            f"({leash}, energy: {self.energy_level_required})."
        )


@dataclass
class MedicationTask(CareTask):
    medication_name: str = ""
    dosage_mg: float = 0.0
    administration_route: str = ""  # "oral", "topical"
    prescribing_vet: str = ""
    requires_food: bool = False
    required_before_task_id: str = ""  # ID of a FeedingTask that must precede this

    def execute(self) -> None:
        """Carry out the medication task."""
        print(
            f"[MedicationTask] Administering {self.dosage_mg} mg of {self.medication_name} "
            f"via {self.administration_route}"
            f"{' (after food)' if self.requires_food else ''}."
        )


@dataclass
class AppointmentTask(CareTask):
    vet_name: str = ""
    clinic_name: str = ""
    appointment_type: str = ""      # "check-up", "vaccination"
    location: str = ""
    is_confirmed: bool = False

    def execute(self) -> None:
        """Carry out the appointment task."""
        status = "confirmed" if self.is_confirmed else "unconfirmed"
        print(
            f"[AppointmentTask] {self.appointment_type} with {self.vet_name} "
            f"at {self.clinic_name} ({status})."
        )


@dataclass
class Pet:
    name: str
    species: str
    age: int
    weight_kg: float
    breed: str = ""
    health_conditions: List[str] = field(default_factory=list)
    tasks: List[CareTask] = field(default_factory=list)

    def add_task(self, task: CareTask) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove a care task by its ID."""
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def get_tasks_by_priority(self) -> List[CareTask]:
        """Return tasks sorted from highest to lowest priority."""
        return sorted(self.tasks, key=lambda t: t.get_priority_score(), reverse=True)


@dataclass
class ScheduledTask:
    task: CareTask
    time_slot: str
    status: str = "pending"         # "pending", "complete", "skipped"
    skip_reason: str = ""

    def mark_complete(self) -> None:
        """Mark this scheduled task as completed."""
        self.status = "complete"

    def mark_skipped(self, reason: str) -> None:
        """Mark this scheduled task as skipped with a reason."""
        self.status = "skipped"
        self.skip_reason = reason


@dataclass
class DayPlan:
    date: str
    pet: Pet
    scheduled_tasks: List[ScheduledTask] = field(default_factory=list)
    skipped_tasks: List[CareTask] = field(default_factory=list)
    total_duration_minutes: int = 0

    def add_task(self, task: CareTask, time_slot: str) -> None:
        """Schedule a task into a specific time slot."""
        self.scheduled_tasks.append(ScheduledTask(task=task, time_slot=time_slot))
        self.total_duration_minutes += task.duration_minutes

    def remove_task(self, task_id: str) -> None:
        """Remove a scheduled task by its care-task ID."""
        removed = [st for st in self.scheduled_tasks if st.task.task_id == task_id]
        self.scheduled_tasks = [st for st in self.scheduled_tasks if st.task.task_id != task_id]
        for st in removed:
            self.total_duration_minutes -= st.task.duration_minutes

    def get_summary(self) -> str:
        """Return a human-readable summary of the day plan."""
        lines = [
            f"Day Plan for {self.pet.name} — {self.date}",
            f"Total time: {self.total_duration_minutes} min",
            "",
        ]
        if self.scheduled_tasks:
            lines.append("Scheduled:")
            for st in self.scheduled_tasks:
                lines.append(
                    f"  [{st.status.upper()}] {st.time_slot}  {st.task.title} "
                    f"({st.task.duration_minutes} min, priority={st.task.priority})"
                )
        if self.skipped_tasks:
            lines.append("\nSkipped:")
            for t in self.skipped_tasks:
                lines.append(f"  - {t.title}")
        return "\n".join(lines)

    def export_to_dict(self) -> dict:
        """Export the plan as a plain dictionary (e.g. for JSON serialisation)."""
        return {
            "date": self.date,
            "pet": self.pet.name,
            "total_duration_minutes": self.total_duration_minutes,
            "scheduled_tasks": [
                {
                    "task_id": st.task.task_id,
                    "title": st.task.title,
                    "time_slot": st.time_slot,
                    "duration_minutes": st.task.duration_minutes,
                    "priority": st.task.priority,
                    "status": st.status,
                    "skip_reason": st.skip_reason,
                }
                for st in self.scheduled_tasks
            ],
            "skipped_tasks": [
                {"task_id": t.task_id, "title": t.title}
                for t in self.skipped_tasks
            ],
        }


# ---------------------------------------------------------------------------
# Regular classes (contain meaningful logic / state management)
# ---------------------------------------------------------------------------

class Owner:
    def __init__(
        self,
        name: str,
        email: str,
        phone: str,
        preferred_walk_time: str = "",
    ) -> None:
        """Initialise an Owner with contact details and an empty pet list."""
        self.name = name
        self.email = email
        self.phone = phone
        self.preferred_walk_time = preferred_walk_time
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a new pet under this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name from this owner's list."""
        self.pets = [p for p in self.pets if p.name != pet_name]

    def get_all_tasks(self) -> List[CareTask]:
        """Return every care task across all owned pets."""
        all_tasks: List[CareTask] = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks


class Scheduler:
    def __init__(
        self,
        scheduling_strategy: str = "priority",
        available_minutes_per_day: int = 480,
    ) -> None:
        """Initialise the Scheduler with a strategy and daily time budget."""
        self.task_queue: List[CareTask] = []
        self.scheduling_strategy = scheduling_strategy
        self.available_minutes_per_day = available_minutes_per_day
        # Holds (next_due_date, cloned_task) pairs for recurring tasks that have
        # been completed and are waiting to be scheduled on a future day.
        self.recurring_queue: List[Tuple[str, CareTask]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_daily_plan(self, pet: Pet, owner: Optional[Owner] = None) -> DayPlan:
        """Build and return a DayPlan for the given pet.

        Steps:
        1. Load pet tasks into the queue.
        2. Filter to tasks due today.
        3. Prioritize / optimize order.
        4. Assign time slots respecting the daily budget.
        5. Place overflow tasks into skipped_tasks.
        """
        today = str(_date.today())
        plan = DayPlan(date=today, pet=pet)

        # Load queue from pet tasks that are due today
        self.task_queue = [t for t in pet.tasks if t.is_due_today(today)]

        # Apply owner walk-time preference to any WalkTask
        if owner and owner.preferred_walk_time:
            for task in self.task_queue:
                if isinstance(task, WalkTask) and not task.preferred_time:
                    task.preferred_time = owner.preferred_walk_time

        # Resolve MedicationTask ordering: tasks that require_food should come
        # after their linked FeedingTask.
        self.task_queue = self._resolve_medication_order(self.task_queue)

        ordered = self.prioritize_tasks(self.task_queue)
        ordered = self.optimize_order(ordered)

        budget = self.available_minutes_per_day
        for task in ordered:
            if task.duration_minutes <= budget:
                slot = task.preferred_time or "09:00"
                plan.add_task(task, slot)
                budget -= task.duration_minutes
            else:
                plan.skipped_tasks.append(task)

        self.task_queue = []  # clear after use
        return plan

    def prioritize_tasks(self, tasks: List[CareTask]) -> List[CareTask]:
        """Return tasks sorted by the chosen scheduling strategy."""
        if self.scheduling_strategy == "priority":
            return sorted(tasks, key=lambda t: t.get_priority_score(), reverse=True)
        elif self.scheduling_strategy == "time":
            return sorted(tasks, key=lambda t: _time_to_minutes(t.preferred_time))
        else:
            return list(tasks)

    def check_conflicts(self, tasks: List[CareTask]) -> List[str]:
        """Return a list of conflict descriptions for overlapping tasks.

        Lightweight strategy: sort tasks by start time, then walk adjacent pairs.
        Returns warning strings instead of raising exceptions so callers can
        decide how to surface the information.
        """
        conflicts: List[str] = []
        timed = [(t, _time_to_minutes(t.preferred_time)) for t in tasks
                 if _time_to_minutes(t.preferred_time) >= 0]
        timed.sort(key=lambda x: x[1])

        for i in range(len(timed) - 1):
            task_a, start_a = timed[i]
            task_b, start_b = timed[i + 1]
            end_a = start_a + task_a.duration_minutes
            if end_a > start_b:
                conflicts.append(
                    f"WARNING: '{task_a.title}' ({task_a.preferred_time}, "
                    f"{task_a.duration_minutes} min) overlaps with "
                    f"'{task_b.title}' ({task_b.preferred_time})."
                )
        return conflicts

    def check_all_conflicts(self, plans: List[DayPlan]) -> List[str]:
        """Detect scheduling conflicts across all pets' day plans.

        Combines every scheduled task from every plan into one timeline, then
        walks adjacent pairs to find overlaps — the same lightweight strategy
        used by check_conflicts, but pet names are included in each warning so
        it is clear whether a conflict is within one pet's schedule or between
        two different pets.

        Returns a (possibly empty) list of human-readable warning strings.
        """
        # Build a flat list of (pet_name, task, start_minutes)
        entries: List[Tuple[str, CareTask, int]] = []
        for plan in plans:
            for st in plan.scheduled_tasks:
                minutes = _time_to_minutes(st.time_slot)
                if minutes >= 0:
                    entries.append((plan.pet.name, st.task, minutes))

        entries.sort(key=lambda e: e[2])  # sort by start time

        conflicts: List[str] = []
        for i in range(len(entries) - 1):
            pet_a, task_a, start_a = entries[i]
            pet_b, task_b, start_b = entries[i + 1]
            end_a = start_a + task_a.duration_minutes
            if end_a > start_b:
                scope = (
                    f"[same pet: {pet_a}]"
                    if pet_a == pet_b
                    else f"[cross-pet: {pet_a} / {pet_b}]"
                )
                conflicts.append(
                    f"WARNING {scope}: '{task_a.title}' "
                    f"({task_a.preferred_time}, {task_a.duration_minutes} min) "
                    f"overlaps with '{task_b.title}' ({task_b.preferred_time})."
                )
        return conflicts

    def sort_by_time(self, tasks: List[CareTask]) -> List[CareTask]:
        """Return tasks sorted chronologically by their preferred_time ('HH:MM').

        Uses a lambda with ``_time_to_minutes`` as the sort key so that string
        times like ``'09:00'`` and ``'14:30'`` are compared numerically rather
        than lexically.  Tasks with no preferred_time (empty string or
        unparseable value) are placed at the end of the list.

        Args:
            tasks: The list of CareTask objects to sort. The original list is
                   not modified.

        Returns:
            A new list of CareTask objects ordered from earliest to latest
            preferred_time.
        """
        return sorted(
            tasks,
            key=lambda t: (
                _time_to_minutes(t.preferred_time)
                if _time_to_minutes(t.preferred_time) >= 0
                else 9999
            ),
        )

    def filter_tasks(
        self,
        scheduled_tasks: List[ScheduledTask],
        status: Optional[str] = None,
        pet_name: Optional[str] = None,
        pet: Optional[Pet] = None,
    ) -> List[ScheduledTask]:
        """Return scheduled tasks filtered by completion status and/or pet name.

        Args:
            scheduled_tasks: The list of ScheduledTask objects to filter.
                             The original list is not modified.
            status:    Keep only tasks whose status equals this value
                       (``"pending"``, ``"complete"``, or ``"skipped"``).
                       Pass ``None`` to skip status filtering.
            pet_name:  When supplied, only return results if *pet* matches
                       this name.  Pass ``None`` to skip pet-name filtering.
            pet:       The Pet whose plan *scheduled_tasks* belongs to.
                       Required when *pet_name* is provided; if omitted while
                       *pet_name* is set, an empty list is returned.

        Returns:
            A new list containing only the ScheduledTask objects that satisfy
            all supplied filter criteria.
        """
        result: List[ScheduledTask] = list(scheduled_tasks)
        if status is not None:
            result = [st for st in result if st.status == status]
        if pet_name is not None:
            if pet is None or pet.name != pet_name:
                result = []
        return result

    def mark_task_complete(self, scheduled_task: ScheduledTask) -> Optional[CareTask]:
        """Mark a scheduled task complete and auto-schedule the next occurrence.

        If the underlying CareTask is recurring, this method:
        1. Marks the task as complete.
        2. Clones the task with a new ``task_id`` (original ID + next due date).
        3. Calculates the next due date using ``timedelta``:
           - ``"daily"``  → today + 1 day
           - ``"weekly"`` → today + 7 days
        4. Appends ``(next_due_date, cloned_task)`` to ``self.recurring_queue``
           so the caller can incorporate it into the next day's plan.

        Returns the cloned next-occurrence CareTask, or ``None`` for one-off tasks.
        """
        scheduled_task.mark_complete()
        task = scheduled_task.task

        if not task.is_recurring:
            return None

        today = _date.today()
        if task.recurrence_interval == "daily":
            next_date = today + timedelta(days=1)
        elif task.recurrence_interval == "weekly":
            next_date = today + timedelta(weeks=1)
        else:
            return None

        next_due_str = str(next_date)
        next_task = copy.copy(task)
        next_task.task_id = f"{task.task_id}-{next_due_str}"
        self.recurring_queue.append((next_due_str, next_task))
        return next_task

    def optimize_order(self, tasks: List[CareTask]) -> List[CareTask]:
        """Re-order tasks to respect preferred_time while keeping priority ties stable."""
        # Sort by preferred_time first (chronological), using priority as tiebreaker.
        def sort_key(t: CareTask):
            minutes = _time_to_minutes(t.preferred_time)
            # Tasks without a preferred_time go last; invert priority for tie-breaking.
            return (minutes if minutes >= 0 else 9999, -t.get_priority_score())

        return sorted(tasks, key=sort_key)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_medication_order(self, tasks: List[CareTask]) -> List[CareTask]:
        """Ensure FeedingTasks linked by MedicationTask.required_before_task_id
        appear before the medication task in the queue."""
        id_to_task = {t.task_id: t for t in tasks}
        result: List[CareTask] = []
        inserted: set = set()

        for task in tasks:
            if task.task_id in inserted:
                continue
            if isinstance(task, MedicationTask) and task.required_before_task_id:
                feeding = id_to_task.get(task.required_before_task_id)
                if feeding and feeding.task_id not in inserted:
                    result.append(feeding)
                    inserted.add(feeding.task_id)
            result.append(task)
            inserted.add(task.task_id)

        return result
