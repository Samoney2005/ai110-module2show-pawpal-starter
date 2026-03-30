# PawPal+ Class Diagram

```mermaid
---
id: 81249dc6-8a6d-4251-9ef8-0c58e4d86038
---
classDiagram
    class Owner {
        +String name
        +String email
        +String phone
        +List~Pet~ pets
        +String preferred_walk_time
        +add_pet(pet: Pet)
        +remove_pet(pet_name: String)
        +get_all_tasks() List~CareTask~
    }

    class Pet {
        +String name
        +String species
        +int age
        +float weight_kg
        +String breed
        +List~String~ health_conditions
        +List~CareTask~ tasks
        +add_task(task: CareTask)
        +remove_task(task_id: String)
        +get_tasks_by_priority() List~CareTask~
    }

    class CareTask {
        +String task_id
        +String title
        +int duration_minutes
        +String priority
        +String preferred_time
        +bool is_recurring
        +String recurrence_interval
        +String notes
        +get_priority_score() int
        +is_due_today() bool
    }

    class FeedingTask {
        +float food_amount_cups
        +String food_type
        +String meal_time
        +bool has_medication_mixed_in
        +execute()
    }

    class WalkTask {
        +float distance_km
        +String route_preference
        +String energy_level_required
        +bool needs_leash
        +execute()
    }

    class MedicationTask {
        +String medication_name
        +float dosage_mg
        +String administration_route
        +String prescribing_vet
        +bool requires_food
        +execute()
    }

    class AppointmentTask {
        +String vet_name
        +String clinic_name
        +String appointment_type
        +String location
        +bool is_confirmed
        +execute()
    }

    class Scheduler {
        +List~CareTask~ task_queue
        +String scheduling_strategy
        +int available_minutes_per_day
        +generate_daily_plan(pet: Pet) DayPlan
        +prioritize_tasks(tasks: List~CareTask~) List~CareTask~
        +check_conflicts(tasks: List~CareTask~) List~String~
        +optimize_order(tasks: List~CareTask~) List~CareTask~
    }

    class DayPlan {
        +String date
        +Pet pet
        +List~ScheduledTask~ scheduled_tasks
        +List~CareTask~ skipped_tasks
        +int total_duration_minutes
        +add_task(task: CareTask, time_slot: String)
        +remove_task(task_id: String)
        +get_summary() String
        +export_to_dict() dict
    }

    class ScheduledTask {
        +CareTask task
        +String time_slot
        +String status
        +String skip_reason
        +mark_complete()
        +mark_skipped(reason: String)
    }

    Owner "1" --> "1..*" Pet : owns
    Pet "1" --> "0..*" CareTask : has
    CareTask <|-- FeedingTask : extends
    CareTask <|-- WalkTask : extends
    CareTask <|-- MedicationTask : extends
    CareTask <|-- AppointmentTask : extends
    Scheduler --> DayPlan : generates
    Scheduler --> "0..*" CareTask : prioritizes
    DayPlan "1" --> "0..*" ScheduledTask : contains
    ScheduledTask --> CareTask : wraps
```
