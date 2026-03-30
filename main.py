"""
PawPal+ Demo Script
Run: python main.py
"""

from pawpal_system import (
    Owner, Pet, Scheduler,
    FeedingTask, WalkTask, MedicationTask, AppointmentTask,
)


# ---------------------------------------------------------------------------
# Build the owner
# ---------------------------------------------------------------------------

owner = Owner(
    name="Jordan Rivera",
    email="jordan@example.com",
    phone="555-0199",
    preferred_walk_time="07:30",
)

# ---------------------------------------------------------------------------
# Pet 1 — Rex the Labrador
# ---------------------------------------------------------------------------

rex = Pet(name="Rex", species="Dog", age=4, weight_kg=28.0, breed="Labrador")

rex.add_task(FeedingTask(
    task_id="rex-f1",
    title="Morning Feed",
    duration_minutes=10,
    priority="high",
    preferred_time="07:00",
    food_amount_cups=2.5,
    food_type="dry kibble",
    is_recurring=True,
    recurrence_interval="daily",
))

rex.add_task(MedicationTask(
    task_id="rex-m1",
    title="Allergy Pill",
    duration_minutes=5,
    priority="high",
    preferred_time="07:10",
    medication_name="Apoquel",
    dosage_mg=16.0,
    administration_route="oral",
    requires_food=True,
    required_before_task_id="rex-f1",
))

rex.add_task(WalkTask(
    task_id="rex-w1",
    title="Morning Walk",
    duration_minutes=30,
    priority="medium",
    preferred_time="",          # will be filled from owner preference
    distance_km=2.5,
    route_preference="park loop",
    energy_level_required="medium",
    is_recurring=True,
    recurrence_interval="daily",
))

rex.add_task(FeedingTask(
    task_id="rex-f2",
    title="Evening Feed",
    duration_minutes=10,
    priority="high",
    preferred_time="18:00",
    food_amount_cups=2.5,
    food_type="dry kibble",
    is_recurring=True,
    recurrence_interval="daily",
))

# ---------------------------------------------------------------------------
# Pet 2 — Luna the Persian Cat
# ---------------------------------------------------------------------------

luna = Pet(name="Luna", species="Cat", age=2, weight_kg=4.2, breed="Persian",
           health_conditions=["sensitive stomach"])

luna.add_task(FeedingTask(
    task_id="luna-f1",
    title="Breakfast",
    duration_minutes=5,
    priority="high",
    preferred_time="08:00",
    food_amount_cups=0.5,
    food_type="wet food — sensitive formula",
    is_recurring=True,
    recurrence_interval="daily",
))

luna.add_task(MedicationTask(
    task_id="luna-m1",
    title="Probiotic Supplement",
    duration_minutes=5,
    priority="medium",
    preferred_time="08:05",
    medication_name="FortiFlora",
    dosage_mg=1000.0,
    administration_route="oral (mixed into food)",
    requires_food=True,
    required_before_task_id="luna-f1",
))

luna.add_task(AppointmentTask(
    task_id="luna-a1",
    title="Annual Check-up",
    duration_minutes=60,
    priority="high",
    preferred_time="10:00",
    vet_name="Dr. Patel",
    clinic_name="Sunrise Animal Clinic",
    appointment_type="annual check-up",
    location="123 Maple St",
    is_confirmed=True,
))

# ---------------------------------------------------------------------------
# Register pets with owner
# ---------------------------------------------------------------------------

owner.add_pet(rex)
owner.add_pet(luna)

# ---------------------------------------------------------------------------
# Generate and print daily plans
# ---------------------------------------------------------------------------

scheduler = Scheduler(scheduling_strategy="time", available_minutes_per_day=480)


def print_banner(text: str) -> None:
    width = 60
    print("\n" + "=" * width)
    print(f"  {text}")
    print("=" * width)


def print_plan(plan) -> None:
    conflicts = scheduler.check_conflicts(
        [st.task for st in plan.scheduled_tasks]
    )

    print(f"\n  Pet   : {plan.pet.name} ({plan.pet.breed} {plan.pet.species})")
    print(f"  Date  : {plan.date}")
    print(f"  Total : {plan.total_duration_minutes} min scheduled\n")

    if plan.scheduled_tasks:
        print(f"  {'TIME':<8} {'TASK':<28} {'PRIORITY':<10} {'MINS':<6} STATUS")
        print("  " + "-" * 56)
        for st in plan.scheduled_tasks:
            t = st.task
            print(
                f"  {st.time_slot:<8} {t.title:<28} {t.priority:<10} "
                f"{t.duration_minutes:<6} {st.status}"
            )

    if plan.skipped_tasks:
        print("\n  Skipped (over daily budget):")
        for t in plan.skipped_tasks:
            print(f"    - {t.title}")

    if conflicts:
        print("\n  ⚠ Conflicts detected:")
        for c in conflicts:
            print(f"    {c}")
    else:
        print("\n  No scheduling conflicts.")


print_banner("PawPal+  —  Today's Schedule")
print(f"\n  Owner : {owner.name}  |  {owner.email}  |  {owner.phone}")

for pet in owner.pets:
    plan = scheduler.generate_daily_plan(pet, owner)
    print_banner(f"Schedule for {pet.name}")
    print_plan(plan)

print("\n" + "=" * 60 + "\n")
