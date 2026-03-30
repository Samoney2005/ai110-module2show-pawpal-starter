import streamlit as st
from pawpal_system import Owner, Pet, CareTask, ScheduledTask, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None

if "task_counter" not in st.session_state:
    st.session_state.task_counter = 0

if "plan" not in st.session_state:
    st.session_state.plan = None

if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

# ---------------------------------------------------------------------------
# Owner + Pet setup
# ---------------------------------------------------------------------------

st.subheader("Owner & Pet")

with st.form("owner_pet_form"):
    owner_name = st.text_input("Owner name", value="Jordan")
    pet_name   = st.text_input("Pet name",   value="Mochi")
    species    = st.selectbox("Species", ["dog", "cat", "other"])
    age        = st.number_input("Pet age (years)",  min_value=0,   max_value=30,    value=3)
    weight     = st.number_input("Pet weight (kg)",  min_value=0.1, max_value=100.0, value=8.0)
    submitted  = st.form_submit_button("Save Owner & Pet")

if submitted:
    owner = Owner(name=owner_name, email="", phone="")
    pet   = Pet(name=pet_name, species=species, age=int(age), weight_kg=float(weight))
    owner.add_pet(pet)
    st.session_state.owner       = owner
    st.session_state.task_counter = 0
    st.session_state.plan        = None
    st.session_state.scheduler   = None
    st.success(f"Owner **{owner_name}** and pet **{pet_name}** saved!")

# ---------------------------------------------------------------------------
# Everything below requires a saved owner/pet
# ---------------------------------------------------------------------------

if not st.session_state.owner:
    st.info("Fill in the Owner & Pet form above and click **Save** to get started.")
    st.stop()

owner = st.session_state.owner
pet   = owner.pets[0]

# ---------------------------------------------------------------------------
# Add a care task
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Add a Care Task")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

col4, col5 = st.columns(2)
with col4:
    preferred_time = st.text_input("Preferred time (HH:MM)", value="09:00")
with col5:
    is_recurring = st.checkbox("Recurring task?")
    recurrence_interval = ""
    if is_recurring:
        recurrence_interval = st.selectbox("Repeat every", ["daily", "weekly"])

if st.button("Add Task"):
    st.session_state.task_counter += 1
    task_id  = f"task_{st.session_state.task_counter}"
    new_task = CareTask(
        task_id=task_id,
        title=task_title,
        duration_minutes=int(duration),
        priority=priority,
        preferred_time=preferred_time,
        is_recurring=is_recurring,
        recurrence_interval=recurrence_interval,
    )
    pet.add_task(new_task)
    # Invalidate any existing plan since tasks changed
    st.session_state.plan = None
    st.success(f"Task **{task_title}** added to {pet.name}!")

# ---------------------------------------------------------------------------
# Current task list — sorted by time, with live conflict check
# ---------------------------------------------------------------------------

st.divider()
st.subheader(f"Tasks for {pet.name}")

if not pet.tasks:
    st.info("No tasks yet. Add one above.")
else:
    scheduler_preview = Scheduler()

    # Sort by time so the table reflects chronological order
    sorted_tasks = scheduler_preview.sort_by_time(pet.tasks)

    st.caption("Sorted chronologically by preferred time")
    st.table([
        {
            "Time":          t.preferred_time or "—",
            "Title":         t.title,
            "Duration (min)": t.duration_minutes,
            "Priority":      t.priority.capitalize(),
            "Recurring":     f"{t.recurrence_interval}" if t.is_recurring else "No",
        }
        for t in sorted_tasks
    ])

    # ── Edit an existing task ────────────────────────────────────────────
    with st.expander("✏️ Edit an existing task"):
        task_map = {t.title: t for t in sorted_tasks}
        edit_choice = st.selectbox("Select task to edit", list(task_map.keys()), key="edit_select")
        task_to_edit = task_map[edit_choice]

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            new_title = st.text_input("Title", value=task_to_edit.title, key="edit_title")
        with col_b:
            new_duration = st.number_input(
                "Duration (minutes)", min_value=1, max_value=240,
                value=task_to_edit.duration_minutes, key="edit_duration"
            )
        with col_c:
            priority_opts = ["low", "medium", "high"]
            new_priority = st.selectbox(
                "Priority", priority_opts,
                index=priority_opts.index(task_to_edit.priority), key="edit_priority"
            )

        col_d, col_e = st.columns(2)
        with col_d:
            new_time = st.text_input(
                "Preferred time (HH:MM)", value=task_to_edit.preferred_time, key="edit_time"
            )
        with col_e:
            new_recurring = st.checkbox(
                "Recurring?", value=task_to_edit.is_recurring, key="edit_recurring"
            )
            new_interval = ""
            if new_recurring:
                interval_opts = ["daily", "weekly"]
                default_idx = interval_opts.index(task_to_edit.recurrence_interval) \
                    if task_to_edit.recurrence_interval in interval_opts else 0
                new_interval = st.selectbox(
                    "Repeat every", interval_opts, index=default_idx, key="edit_interval"
                )

        if st.button("Save Changes"):
            pet.update_task(
                task_id=task_to_edit.task_id,
                title=new_title,
                duration_minutes=int(new_duration),
                priority=new_priority,
                preferred_time=new_time,
                is_recurring=new_recurring,
                recurrence_interval=new_interval,
            )
            st.session_state.plan = None
            st.success(f"Task **{new_title}** updated!")
            st.rerun()

    # Live conflict warnings — shown immediately after the table
    conflicts = scheduler_preview.check_conflicts(pet.tasks)
    if conflicts:
        st.markdown("**Scheduling conflicts detected:**")
        for msg in conflicts:
            # Strip the leading "WARNING: " prefix for a cleaner Streamlit display
            clean = msg.replace("WARNING: ", "")
            st.warning(
                f"⚠️ **Time conflict** — {clean}\n\n"
                "_Tip: adjust the start time or duration of one of these tasks to resolve the overlap._"
            )
    else:
        st.success("No time conflicts — your schedule looks good!")

# ---------------------------------------------------------------------------
# Generate daily schedule
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Build Today's Schedule")

if st.button("Generate Schedule", disabled=not bool(pet.tasks)):
    scheduler = Scheduler(scheduling_strategy="time", available_minutes_per_day=480)
    plan      = scheduler.generate_daily_plan(pet=pet, owner=owner)
    st.session_state.plan      = plan
    st.session_state.scheduler = scheduler

# Display the plan if one exists
if st.session_state.plan:
    plan      = st.session_state.plan
    scheduler = st.session_state.scheduler

    st.success(f"Schedule generated for **{pet.name}** — {plan.date}")

    # ── Scheduled tasks ──────────────────────────────────────────────────
    if plan.scheduled_tasks:
        st.markdown("#### Scheduled Tasks")

        # Run conflict check on the generated plan's tasks for display
        plan_tasks     = [sched.task for sched in plan.scheduled_tasks]
        plan_conflicts = scheduler.check_conflicts(plan_tasks)

        if plan_conflicts:
            st.markdown("**Conflicts in this plan:**")
            for msg in plan_conflicts:
                clean = msg.replace("WARNING: ", "")
                st.warning(
                    f"⚠️ **Time conflict** — {clean}\n\n"
                    "_Consider rescheduling one of these tasks._"
                )

        rows = []
        for sched in plan.scheduled_tasks:
            status_icon = {"pending": "🔵", "complete": "✅", "skipped": "⏭️"}.get(
                sched.status, ""
            )
            rows.append({
                "Status":         f"{status_icon} {sched.status.capitalize()}",
                "Time Slot":      sched.time_slot,
                "Task":           sched.task.title,
                "Duration (min)": sched.task.duration_minutes,
                "Priority":       sched.task.priority.capitalize(),
                "Recurring":      sched.task.recurrence_interval if sched.task.is_recurring else "—",
            })
        st.table(rows)

        st.caption(f"Total scheduled time: **{plan.total_duration_minutes} min**")

    # ── Mark complete ─────────────────────────────────────────────────────
    pending = [sched for sched in plan.scheduled_tasks if sched.status == "pending"]
    if pending:
        st.markdown("#### Mark a Task Complete")
        task_options = {sched.task.title: sched for sched in pending}
        chosen_title = st.selectbox("Select task to mark complete", list(task_options.keys()))
        if st.button("Mark Complete"):
            chosen_st = task_options[chosen_title]
            next_task = scheduler.mark_task_complete(chosen_st)
            if next_task:
                due_date, queued = scheduler.recurring_queue[-1]
                st.success(
                    f"**{chosen_title}** marked complete! "
                    f"Next occurrence automatically scheduled for **{due_date}**."
                )
            else:
                st.success(f"**{chosen_title}** marked complete!")
            # Rerun to refresh the table
            st.rerun()

    # ── Skipped tasks ─────────────────────────────────────────────────────
    if plan.skipped_tasks:
        st.markdown("#### Skipped Tasks")
        st.info(
            "The following tasks didn't fit within today's 480-minute budget "
            "and were skipped:"
        )
        for t in plan.skipped_tasks:
            st.markdown(f"- **{t.title}** ({t.duration_minutes} min, {t.priority} priority)")
