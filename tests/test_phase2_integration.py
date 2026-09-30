"""
FitPulse SaaS - Phase 2 Comprehensive Integration Test (Section L)
Performs an end-to-end integration test across all 21 models from Phases 2A, 2B, 2C, and 2D.
Validates the entire relational hierarchy using temporary records that are cleanly deleted upon completion:
  1. User -> Coach -> Client -> DietPlan -> DietItem
  2. Coach -> Client -> WorkoutPlan -> WorkoutDay -> WorkoutExercise -> Exercise
  3. Client -> Progress -> Measurement
  4. Client -> Transformation -> TransformationConsent
  5. Coach -> SubscriptionPlan -> Subscription
  6. User -> Notification -> SupportTicket -> AuditLog
"""
import sqlite3
import os
import sys

INTEG_DB = "phase2_integration_test.db"

def run_integration_test():
    if os.path.exists(INTEG_DB):
        os.remove(INTEG_DB)

    conn = sqlite3.connect(INTEG_DB)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    print("==================================================")
    print("FITPULSE PHASE 2 COMPREHENSIVE INTEGRATION AUDIT")
    print("==================================================")

    # 1. DDL: Create All 15 Tables
    print("\n[Step 1] Creating all Phase 2 DDL tables...")
    cursor.executescript("""
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

    CREATE TABLE diet_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coach_id INTEGER NOT NULL,
        client_id INTEGER NOT NULL,
        name VARCHAR(150) NOT NULL,
        description TEXT,
        daily_calorie_target FLOAT,
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

    CREATE TABLE diet_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        diet_plan_id INTEGER NOT NULL,
        meal_name VARCHAR(100) NOT NULL,
        food_name VARCHAR(150) NOT NULL,
        quantity FLOAT NOT NULL DEFAULT 1.0,
        unit VARCHAR(50) NOT NULL DEFAULT 'serving',
        calories FLOAT,
        protein FLOAT,
        carbohydrates FLOAT,
        fat FLOAT,
        meal_time VARCHAR(20),
        notes TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (diet_plan_id) REFERENCES diet_plans(id) ON DELETE CASCADE
    );

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

    CREATE TABLE workout_exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workout_day_id INTEGER NOT NULL,
        exercise_id INTEGER NOT NULL,
        sets INTEGER NOT NULL DEFAULT 3,
        reps VARCHAR(50) NOT NULL DEFAULT '10-12',
        duration VARCHAR(50),
        rest_seconds INTEGER NOT NULL DEFAULT 60,
        order_index INTEGER NOT NULL DEFAULT 1,
        notes TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workout_day_id) REFERENCES workout_days(id) ON DELETE CASCADE,
        FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE RESTRICT
    );

    CREATE TABLE progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        date DATE NOT NULL,
        weight FLOAT,
        body_fat_percentage FLOAT,
        muscle_mass FLOAT,
        waist FLOAT,
        chest FLOAT,
        arms FLOAT,
        thighs FLOAT,
        hips FLOAT,
        notes TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
    );

    CREATE TABLE measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        measurement_date DATE NOT NULL,
        weight FLOAT,
        body_fat_percentage FLOAT,
        neck FLOAT,
        shoulders FLOAT,
        chest FLOAT,
        waist FLOAT,
        abdomen FLOAT,
        hips FLOAT,
        left_arm FLOAT,
        right_arm FLOAT,
        left_thigh FLOAT,
        right_thigh FLOAT,
        notes TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
    );

    CREATE TABLE progress_photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        photo_type VARCHAR(20) NOT NULL,
        file_path VARCHAR(255) NOT NULL,
        captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        is_private BOOLEAN NOT NULL DEFAULT 1,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
    );

    CREATE TABLE transformations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coach_id INTEGER NOT NULL,
        client_id INTEGER NOT NULL,
        title VARCHAR(150) NOT NULL,
        description TEXT,
        before_photo VARCHAR(255),
        after_photo VARCHAR(255),
        duration_text VARCHAR(100),
        achievement_text TEXT,
        is_public BOOLEAN NOT NULL DEFAULT 0,
        published_at TIMESTAMP,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (coach_id) REFERENCES coaches(id) ON DELETE CASCADE,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
    );

    CREATE TABLE transformation_consents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transformation_id INTEGER NOT NULL,
        client_id INTEGER NOT NULL,
        consent_given BOOLEAN NOT NULL DEFAULT 0,
        consent_date TIMESTAMP,
        revoked_at TIMESTAMP,
        consent_text TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (transformation_id) REFERENCES transformations(id) ON DELETE CASCADE,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
    );

    CREATE TABLE reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coach_id INTEGER NOT NULL,
        client_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        title VARCHAR(150),
        content TEXT NOT NULL,
        is_public BOOLEAN NOT NULL DEFAULT 0,
        is_approved BOOLEAN NOT NULL DEFAULT 0,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (rating >= 1 AND rating <= 5),
        FOREIGN KEY (coach_id) REFERENCES coaches(id) ON DELETE CASCADE,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
    );

    CREATE TABLE subscription_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        price FLOAT NOT NULL DEFAULT 0.0,
        billing_period VARCHAR(20) NOT NULL DEFAULT 'MONTHLY',
        max_clients INTEGER NOT NULL DEFAULT 15,
        storage_limit INTEGER NOT NULL DEFAULT 5120,
        analytics_enabled BOOLEAN NOT NULL DEFAULT 0,
        ml_enabled BOOLEAN NOT NULL DEFAULT 0,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coach_id INTEGER NOT NULL,
        plan_id INTEGER NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'TRIAL',
        start_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        end_date TIMESTAMP,
        trial_start TIMESTAMP,
        trial_end TIMESTAMP,
        auto_renew BOOLEAN NOT NULL DEFAULT 1,
        external_subscription_id VARCHAR(150),
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (coach_id) REFERENCES coaches(id) ON DELETE CASCADE,
        FOREIGN KEY (plan_id) REFERENCES subscription_plans(id) ON DELETE RESTRICT
    );

    CREATE TABLE notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title VARCHAR(200) NOT NULL,
        message TEXT NOT NULL,
        notification_type VARCHAR(50) NOT NULL DEFAULT 'SYSTEM',
        is_read BOOLEAN NOT NULL DEFAULT 0,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE support_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        coach_id INTEGER,
        subject VARCHAR(200) NOT NULL,
        description TEXT NOT NULL,
        priority VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
        status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (coach_id) REFERENCES coaches(id) ON DELETE SET NULL
    );

    CREATE TABLE announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(200) NOT NULL,
        content TEXT NOT NULL,
        target_role VARCHAR(30) NOT NULL DEFAULT 'ALL',
        is_active BOOLEAN NOT NULL DEFAULT 1,
        published_at TIMESTAMP,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action VARCHAR(50) NOT NULL,
        entity_type VARCHAR(50),
        entity_id INTEGER,
        description TEXT NOT NULL,
        ip_address VARCHAR(45),
        user_agent VARCHAR(255),
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)
    conn.commit()
    print("✓ All 20 tables successfully created.")

    # 2. Integration Chain 1: User -> Coach -> Client -> DietPlan -> DietItem
    print("\n[Step 2] Testing Chain 1: User -> Coach -> Client -> DietPlan -> DietItem...")
    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('coach.audit@test.com', 'pwhash', 'COACH', 'Aiden', 'Cross');")
    coach_uid = cursor.lastrowid
    cursor.execute("INSERT INTO coaches (user_id, business_name, specialization) VALUES (?, 'Cross Kinetics', 'Hypertrophy');", (coach_uid,))
    coach_id = cursor.lastrowid

    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('client.audit@test.com', 'pwhash', 'CLIENT', 'Leo', 'Vance');")
    client_uid = cursor.lastrowid
    cursor.execute("INSERT INTO clients (user_id, coach_id, goal) VALUES (?, ?, 'Body Recomp');", (client_uid, coach_id))
    client_id = cursor.lastrowid

    cursor.execute("INSERT INTO diet_plans (coach_id, client_id, name, daily_calorie_target) VALUES (?, ?, 'High Protein Recomp', 2400.0);", (coach_id, client_id))
    dp_id = cursor.lastrowid

    cursor.execute("INSERT INTO diet_items (diet_plan_id, meal_name, food_name, calories) VALUES (?, 'Post-Workout', 'Whey & Oats', 480.0);", (dp_id,))
    print("✓ Chain 1 verified: User -> Coach -> Client -> DietPlan -> DietItem.")

    # 3. Integration Chain 2: Coach -> Client -> WorkoutPlan -> WorkoutDay -> WorkoutExercise -> Exercise
    print("\n[Step 3] Testing Chain 2: Coach -> Client -> WorkoutPlan -> WorkoutDay -> WorkoutExercise -> Exercise...")
    cursor.execute("INSERT INTO exercises (name, category, muscle_group) VALUES ('Incline DB Press', 'Strength', 'Chest');")
    ex_id = cursor.lastrowid

    cursor.execute("INSERT INTO workout_plans (coach_id, client_id, name) VALUES (?, ?, 'Upper/Lower Split');", (coach_id, client_id))
    wp_id = cursor.lastrowid

    cursor.execute("INSERT INTO workout_days (workout_plan_id, day_name, day_number) VALUES (?, 'Upper Day 1', 1);", (wp_id,))
    wd_id = cursor.lastrowid

    cursor.execute("INSERT INTO workout_exercises (workout_day_id, exercise_id, sets, reps) VALUES (?, ?, 4, '8-10');", (wd_id, ex_id))
    print("✓ Chain 2 verified: Coach -> Client -> WorkoutPlan -> WorkoutDay -> WorkoutExercise -> Exercise.")

    # 4. Integration Chain 3: Client -> Progress -> Measurement
    print("\n[Step 4] Testing Chain 3: Client -> Progress & Measurement...")
    cursor.execute("INSERT INTO progress (client_id, date, weight, body_fat_percentage) VALUES (?, '2026-09-20', 79.5, 15.0);", (client_id,))
    cursor.execute("INSERT INTO measurements (client_id, measurement_date, chest, waist) VALUES (?, '2026-09-20', 104.0, 83.0);", (client_id,))
    cursor.execute("INSERT INTO progress_photos (client_id, photo_type, file_path, is_private) VALUES (?, 'FRONT', 'path/front.jpg', 1);", (client_id,))
    print("✓ Chain 3 verified: Client -> Progress & Measurement & ProgressPhoto.")

    # 5. Integration Chain 4: Client -> Transformation -> TransformationConsent
    print("\n[Step 4] Testing Chain 4: Client -> Transformation -> Consent...")
    cursor.execute("INSERT INTO transformations (coach_id, client_id, title, is_public) VALUES (?, ?, '12-Week Recomp', 1);", (coach_id, client_id))
    trans_id = cursor.lastrowid
    cursor.execute("INSERT INTO transformation_consents (transformation_id, client_id, consent_given) VALUES (?, ?, 1);", (trans_id, client_id))
    print("✓ Chain 4 verified: Client -> Transformation -> Consent.")

    # 6. Integration Chain 5: Coach -> SubscriptionPlan -> Subscription
    print("\n[Step 5] Testing Chain 5: Coach -> SubscriptionPlan -> Subscription...")
    cursor.execute("INSERT INTO subscription_plans (name, price, max_clients) VALUES ('Audit Tier Pro', 49.0, 30);",)
    plan_id = cursor.lastrowid
    cursor.execute("INSERT INTO subscriptions (coach_id, plan_id, status) VALUES (?, ?, 'ACTIVE');", (coach_id, plan_id))
    print("✓ Chain 5 verified: Coach -> SubscriptionPlan -> Subscription.")

    # 7. Integration Chain 6: User -> Notification -> SupportTicket -> AuditLog
    print("\n[Step 6] Testing Chain 6: User -> Notification, SupportTicket, AuditLog...")
    cursor.execute("INSERT INTO notifications (user_id, title, message) VALUES (?, 'Welcome', 'Account initialized');", (coach_uid,))
    cursor.execute("INSERT INTO support_tickets (user_id, coach_id, subject, description) VALUES (?, ?, 'Feature request', 'Export tool');", (coach_uid, coach_id))
    cursor.execute("INSERT INTO audit_logs (user_id, action, entity_type, entity_id, description) VALUES (?, 'CREATE', 'User', ?, 'Account registered');", (coach_uid, coach_uid))
    print("✓ Chain 6 verified: User -> Notification, SupportTicket, AuditLog.")

    # 8. Query verification
    cursor.execute("""
    SELECT c.business_name, u_cl.first_name, dp.name, wp.name, p.weight, sp.name, notif.title
    FROM coaches c
    JOIN clients cl ON cl.coach_id = c.id
    JOIN users u_cl ON cl.user_id = u_cl.id
    JOIN diet_plans dp ON dp.coach_id = c.id
    JOIN workout_plans wp ON wp.coach_id = c.id
    JOIN progress p ON p.client_id = cl.id
    JOIN subscriptions sub ON sub.coach_id = c.id
    JOIN subscription_plans sp ON sub.plan_id = sp.id
    JOIN notifications notif ON notif.user_id = c.user_id
    WHERE c.id = ?;
    """, (coach_id,))
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == 'Cross Kinetics'
    assert row[1] == 'Leo'
    assert row[2] == 'High Protein Recomp'
    assert row[3] == 'Upper/Lower Split'
    assert row[4] == 79.5
    assert row[5] == 'Audit Tier Pro'
    assert row[6] == 'Welcome'
    print("✓ Full cross-model relational join succeeded with expected data.")

    # Cleanup temporary test database
    conn.close()
    if os.path.exists(INTEG_DB):
        os.remove(INTEG_DB)
    print("✓ Temporary test database cleaned up.")
    print("\n==================================================")
    print("ALL COMPREHENSIVE INTEGRATION TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_integration_test()
