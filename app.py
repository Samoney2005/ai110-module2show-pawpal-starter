import streamlit as st
from pawpal_system import Owner, Pet, CareTask, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None

if "task_counter" not in st.session_state:
    st.session_state.task_counter = 0

# ---------------------------------------------------------------------------
# Owner + Pet setup
# ---------------------------------------------------------------------------

st.subheader("Owner & Pet")

with st.form("owner_pet_form"):
    owner_name = st.text_input("Owner name", value="Jordan")
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    age = st.number_input("Pet age (years)", min_value=0, max_value=30, value=3)
    weight = st.number_input("Pet weight (kg)", min_value=0.1, max_value=100.0, value=8.0)
    submitted = st.form_submit_button("Save Owner & Pet")

if submitted:
    owner = Owner(name=owner_name, email="", phone="")
    pet = Pet(name=pet_name, species=species, age=int(age), weight_kg=float(weight))
    owner.add_pet(pet)                      # Owner.add_pet() wires Pet into Owner
    st.session_state.owner = owner
    st.session_state.task_counter = 0
    st.success(f"Owner **{owner_name}** and pet **{pet_name}** saved!")

if st.session_state.owner:
    owner = st.session_state.owner
    pet = owner.pets[0]

    # -----------------------------------------------------------------------
    # Add a task
    # -----------------------------------------------------------------------

    st.divider()
    st.subheader("Add a Care Task")

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    preferred_time = st.text_input("Preferred time (HH:MM)", value="09:00")

    if st.button("Add Task"):
        st.session_state.task_counter += 1
        task_id = f"task_{st.session_state.task_counter}"
        new_task = CareTask(
            task_id=task_id,
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            preferred_time=preferred_time,
        )
        pet.add_task(new_task)              # Pet.add_task() stores the CareTask object
        st.success(f"Task **{task_title}** added to {pet.name}!")

    # Show current tasks on the pet
    if pet.tasks:
        st.write(f"Tasks for **{pet.name}**:")
        st.table([
            {
                "Title": t.title,
                "Duration (min)": t.duration_minutes,
                "Priority": t.priority,
                "Preferred Time": t.preferred_time,
            }
            for t in pet.get_tasks_by_priority()   # sorted high → low
        ])
    else:
        st.info("No tasks yet. Add one above.")

    # -----------------------------------------------------------------------
    # Generate schedule
    # -----------------------------------------------------------------------

    st.divider()
    st.subheader("Build Schedule")

    if st.button("Generate Schedule"):
        if not pet.tasks:
            st.warning("Add at least one task before generating a schedule.")
        else:
            scheduler = Scheduler(scheduling_strategy="priority", available_minutes_per_day=480)
            plan = scheduler.generate_daily_plan(pet=pet, owner=owner)
            st.success("Schedule generated!")
            st.text(plan.get_summary())

else:
    st.info("Fill in the Owner & Pet form above and click **Save** to get started.")
