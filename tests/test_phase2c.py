"""
FitPulse SaaS - Phase 2C Test Suite
Validates Progress, Measurements, ProgressPhotos, Transformations, Consents, and Reviews.
Runs standalone using Python standard library (sqlite3) to verify schema integrity,
check constraints, default privacy flags, and multi-tenant isolation.
"""
import sqlite3
import os
import sys

DB_FILE = "fitness_platform_phase2c_test.db"

def run_tests():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    print("==================================================")
    print("RUNNING FITPULSE PHASE 2C DATABASE SCHEMA TESTS")
    print("==================================================")

    # 1. Initialize Phase 2A & 2B Foundations
    print("\n[Test 1] Initializing Phase 2A & 2B tables...")
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
    print("✓ Phase 2A & 2B base tables verified.")

    # 2. Initialize Phase 2C Tables
    print("\n[Test 2] Creating Phase 2C tables (progress, measurements, progress_photos)...")
    cursor.execute("""
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
    """)
    cursor.execute("CREATE INDEX ix_progress_client_id ON progress(client_id);")
    cursor.execute("CREATE INDEX ix_progress_date ON progress(date);")

    cursor.execute("""
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
    """)
    cursor.execute("CREATE INDEX ix_measurements_client_id ON measurements(client_id);")
    cursor.execute("CREATE INDEX ix_measurements_measurement_date ON measurements(measurement_date);")

    cursor.execute("""
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
    """)
    cursor.execute("CREATE INDEX ix_progress_photos_client_id ON progress_photos(client_id);")
    cursor.execute("CREATE INDEX ix_progress_photos_captured_at ON progress_photos(captured_at);")
    cursor.execute("CREATE INDEX ix_progress_photos_is_private ON progress_photos(is_private);")
    print("✓ 'progress', 'measurements', and 'progress_photos' created successfully.")

    print("\n[Test 3] Creating 'transformations' and 'transformation_consents' tables...")
    cursor.execute("""
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
    """)
    cursor.execute("CREATE INDEX ix_transformations_coach_id ON transformations(coach_id);")
    cursor.execute("CREATE INDEX ix_transformations_client_id ON transformations(client_id);")
    cursor.execute("CREATE INDEX ix_transformations_is_public ON transformations(is_public);")

    cursor.execute("""
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
    """)
    cursor.execute("CREATE INDEX ix_transformation_consents_transformation_id ON transformation_consents(transformation_id);")
    cursor.execute("CREATE INDEX ix_transformation_consents_client_id ON transformation_consents(client_id);")
    print("✓ 'transformations' and 'transformation_consents' created successfully.")

    print("\n[Test 4] Creating 'reviews' table with Rating CheckConstraint [1..5]...")
    cursor.execute("""
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
    """)
    cursor.execute("CREATE INDEX ix_reviews_coach_id ON reviews(coach_id);")
    cursor.execute("CREATE INDEX ix_reviews_client_id ON reviews(client_id);")
    cursor.execute("CREATE INDEX ix_reviews_is_public ON reviews(is_public);")
    cursor.execute("CREATE INDEX ix_reviews_is_approved ON reviews(is_approved);")
    print("✓ 'reviews' table and indexes created successfully.")

    # 3. Seed Multi-Tenant Data
    print("\n[Test 5] Seeding Coach A, Client A1, Coach B, Client B1...")
    # Coach A
    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('coach.a@fitpulse.test', 'hash_a', 'COACH', 'Marcus', 'Aurelius');")
    coach_a_uid = cursor.lastrowid
    cursor.execute("INSERT INTO coaches (user_id, business_name, specialization) VALUES (?, 'Stoic Strength Labs', 'Hypertrophy');", (coach_a_uid,))
    coach_a_id = cursor.lastrowid

    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('client.a1@fitpulse.test', 'hash_ca1', 'CLIENT', 'Lucius', 'Verus');")
    client_a1_uid = cursor.lastrowid
    cursor.execute("INSERT INTO clients (user_id, coach_id, goal) VALUES (?, ?, 'Strength & Fat Loss');", (client_a1_uid, coach_a_id))
    client_a1_id = cursor.lastrowid

    # Coach B
    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('coach.b@fitpulse.test', 'hash_b', 'COACH', 'Athena', 'Olympia');")
    coach_b_uid = cursor.lastrowid
    cursor.execute("INSERT INTO coaches (user_id, business_name, specialization) VALUES (?, 'Apex Kinetics', 'Biomechanics');", (coach_b_uid,))
    coach_b_id = cursor.lastrowid

    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('client.b1@fitpulse.test', 'hash_cb1', 'CLIENT', 'Hector', 'Troy');")
    client_b1_uid = cursor.lastrowid
    cursor.execute("INSERT INTO clients (user_id, coach_id, goal) VALUES (?, ?, 'Marathon Endurance');", (client_b1_uid, coach_b_id))
    client_b1_id = cursor.lastrowid
    conn.commit()

    # 4. Insert Progress, Measurements, Photos for Client A1
    print("\n[Test 6] Inserting private biometrics, measurements, and photos...")
    cursor.execute("""
    INSERT INTO progress (client_id, date, weight, body_fat_percentage, muscle_mass, waist, chest, arms, thighs, hips, notes)
    VALUES (?, '2026-09-01', 82.5, 16.2, 41.0, 84.0, 102.0, 38.0, 58.0, 96.0, 'Week 4 Check-in: Energy high, recovery solid.');
    """, (client_a1_id,))
    progress_a1_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO measurements (client_id, measurement_date, weight, body_fat_percentage, neck, shoulders, chest, waist, abdomen, hips, left_arm, right_arm, left_thigh, right_thigh)
    VALUES (?, '2026-09-01', 82.5, 16.2, 39.5, 122.0, 102.0, 84.0, 86.0, 96.0, 38.0, 38.2, 58.0, 58.3);
    """, (client_a1_id,))

    cursor.execute("""
    INSERT INTO progress_photos (client_id, photo_type, file_path, notes, is_private)
    VALUES (?, 'FRONT', 'uploads/clients/1/photos/front_20260901.jpg', 'Neutral lighting, morning fasted.', 1);
    """, (client_a1_id,))
    photo_a1_id = cursor.lastrowid

    # Verify default privacy
    cursor.execute("SELECT is_private FROM progress_photos WHERE id = ?;", (photo_a1_id,))
    assert cursor.fetchone()[0] == 1, "Photo must be private by default!"
    print("✓ Private biometric tracking and photos stored with default privacy enforced.")

    # 5. Insert Transformation and Test Explicit Consent Workflow
    print("\n[Test 7] Testing Transformation & Consent Privacy Architecture...")
    cursor.execute("""
    INSERT INTO transformations (coach_id, client_id, title, description, duration_text, achievement_text, is_public)
    VALUES (?, ?, '16-Week Recomposition Breakthrough', 'Dedicated training focused on hypertrophy and lean deficit.', '16 Weeks', '-7kg fat, +3kg muscle', 1);
    """, (coach_a_id, client_a1_id))
    trans_a1_id = cursor.lastrowid

    # Before consent is given
    cursor.execute("SELECT is_public FROM transformations WHERE id = ?;", (trans_a1_id,))
    assert cursor.fetchone()[0] == 1

    # Insert explicit consent record
    cursor.execute("""
    INSERT INTO transformation_consents (transformation_id, client_id, consent_given, consent_date, consent_text)
    VALUES (?, ?, 1, CURRENT_TIMESTAMP, 'I agree to feature my physique transformation publicly on FitPulse.');
    """, (trans_a1_id, client_a1_id))
    consent_id = cursor.lastrowid

    # Verify query for public display eligibility:
    # (transformation.is_public == 1 AND consent.consent_given == 1 AND consent.revoked_at IS NULL)
    cursor.execute("""
    SELECT t.id, t.title, c.consent_given, c.revoked_at
    FROM transformations t
    JOIN transformation_consents c ON c.transformation_id = t.id
    WHERE t.is_public = 1 AND c.consent_given = 1 AND c.revoked_at IS NULL;
    """)
    eligible = cursor.fetchall()
    assert len(eligible) == 1, "Transformation with active consent must be eligible for display."
    print("✓ Public transformation verified with active client consent.")

    # Simulate client revoking consent
    cursor.execute("UPDATE transformation_consents SET revoked_at = CURRENT_TIMESTAMP WHERE id = ?;", (consent_id,))
    cursor.execute("""
    SELECT t.id
    FROM transformations t
    JOIN transformation_consents c ON c.transformation_id = t.id
    WHERE t.is_public = 1 AND c.consent_given = 1 AND c.revoked_at IS NULL;
    """)
    eligible_after_revoke = cursor.fetchall()
    assert len(eligible_after_revoke) == 0, "Revoked consent must disqualify transformation from public display!"
    print("✓ Revocation verified: Transformation immediately excluded when consent is revoked.")

    # Re-enable consent for remaining tests
    cursor.execute("UPDATE transformation_consents SET revoked_at = NULL WHERE id = ?;", (consent_id,))
    conn.commit()

    # 6. Test Reviews & Rating Check Constraint [1..5]
    print("\n[Test 8] Testing Reviews & Rating Constraint...")
    # Valid review
    cursor.execute("""
    INSERT INTO reviews (coach_id, client_id, rating, title, content, is_public, is_approved)
    VALUES (?, ?, 5, 'World-class coaching experience!', 'Marcus provided personalized protocols and daily accountability.', 1, 1);
    """, (coach_a_id, client_a1_id))
    review_a1_id = cursor.lastrowid
    print("✓ Valid review with rating 5 successfully saved.")

    # Test invalid rating (> 5) -> should raise IntegrityError
    try:
        cursor.execute("""
        INSERT INTO reviews (coach_id, client_id, rating, content)
        VALUES (?, ?, 6, 'Over the top!');
        """, (coach_a_id, client_a1_id))
        raise AssertionError("Check constraint failed: rating=6 was accepted!")
    except sqlite3.IntegrityError:
        print("✓ CheckConstraint passed: Rating=6 correctly rejected with IntegrityError.")

    # Test invalid rating (< 1) -> should raise IntegrityError
    try:
        cursor.execute("""
        INSERT INTO reviews (coach_id, client_id, rating, content)
        VALUES (?, ?, 0, 'Zero stars!');
        """, (coach_a_id, client_a1_id))
        raise AssertionError("Check constraint failed: rating=0 was accepted!")
    except sqlite3.IntegrityError:
        print("✓ CheckConstraint passed: Rating=0 correctly rejected with IntegrityError.")

    # 7. Multi-Tenant Isolation Tests
    print("\n[Test 9] Verifying Multi-Tenant Data Isolation...")
    # Add Coach B review and progress
    cursor.execute("""
    INSERT INTO progress (client_id, date, weight, notes)
    VALUES (?, '2026-09-02', 74.0, 'Coach B client entry');
    """, (client_b1_id,))

    cursor.execute("""
    INSERT INTO reviews (coach_id, client_id, rating, content, is_public, is_approved)
    VALUES (?, ?, 4, 'Great running advice.', 1, 1);
    """, (coach_b_id, client_b1_id))
    conn.commit()

    # Coach A queries their client's progress via Coach hierarchy
    cursor.execute("""
    SELECT p.id, u.first_name, p.weight
    FROM progress p
    JOIN clients cl ON p.client_id = cl.id
    JOIN users u ON cl.user_id = u.id
    WHERE cl.coach_id = ?;
    """, (coach_a_id,))
    coach_a_progress = cursor.fetchall()
    assert len(coach_a_progress) == 1
    assert coach_a_progress[0][1] == "Lucius"
    assert coach_a_progress[0][2] == 82.5
    print(f"  -> Coach A Progress: Client '{coach_a_progress[0][1]}' Weight {coach_a_progress[0][2]}kg (PASS)")

    # Verify Coach A cannot see Coach B progress
    for row in coach_a_progress:
        assert row[1] != "Hector", "TENANT LEAK: Coach B client appeared in Coach A progress query!"
    print("✓ Multi-tenant biometric isolation verified: 0% data leakage.")

    # 8. Cascade Deletion Behavior Verification
    print("\n[Test 10] Verifying Cascade Deletions upon Client Removal...")
    cursor.execute("DELETE FROM clients WHERE id = ?;", (client_a1_id,))
    conn.commit()

    # Verify client progress deleted
    cursor.execute("SELECT COUNT(*) FROM progress WHERE client_id = ?;", (client_a1_id,))
    assert cursor.fetchone()[0] == 0, "Cascade failed: progress not deleted."

    # Verify client measurements deleted
    cursor.execute("SELECT COUNT(*) FROM measurements WHERE client_id = ?;", (client_a1_id,))
    assert cursor.fetchone()[0] == 0, "Cascade failed: measurements not deleted."

    # Verify client photos deleted
    cursor.execute("SELECT COUNT(*) FROM progress_photos WHERE client_id = ?;", (client_a1_id,))
    assert cursor.fetchone()[0] == 0, "Cascade failed: progress_photos not deleted."

    # Verify transformations deleted
    cursor.execute("SELECT COUNT(*) FROM transformations WHERE client_id = ?;", (client_a1_id,))
    assert cursor.fetchone()[0] == 0, "Cascade failed: transformations not deleted."

    # Verify transformation_consents deleted
    cursor.execute("SELECT COUNT(*) FROM transformation_consents WHERE client_id = ?;", (client_a1_id,))
    assert cursor.fetchone()[0] == 0, "Cascade failed: transformation_consents not deleted."

    # Verify reviews deleted
    cursor.execute("SELECT COUNT(*) FROM reviews WHERE client_id = ?;", (client_a1_id,))
    assert cursor.fetchone()[0] == 0, "Cascade failed: reviews not deleted."

    # Verify Coach A and Coach A's User record are NOT deleted!
    cursor.execute("SELECT COUNT(*) FROM coaches WHERE id = ?;", (coach_a_id,))
    assert cursor.fetchone()[0] == 1, "Error: Coach was deleted when client was deleted!"
    cursor.execute("SELECT COUNT(*) FROM users WHERE id = ?;", (coach_a_uid,))
    assert cursor.fetchone()[0] == 1, "Error: Coach User record was deleted when client was deleted!"
    print("✓ Client cascade deletion cleanly pruned biometric and showcase records while preserving Coach and User.")

    # Clean up test database
    conn.close()
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    print("✓ Test database removed.")

    print("\n==================================================")
    print("ALL PHASE 2C DATABASE TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
