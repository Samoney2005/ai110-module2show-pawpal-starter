"""
PawPal+ Logic Layer
Backend classes based on the UML class diagram.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Data classes (simple value objects with no heavy behaviour)
# ---------------------------------------------------------------------------

@dataclass
class CareTask:
    task_id: str
    title: str
    duration_minutes: int
    priority: str                   # e.g. "high", "medium", "low"
    preferred_time: str             # e.g. "08:00"
    is_recurring: bool = False
    recurrence_interval: str = ""   # e.g. "daily", "weekly"
    notes: str = ""

    def get_priority_score(self) -> int:
        """Return a numeric score for sorting (higher = more urgent)."""
        pass

    def is_due_today(self) -> bool:
        """Return True if this task should be completed today."""
        pass


@dataclass
class FeedingTask(CareTask):
    food_amount_cups: float = 0.0
    food_type: str = ""
    meal_time: str = ""
    has_medication_mixed_in: bool = False

    def execute(self) -> None:
        """Carry out the feeding task."""
        pass


@dataclass
class WalkTask(CareTask):
    distance_km: float = 0.0
    route_preference: str = ""
    energy_level_required: str = ""  # e.g. "low", "medium", "high"
    needs_leash: bool = True

    def execute(self) -> None:
        """Carry out the walk task."""
        pass


@dataclass
class MedicationTask(CareTask):
    medication_name: str = ""
    dosage_mg: float = 0.0
    administration_route: str = ""  # e.g. "oral", "topical"
    prescribing_vet: str = ""
    requires_food: bool = False

    def execute(self) -> None:
        """Carry out the medication task."""
        pass


@dataclass
class AppointmentTask(CareTask):
    vet_name: str = ""
    clinic_name: str = ""
    appointment_type: str = ""      # e.g. "check-up", "vaccination"
    location: str = ""
    is_confirmed: bool = False

    def execute(self) -> None:
        """Carry out the appointment task."""
        pass


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
        pass

    def remove_task(self, task_id: str) -> None:
        """Remove a care task by its ID."""
        pass

    def get_tasks_by_priority(self) -> List[CareTask]:
        """Return tasks sorted from highest to lowest priority."""
        pass


@dataclass
class ScheduledTask:
    task: CareTask
    time_slot: str
    status: str = "pending"         # "pending", "complete", "skipped"
    skip_reason: str = ""

    def mark_complete(self) -> None:
        """Mark this scheduled task as completed."""
        pass

    def mark_skipped(self, reason: str) -> None:
        """Mark this scheduled task as skipped with a reason."""
        pass


@dataclass
class DayPlan:
    date: str
    pet: Pet
    scheduled_tasks: List[ScheduledTask] = field(default_factory=list)
    skipped_tasks: List[CareTask] = field(default_factory=list)
    total_duration_minutes: int = 0

    def add_task(self, task: CareTask, time_slot: str) -> None:
        """Schedule a task into a specific time slot."""
        pass

    def remove_task(self, task_id: str) -> None:
        """Remove a scheduled task by its care-task ID."""
        pass

    def get_summary(self) -> str:
        """Return a human-readable summary of the day plan."""
        pass

    def export_to_dict(self) -> dict:
        """Export the plan as a plain dictionary (e.g. for JSON serialisation)."""
        pass


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
        pass

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name from this owner's list."""
        pass

    def get_all_tasks(self) -> List[CareTask]:
        """Return every care task across all owned pets."""
        pass


class Scheduler:
    def __init__(
        self,
        scheduling_strategy: str = "priority",
        available_minutes_per_day: int = 480,
    ) -> None:
        self.task_queue: List[CareTask] = []
        self.scheduling_strategy = scheduling_strategy
        self.available_minutes_per_day = available_minutes_per_day

    def generate_daily_plan(self, pet: Pet) -> DayPlan:
        """Build and return a DayPlan for the given pet."""
        pass

    def prioritize_tasks(self, tasks: List[CareTask]) -> List[CareTask]:
        """Return tasks sorted by the chosen scheduling strategy."""
        pass

    def check_conflicts(self, tasks: List[CareTask]) -> List[str]:
        """Return a list of conflict descriptions for overlapping tasks."""
        pass

    def optimize_order(self, tasks: List[CareTask]) -> List[CareTask]:
        """Re-order tasks to minimise travel/effort and respect time preferences."""
        pass
