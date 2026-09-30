"""
FitPulse SaaS - Initial Shared Exercise Library Seed Data
Standard, non-proprietary movement references for the shared exercise database.
Note: Contains ONLY shared exercise library records. No mock users, coaches, or plans.
"""

SHARED_EXERCISES_SEED = [
    {
        "name": "Bodyweight Squat",
        "category": "Strength",
        "muscle_group": "Quads",
        "equipment": "Bodyweight",
        "difficulty": "Beginner",
        "instructions": "Stand with feet shoulder-width apart. Descend by bending knees and hips, keeping torso upright, until thighs are parallel to ground. Drive through heels to stand.",
        "precautions": "Keep knees aligned with toes. Do not let heels lift off the ground.",
        "video_url": None,
        "image_url": None,
        "is_active": True,
    },
    {
        "name": "Push-Up",
        "category": "Strength",
        "muscle_group": "Chest",
        "equipment": "Bodyweight",
        "difficulty": "Beginner",
        "instructions": "Place hands shoulder-width apart in high plank position. Lower body until chest is an inch above floor, elbows at 45 degrees. Press back up.",
        "precautions": "Maintain neutral spine; do not let lower back sag or hips pike upwards.",
        "video_url": None,
        "image_url": None,
        "is_active": True,
    },
    {
        "name": "Plank",
        "category": "Core",
        "muscle_group": "Core",
        "equipment": "Bodyweight",
        "difficulty": "Beginner",
        "instructions": "Rest on forearms and balls of feet. Maintain straight line from shoulders to ankles, contracting core and glutes continuously.",
        "precautions": "Avoid arching lower back. Breathe rhythmically throughout the hold.",
        "video_url": None,
        "image_url": None,
        "is_active": True,
    },
    {
        "name": "Walking",
        "category": "Cardio",
        "muscle_group": "Full Body",
        "equipment": "None",
        "difficulty": "Beginner",
        "instructions": "Brisk steady-state walking at a conversational pace. Aim for upright posture and natural arm swing.",
        "precautions": "Wear supportive athletic footwear appropriate for the walking surface.",
        "video_url": None,
        "image_url": None,
        "is_active": True,
    },
    {
        "name": "Dumbbell Row",
        "category": "Strength",
        "muscle_group": "Back",
        "equipment": "Dumbbell",
        "difficulty": "Intermediate",
        "instructions": "Hinge at hips with flat back, supporting non-working hand on bench. Pull dumbbell toward hip pocket, retracting shoulder blade at top.",
        "precautions": "Avoid rounding lumbar spine or rotating torso excessively during pull.",
        "video_url": None,
        "image_url": None,
        "is_active": True,
    },
    {
        "name": "Romanian Deadlift",
        "category": "Strength",
        "muscle_group": "Hamstrings",
        "equipment": "Barbell",
        "difficulty": "Intermediate",
        "instructions": "Hold barbell with overhand grip at thighs. Push hips backward with soft knee bend, lowering bar along shins until hamstring stretch is felt. Drive hips forward to lockout.",
        "precautions": "Maintain strict neutral spine. Do not round upper or lower back.",
        "video_url": None,
        "image_url": None,
        "is_active": True,
    },
]


def seed_exercises(db_session, ExerciseModel):
    """
    Idempotent seeding helper: inserts generic library exercises if not already present.
    """
    added_count = 0
    for item in SHARED_EXERCISES_SEED:
        existing = db_session.query(ExerciseModel).filter_by(name=item["name"]).first()
        if not existing:
            ex = ExerciseModel(**item)
            db_session.add(ex)
            added_count += 1
    if added_count > 0:
        db_session.commit()
    return added_count
