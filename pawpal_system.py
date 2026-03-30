"""
PawPal+ Logic Layer
Backend classes based on the UML class diagram.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date as _date
from typing import List, Optional


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
        self.task_queue: List[CareTask] = []
        self.scheduling_strategy = scheduling_strategy
        self.available_minutes_per_day = available_minutes_per_day

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
        """Return a list of conflict descriptions for overlapping tasks."""
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
                    f"Conflict: '{task_a.title}' ({task_a.preferred_time}, "
                    f"{task_a.duration_minutes} min) overlaps with "
                    f"'{task_b.title}' ({task_b.preferred_time})."
                )
        return conflicts

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
