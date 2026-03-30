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

# ---------------------------------------------------------------------------
# Step 2: Sorting and Filtering demo
# ---------------------------------------------------------------------------

print_banner("Step 2 — Sorting & Filtering")

# --- sort_by_time demo ---
# Collect Rex's tasks intentionally out of order (evening feed first)
tasks_out_of_order = [
    rex.tasks[3],   # Evening Feed   18:00
    rex.tasks[2],   # Morning Walk   (no time — gets owner default later)
    rex.tasks[1],   # Allergy Pill   07:10
    rex.tasks[0],   # Morning Feed   07:00
]

print("\n  Tasks added OUT of order:")
for t in tasks_out_of_order:
    print(f"    [{t.preferred_time or '  --  '}]  {t.title}")

sorted_tasks = scheduler.sort_by_time(tasks_out_of_order)

print("\n  After sort_by_time():")
for t in sorted_tasks:
    print(f"    [{t.preferred_time or '  --  '}]  {t.title}")

# --- filter_tasks demo ---
# Generate fresh plans so we have ScheduledTask objects to filter
rex_plan  = scheduler.generate_daily_plan(rex,  owner)
luna_plan = scheduler.generate_daily_plan(luna, owner)

# Mark a couple of tasks complete so filtering by status is meaningful
rex_plan.scheduled_tasks[0].mark_complete()
luna_plan.scheduled_tasks[0].mark_complete()

print("\n  --- Filter: Rex tasks with status='complete' ---")
complete_rex = scheduler.filter_tasks(
    rex_plan.scheduled_tasks, status="complete", pet_name="Rex", pet=rex
)
for st in complete_rex:
    print(f"    [{st.status.upper()}] {st.time_slot}  {st.task.title}")

print("\n  --- Filter: Rex tasks with status='pending' ---")
pending_rex = scheduler.filter_tasks(
    rex_plan.scheduled_tasks, status="pending", pet_name="Rex", pet=rex
)
for st in pending_rex:
    print(f"    [{st.status.upper()}] {st.time_slot}  {st.task.title}")

print("\n  --- Filter: Luna tasks with status='pending' ---")
pending_luna = scheduler.filter_tasks(
    luna_plan.scheduled_tasks, status="pending", pet_name="Luna", pet=luna
)
for st in pending_luna:
    print(f"    [{st.status.upper()}] {st.time_slot}  {st.task.title}")

# Wrong pet name → should return empty list
wrong_pet = scheduler.filter_tasks(
    rex_plan.scheduled_tasks, pet_name="Luna", pet=rex
)
print(f"\n  Filter Rex plan for pet_name='Luna' → {len(wrong_pet)} result(s) (expected 0)")

print("\n" + "=" * 60 + "\n")

# ---------------------------------------------------------------------------
# Step 3: Automate Recurring Tasks demo
# ---------------------------------------------------------------------------

print_banner("Step 3 — Recurring Task Automation")

# Fresh plans for this demo
rex_plan3  = scheduler.generate_daily_plan(rex,  owner)
luna_plan3 = scheduler.generate_daily_plan(luna, owner)

print("\n  Completing recurring tasks via scheduler.mark_task_complete()...\n")

# Complete all of Rex's scheduled tasks
for st in rex_plan3.scheduled_tasks:
    next_task = scheduler.mark_task_complete(st)
    recur_note = (
        f"  → next occurrence queued for {next_task.task_id.split('-', 2)[-1]}"
        if next_task else "  (one-off, no recurrence)"
    )
    print(f"  [{st.status.upper()}] {st.task.title}{recur_note}")

# Complete Luna's first task (Breakfast — daily recurring)
st_luna = luna_plan3.scheduled_tasks[0]
next_luna = scheduler.mark_task_complete(st_luna)
recur_note = (
    f"  → next occurrence queued for {next_luna.task_id.split('-', 2)[-1]}"
    if next_luna else "  (one-off, no recurrence)"
)
print(f"  [{st_luna.status.upper()}] {st_luna.task.title}{recur_note}")

print(f"\n  recurring_queue now has {len(scheduler.recurring_queue)} entry(ies):\n")
for due_date, queued_task in scheduler.recurring_queue:
    print(
        f"    Due {due_date}  |  [{queued_task.recurrence_interval}]  "
        f"{queued_task.title}  (id: {queued_task.task_id})"
    )

print("\n" + "=" * 60 + "\n")
