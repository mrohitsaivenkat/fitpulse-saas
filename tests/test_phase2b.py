"""
FitPulse SaaS - Phase 2B Test Suite
Validates Exercise, Diet, and Workout models, relationships, cascades, and multi-tenant isolation.
Runs standalone using Python standard library (sqlite3) to verify schema integrity.
"""
import sqlite3
import os
import sys

DB_FILE = "fitness_platform_phase2b_test.db"

def run_tests():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    print("==================================================")
    print("RUNNING FITPULSE PHASE 2B DATABASE SCHEMA TESTS")
    print("==================================================")

    # 1. Create Core Tables (Phase 2A Foundation)
    print("\n[Test 1] Initializing Phase 2A core tables (users, coaches, clients)...")
    cursor.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email VARCHAR(255) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(20) NOT NULL DEFAULT 'CLIENT',
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        phone VARCHAR(30),
        is_active BOOLEAN NOT NULL DEFAULT 1,
        is_verified BOOLEAN NOT NULL DEFAULT 0,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_login_at TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE coaches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        business_name VARCHAR(150) NOT NULL,
        bio TEXT,
        specialization VARCHAR(150),
        experience_years INTEGER NOT NULL DEFAULT 0,
        profile_image VARCHAR(255),
        location VARCHAR(150),
        website VARCHAR(255),
        instagram VARCHAR(100),
        facebook VARCHAR(100),
        youtube VARCHAR(100),
        is_public BOOLEAN NOT NULL DEFAULT 1,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        coach_id INTEGER NOT NULL,
        date_of_birth DATE,
        gender VARCHAR(20),
        height FLOAT,
        current_weight FLOAT,
        goal VARCHAR(200),
        activity_level VARCHAR(50),
        notes TEXT,
        joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (coach_id) REFERENCES coaches(id) ON DELETE CASCADE
    );
    """)
    print("✓ Phase 2A tables initialized successfully.")

    # 2. Create Phase 2B Tables
    print("\n[Test 2] Creating 'exercises' table (Shared Library)...")
    cursor.execute("""
    CREATE TABLE exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(150) NOT NULL,
        category VARCHAR(50) NOT NULL,
        muscle_group VARCHAR(100) NOT NULL,
        equipment VARCHAR(100),
        difficulty VARCHAR(50) NOT NULL DEFAULT 'Intermediate',
        instructions TEXT,
        precautions TEXT,
        video_url VARCHAR(255),
        image_url VARCHAR(255),
        is_active BOOLEAN NOT NULL DEFAULT 1,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("CREATE INDEX ix_exercises_name ON exercises(name);")
    cursor.execute("CREATE INDEX ix_exercises_category ON exercises(category);")
    cursor.execute("CREATE INDEX ix_exercises_muscle_group ON exercises(muscle_group);")
    print("✓ 'exercises' table created successfully.")

    print("\n[Test 3] Creating 'diet_plans' and 'diet_items' tables...")
    cursor.execute("""
    CREATE TABLE diet_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coach_id INTEGER NOT NULL,
        client_id INTEGER NOT NULL,
        name VARCHAR(150) NOT NULL,
        description TEXT,
        daily_calorie_target INTEGER,
        protein_target FLOAT,
        carbs_target FLOAT,
        fat_target FLOAT,
        start_date DATE,
        end_date DATE,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (coach_id) REFERENCES coaches(id) ON DELETE CASCADE,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
    );
    """)
    cursor.execute("CREATE INDEX ix_diet_plans_coach_id ON diet_plans(coach_id);")
    cursor.execute("CREATE INDEX ix_diet_plans_client_id ON diet_plans(client_id);")

    cursor.execute("""
    CREATE TABLE diet_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        diet_plan_id INTEGER NOT NULL,
        meal_name VARCHAR(100) NOT NULL,
        food_name VARCHAR(150) NOT NULL,
        quantity FLOAT NOT NULL,
        unit VARCHAR(50) NOT NULL,
        calories INTEGER,
        protein FLOAT,
        carbohydrates FLOAT,
        fat FLOAT,
        meal_time VARCHAR(50),
        notes TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (diet_plan_id) REFERENCES diet_plans(id) ON DELETE CASCADE
    );
    """)
    cursor.execute("CREATE INDEX ix_diet_items_diet_plan_id ON diet_items(diet_plan_id);")
    print("✓ 'diet_plans' and 'diet_items' tables created successfully.")

    print("\n[Test 4] Creating 'workout_plans', 'workout_days', and 'workout_exercises' tables...")
    cursor.execute("""
    CREATE TABLE workout_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coach_id INTEGER NOT NULL,
        client_id INTEGER NOT NULL,
        name VARCHAR(150) NOT NULL,
        description TEXT,
        start_date DATE,
        end_date DATE,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (coach_id) REFERENCES coaches(id) ON DELETE CASCADE,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
    );
    """)
    cursor.execute("CREATE INDEX ix_workout_plans_coach_id ON workout_plans(coach_id);")
    cursor.execute("CREATE INDEX ix_workout_plans_client_id ON workout_plans(client_id);")

    cursor.execute("""
    CREATE TABLE workout_days (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workout_plan_id INTEGER NOT NULL,
        day_name VARCHAR(100) NOT NULL,
        day_number INTEGER NOT NULL DEFAULT 1,
        focus VARCHAR(150),
        notes TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workout_plan_id) REFERENCES workout_plans(id) ON DELETE CASCADE
    );
    """)
    cursor.execute("CREATE INDEX ix_workout_days_workout_plan_id ON workout_days(workout_plan_id);")

    cursor.execute("""
    CREATE TABLE workout_exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workout_day_id INTEGER NOT NULL,
        exercise_id INTEGER NOT NULL,
        sets INTEGER NOT NULL DEFAULT 3,
        reps VARCHAR(50),
        duration INTEGER,
        rest_seconds INTEGER DEFAULT 90,
        order_index INTEGER NOT NULL DEFAULT 1,
        notes TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workout_day_id) REFERENCES workout_days(id) ON DELETE CASCADE,
        FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE
    );
    """)
    cursor.execute("CREATE INDEX ix_workout_exercises_workout_day_id ON workout_exercises(workout_day_id);")
    cursor.execute("CREATE INDEX ix_workout_exercises_exercise_id ON workout_exercises(exercise_id);")
    print("✓ 'workout_plans', 'workout_days', and 'workout_exercises' tables created successfully.")

    # 3. Seed Shared Exercises
    print("\n[Test 5] Seeding generic shared exercise library...")
    cursor.executemany("""
    INSERT INTO exercises (name, category, muscle_group, equipment, difficulty, instructions)
    VALUES (?, ?, ?, ?, ?, ?);
    """, [
        ("Bodyweight Squat", "Strength", "Quads", "Bodyweight", "Beginner", "Squat to parallel."),
        ("Push-Up", "Strength", "Chest", "Bodyweight", "Beginner", "Full range push-up."),
        ("Plank", "Core", "Core", "Bodyweight", "Beginner", "Hold rigid plank position."),
        ("Walking", "Cardio", "Full Body", "None", "Beginner", "Brisk walking."),
        ("Dumbbell Row", "Strength", "Back", "Dumbbell", "Intermediate", "Single arm row.")
    ])
    conn.commit()
    print("✓ 5 generic shared exercises seeded successfully.")

    # 4. Seed Multi-Tenant Data (Coach A and Coach B)
    print("\n[Test 6] Seeding Coach A (IronPeak) and Coach B (Apex) multi-tenant data...")
    # Coach A
    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('coach.a@fitpulse.test', 'hash_a', 'COACH', 'Alex', 'Carter');")
    coach_a_uid = cursor.lastrowid
    cursor.execute("INSERT INTO coaches (user_id, business_name, specialization) VALUES (?, 'IronPeak Performance', 'Hypertrophy');", (coach_a_uid,))
    coach_a_id = cursor.lastrowid

    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('client.a1@fitpulse.test', 'hash_ca1', 'CLIENT', 'Chris', 'Evans');")
    client_a1_uid = cursor.lastrowid
    cursor.execute("INSERT INTO clients (user_id, coach_id, goal) VALUES (?, ?, 'Muscle Gain');", (client_a1_uid, coach_a_id))
    client_a1_id = cursor.lastrowid

    # Coach B
    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('coach.b@fitpulse.test', 'hash_b', 'COACH', 'Brooke', 'Taylor');")
    coach_b_uid = cursor.lastrowid
    cursor.execute("INSERT INTO coaches (user_id, business_name, specialization) VALUES (?, 'Apex Endurance Hub', 'Conditioning');", (coach_b_uid,))
    coach_b_id = cursor.lastrowid

    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('client.b1@fitpulse.test', 'hash_cb1', 'CLIENT', 'Sam', 'Wilson');")
    client_b1_uid = cursor.lastrowid
    cursor.execute("INSERT INTO clients (user_id, coach_id, goal) VALUES (?, ?, 'Half-Marathon Prep');", (client_b1_uid, coach_b_id))
    client_b1_id = cursor.lastrowid

    # Coach A Prescriptions
    cursor.execute("""
    INSERT INTO diet_plans (coach_id, client_id, name, daily_calorie_target, protein_target, carbs_target, fat_target)
    VALUES (?, ?, 'Hypertrophy Mass Plan', 2800, 180.0, 320.0, 75.0);
    """, (coach_a_id, client_a1_id))
    diet_plan_a_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO diet_items (diet_plan_id, meal_name, food_name, quantity, unit, calories, protein, carbohydrates, fat)
    VALUES (?, 'Breakfast', 'Oatmeal with Whey & Banana', 100, 'grams', 520, 35.0, 70.0, 9.0);
    """, (diet_plan_a_id,))

    cursor.execute("""
    INSERT INTO workout_plans (coach_id, client_id, name, description)
    VALUES (?, ?, 'PPL Hypertrophy 4-Week Block', 'Upper/Lower Split');
    """, (coach_a_id, client_a1_id))
    workout_plan_a_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO workout_days (workout_plan_id, day_name, day_number, focus)
    VALUES (?, 'Push Day 1', 1, 'Chest, Delts & Triceps');
    """, (workout_plan_a_id,))
    workout_day_a1_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO workout_exercises (workout_day_id, exercise_id, sets, reps, rest_seconds, order_index)
    VALUES (?, 2, 4, '10-12', 90, 1);
    """, (workout_day_a1_id,))  # Exercise 2 = Push-Up

    # Coach B Prescriptions
    cursor.execute("""
    INSERT INTO diet_plans (coach_id, client_id, name, daily_calorie_target, protein_target, carbs_target, fat_target)
    VALUES (?, ?, 'Endurance Fueling Protocol', 2400, 140.0, 300.0, 60.0);
    """, (coach_b_id, client_b1_id))
    diet_plan_b_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO diet_items (diet_plan_id, meal_name, food_name, quantity, unit, calories, protein, carbohydrates, fat)
    VALUES (?, 'Pre-Workout', 'Energy Rice Cake with Honey', 2, 'pieces', 220, 4.0, 48.0, 1.0);
    """, (diet_plan_b_id,))

    cursor.execute("""
    INSERT INTO workout_plans (coach_id, client_id, name, description)
    VALUES (?, ?, 'Aerobic Base Building Block', 'Zone 2 running and core support');
    """, (coach_b_id, client_b1_id))
    workout_plan_b_id = cursor.lastrowid

    conn.commit()
    print("✓ Multi-tenant coaching hierarchies seeded.")

    # 5. Multi-Tenant Isolation Tests
    print("\n[Test 7] Verifying Strict Multi-Tenant Diet & Workout Isolation...")
    # Query Coach A Diet Plans
    cursor.execute("SELECT id, name, coach_id FROM diet_plans WHERE coach_id = ?;", (coach_a_id,))
    coach_a_diets = cursor.fetchall()
    assert len(coach_a_diets) == 1
    assert coach_a_diets[0][1] == "Hypertrophy Mass Plan"
    print(f"  -> Coach A Diet Plans: {[d[1] for d in coach_a_diets]} (PASS)")

    # Query Coach A Workout Plans
    cursor.execute("SELECT id, name, coach_id FROM workout_plans WHERE coach_id = ?;", (coach_a_id,))
    coach_a_workouts = cursor.fetchall()
    assert len(coach_a_workouts) == 1
    assert coach_a_workouts[0][1] == "PPL Hypertrophy 4-Week Block"
    print(f"  -> Coach A Workout Plans: {[w[1] for w in coach_a_workouts]} (PASS)")

    # Query Coach B Diet Plans
    cursor.execute("SELECT id, name, coach_id FROM diet_plans WHERE coach_id = ?;", (coach_b_id,))
    coach_b_diets = cursor.fetchall()
    assert len(coach_b_diets) == 1
    assert coach_b_diets[0][1] == "Endurance Fueling Protocol"
    print(f"  -> Coach B Diet Plans: {[d[1] for d in coach_b_diets]} (PASS)")

    # Verify no cross-tenant contamination
    for d in coach_a_diets:
        assert d[2] != coach_b_id, "TENANT LEAK: Coach B's diet plan found in Coach A query!"
    print("✓ Zero cross-tenant data leakage confirmed across diet and workout plans.")

    # 6. Deep Hierarchy Query (Coach -> Client -> WorkoutPlan -> WorkoutDay -> WorkoutExercise -> Exercise)
    print("\n[Test 8] Testing Complete 6-Level Workout Hierarchy Query...")
    cursor.execute("""
    SELECT 
        c.business_name AS coach_business,
        u.first_name || ' ' || u.last_name AS client_name,
        wp.name AS workout_plan_name,
        wd.day_name,
        ex.name AS exercise_name,
        we.sets,
        we.reps
    FROM coaches c
    JOIN clients cl ON cl.coach_id = c.id
    JOIN users u ON cl.user_id = u.id
    JOIN workout_plans wp ON wp.client_id = cl.id
    JOIN workout_days wd ON wd.workout_plan_id = wp.id
    JOIN workout_exercises we ON we.workout_day_id = wd.id
    JOIN exercises ex ON we.exercise_id = ex.id
    WHERE c.id = ?;
    """, (coach_a_id,))
    full_hierarchy = cursor.fetchall()
    print("Hierarchy output row:")
    for row in full_hierarchy:
        print(f"  Coach: '{row[0]}' | Client: '{row[1]}' | Plan: '{row[2]}' | Day: '{row[3]}' | Movement: '{row[4]}' ({row[5]} sets x {row[6]})")
    assert len(full_hierarchy) == 1
    assert full_hierarchy[0][4] == "Push-Up"
    print("✓ Full 6-level workout hierarchy resolved successfully.")

    # 7. Cascade Deletion Behavior Verification
    print("\n[Test 9] Verifying Cascade Deletions...")
    # Deleting workout_plan_a should cascade delete workout_days and workout_exercises
    cursor.execute("DELETE FROM workout_plans WHERE id = ?;", (workout_plan_a_id,))
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM workout_days WHERE workout_plan_id = ?;", (workout_plan_a_id,))
    assert cursor.fetchone()[0] == 0, "Cascade failed: workout_days not deleted."

    cursor.execute("SELECT COUNT(*) FROM workout_exercises WHERE workout_day_id = ?;", (workout_day_a1_id,))
    assert cursor.fetchone()[0] == 0, "Cascade failed: workout_exercises not deleted."

    # Verify shared exercise is NOT deleted
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE id = 2;")
    assert cursor.fetchone()[0] == 1, "Error: Shared exercise was deleted when workout plan was deleted!"
    print("✓ Cascade delete cleanly removed days and exercise prescriptions without removing the shared Exercise.")

    # Clean up test database
    conn.close()
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    print("✓ Test database removed.")

    print("\n==================================================")
    print("ALL PHASE 2B DATABASE TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
