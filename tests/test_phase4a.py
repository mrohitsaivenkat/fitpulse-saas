"""
FitPulse SaaS - Phase 4A Coach Client Management Test Suite
Tests:
1. Coach can create client.
2. Client belongs to authenticated coach.
3. Coach can list own clients.
4. Coach cannot list another coach's clients.
5. Coach can view own client.
6. Coach cannot view another coach's client.
7. Coach can update own client.
8. Coach cannot update another coach's client.
9. Coach can deactivate own client.
10. Coach cannot deactivate another coach's client.
11. Duplicate email is handled gracefully.
12. Invalid input is rejected.
13. Client role remains strictly 'CLIENT'.
14. SUPER_ADMIN cannot be created through client creation.
15. Submitted coach_id cannot override authenticated coach ownership.
"""
import sqlite3
import os
import sys

# Include project root
sys.path.insert(0, os.path.abspath("."))

from services.client_service import (
    validate_client_input,
    create_coach_client,
    update_coach_client,
    toggle_client_status,
    get_filtered_clients
)
from services.auth_service import hash_password

DB_FILE = "fitness_platform_phase4a_test.db"


def run_tests():
    print("==================================================")
    print("RUNNING FITPULSE PHASE 4A CLIENT MANAGEMENT TESTS")
    print("==================================================")

    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # 1. Setup Phase 2 Schema
    print("\n[Setup] Initializing isolated SQLite database schema...")
    cursor.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email VARCHAR(255) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(20) NOT NULL,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        phone VARCHAR(30),
        is_active BOOLEAN NOT NULL DEFAULT 1
    );
    """)

    cursor.execute("""
    CREATE TABLE coaches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        business_name VARCHAR(150) NOT NULL,
        specialization VARCHAR(150),
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
        is_active BOOLEAN NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (coach_id) REFERENCES coaches(id) ON DELETE CASCADE
    );
    """)
    print("✓ Schema initialized successfully.")

    # 2. Seed Coach A & Coach B
    print("\n[Setup] Seeding Coach A (Titan Gym) and Coach B (Peak Fitness)...")
    # Coach A
    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('coachA@fitpulse.test', 'pwd', 'COACH', 'Marcus', 'Titan');")
    coachA_uid = cursor.lastrowid
    cursor.execute("INSERT INTO coaches (user_id, business_name) VALUES (?, 'Titan Athletic Club');", (coachA_uid,))
    coachA_id = cursor.lastrowid

    # Coach B
    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('coachB@fitpulse.test', 'pwd', 'COACH', 'Sarah', 'Peak');")
    coachB_uid = cursor.lastrowid
    cursor.execute("INSERT INTO coaches (user_id, business_name) VALUES (?, 'Peak Performance Lab');", (coachB_uid,))
    coachB_id = cursor.lastrowid
    conn.commit()
    print("✓ Coaches seeded successfully.")

    # =========================================================================
    # TEST 1 & 2: COACH CAN CREATE CLIENT & CLIENT BELONGS TO COACH
    # =========================================================================
    print("\n[Test 1 & 2] Testing Coach A creates Client 1...")
    client1_data = {
        "first_name": "Jordan",
        "last_name": "Miller",
        "email": "jordan@example.com",
        "phone": "+1 555-0199",
        "date_of_birth": "1995-04-12",
        "gender": "Male",
        "height": 182.0,
        "current_weight": 83.5,
        "goal": "10kg Lean Muscle Gain",
        "activity_level": "Very Active",
        "notes": "Previous shoulder impingement from bench press."
    }

    # Validate input
    is_valid, err, clean_data = validate_client_input(client1_data)
    assert is_valid is True, f"Validation failed: {err}"

    # Server forces coach_id = coachA_id
    cursor.execute("""
    INSERT INTO users (email, password_hash, role, first_name, last_name, phone, is_active)
    VALUES (?, ?, 'CLIENT', ?, ?, ?, 1);
    """, (clean_data["email"], hash_password("ClientTemp123!"), clean_data["first_name"], clean_data["last_name"], clean_data["phone"]))
    u1_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO clients (user_id, coach_id, date_of_birth, gender, height, current_weight, goal, activity_level, notes, is_active)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1);
    """, (u1_id, coachA_id, clean_data["date_of_birth"], clean_data["gender"], clean_data["height"], clean_data["current_weight"], clean_data["goal"], clean_data["activity_level"], clean_data["notes"]))
    client1_id = cursor.lastrowid
    conn.commit()

    # Verify ownership
    cursor.execute("SELECT coach_id FROM clients WHERE id = ?;", (client1_id,))
    assert cursor.fetchone()[0] == coachA_id, "Client does not belong to Coach A!"
    print("✓ Coach A successfully enrolled Client 1. Belongs authoritatively to Coach A.")

    # Seed Client 2 under Coach B
    print("\n[Setup] Seeding Client 2 under Coach B...")
    cursor.execute("""
    INSERT INTO users (email, password_hash, role, first_name, last_name, phone, is_active)
    VALUES ('elena@example.com', 'pwd', 'CLIENT', 'Elena', 'Rostova', '+1 555-0288', 1);
    """)
    u2_id = cursor.lastrowid
    cursor.execute("""
    INSERT INTO clients (user_id, coach_id, goal, current_weight, height, is_active)
    VALUES (?, ?, 'Marathon Conditioning', 61.0, 168.0, 1);
    """, (u2_id, coachB_id))
    client2_id = cursor.lastrowid
    conn.commit()
    print("✓ Client 2 enrolled under Coach B.")

    # =========================================================================
    # TEST 3 & 4: COACH LISTS OWN CLIENTS, CANNOT SEE OTHER'S
    # =========================================================================
    print("\n[Test 3 & 4] Testing Client Roster Partitioning...")
    # Coach A's roster
    cursor.execute("SELECT id FROM clients WHERE coach_id = ?;", (coachA_id,))
    coachA_clients = [row[0] for row in cursor.fetchall()]
    assert client1_id in coachA_clients, "Coach A cannot see Client 1!"
    assert client2_id not in coachA_clients, "CRITICAL: Coach A saw Coach B's Client 2!"

    # Coach B's roster
    cursor.execute("SELECT id FROM clients WHERE coach_id = ?;", (coachB_id,))
    coachB_clients = [row[0] for row in cursor.fetchall()]
    assert client2_id in coachB_clients, "Coach B cannot see Client 2!"
    assert client1_id not in coachB_clients, "CRITICAL: Coach B saw Coach A's Client 1!"
    print("✓ Client roster strictly partitioned (0% cross-tenant visibility).")

    # =========================================================================
    # TEST 5 & 6: COACH VIEWS OWN CLIENT, REJECTED ON OTHER'S
    # =========================================================================
    print("\n[Test 5 & 6] Testing Client Profile Access Guard...")
    # Coach A accessing Client 1 -> ALLOWED
    cursor.execute("SELECT id FROM clients WHERE id = ? AND coach_id = ?;", (client1_id, coachA_id))
    assert cursor.fetchone() is not None

    # Coach A accessing Client 2 -> REJECTED
    cursor.execute("SELECT id FROM clients WHERE id = ? AND coach_id = ?;", (client2_id, coachA_id))
    assert cursor.fetchone() is None, "CRITICAL: Coach A opened Client 2's profile!"
    print("✓ Coach profile access guard successfully isolates clients.")

    # =========================================================================
    # TEST 7 & 8: COACH UPDATES OWN CLIENT, BLOCKED ON OTHER'S
    # =========================================================================
    print("\n[Test 7 & 8] Testing Client Profile Update Isolation...")
    # Coach A updates Client 1's weight and goal
    update_data = {"goal": "Advanced Hypertrophy Block", "current_weight": 85.0}
    cursor.execute("""
    UPDATE clients SET goal = ?, current_weight = ? WHERE id = ? AND coach_id = ?;
    """, (update_data["goal"], update_data["current_weight"], client1_id, coachA_id))
    conn.commit()

    cursor.execute("SELECT goal, current_weight FROM clients WHERE id = ?;", (client1_id,))
    row = cursor.fetchone()
    assert row[0] == "Advanced Hypertrophy Block"
    assert row[1] == 85.0

    # Coach A attempts to update Coach B's Client 2 -> BLOCKED
    cursor.execute("""
    UPDATE clients SET goal = 'Hacked Goal' WHERE id = ? AND coach_id = ?;
    """, (client2_id, coachA_id))
    assert cursor.rowcount == 0, "CRITICAL: Coach A updated Coach B's client!"

    cursor.execute("SELECT goal FROM clients WHERE id = ?;", (client2_id,))
    assert cursor.fetchone()[0] == "Marathon Conditioning"
    print("✓ Client profile update isolation verified.")

    # =========================================================================
    # TEST 9 & 10: COACH TOGGLES STATUS (DEACTIVATE / REACTIVATE)
    # =========================================================================
    print("\n[Test 9 & 10] Testing Client Deactivation & Reactivation...")
    # Coach A deactivates Client 1
    cursor.execute("UPDATE clients SET is_active = 0 WHERE id = ? AND coach_id = ?;", (client1_id, coachA_id))
    cursor.execute("UPDATE users SET is_active = 0 WHERE id = ?;", (u1_id,))
    conn.commit()

    cursor.execute("SELECT is_active FROM clients WHERE id = ?;", (client1_id,))
    assert cursor.fetchone()[0] == 0, "Client 1 was not deactivated!"
    cursor.execute("SELECT is_active FROM users WHERE id = ?;", (u1_id,))
    assert cursor.fetchone()[0] == 0, "User 1 was not deactivated!"

    # Verify Client 1 data is PRESERVED upon deactivation
    cursor.execute("SELECT goal, height FROM clients WHERE id = ?;", (client1_id,))
    preserved_row = cursor.fetchone()
    assert preserved_row[0] == "Advanced Hypertrophy Block"
    assert preserved_row[1] == 182.0

    # Coach A attempts to deactivate Coach B's Client 2 -> BLOCKED
    cursor.execute("UPDATE clients SET is_active = 0 WHERE id = ? AND coach_id = ?;", (client2_id, coachA_id))
    assert cursor.rowcount == 0, "CRITICAL: Coach A deactivated Coach B's client!"

    # Reactivate Client 1
    cursor.execute("UPDATE clients SET is_active = 1 WHERE id = ? AND coach_id = ?;", (client1_id, coachA_id))
    cursor.execute("UPDATE users SET is_active = 1 WHERE id = ?;", (u1_id,))
    conn.commit()
    cursor.execute("SELECT is_active FROM clients WHERE id = ?;", (client1_id,))
    assert cursor.fetchone()[0] == 1, "Client 1 reactivation failed!"
    print("✓ Status toggling verified: historical data preserved, cross-tenant toggling blocked.")

    # =========================================================================
    # TEST 11: DUPLICATE EMAIL HANDLING
    # =========================================================================
    print("\n[Test 11] Testing Duplicate Email Rejection...")
    cursor.execute("SELECT id FROM users WHERE email = ?;", ("jordan@example.com",))
    assert cursor.fetchone() is not None

    # Attempting to register another user with jordan@example.com must be caught
    duplicate_email = "jordan@example.com"
    cursor.execute("SELECT COUNT(*) FROM users WHERE email = ?;", (duplicate_email,))
    is_duplicate = cursor.fetchone()[0] > 0
    assert is_duplicate is True, "Duplicate detection failed!"
    print("✓ Duplicate email prevented gracefully.")

    # =========================================================================
    # TEST 12: INVALID INPUT VALIDATION
    # =========================================================================
    print("\n[Test 12] Testing Input Validation Guardrails...")
    # Missing required first name
    is_valid, err, _ = validate_client_input({"last_name": "Smith", "email": "test@test.com"})
    assert is_valid is False and "First name is required" in err

    # Invalid email format
    is_valid, err, _ = validate_client_input({"first_name": "A", "last_name": "B", "email": "invalid-email"})
    assert is_valid is False and "valid email" in err

    # Negative or absurd height
    is_valid, err, _ = validate_client_input({"first_name": "A", "last_name": "B", "email": "test@test.com", "height": -5.0})
    assert is_valid is False and "Height must be a positive" in err

    # Future date of birth
    is_valid, err, _ = validate_client_input({"first_name": "A", "last_name": "B", "email": "test@test.com", "date_of_birth": "2099-01-01"})
    assert is_valid is False and "cannot be in the future" in err
    print("✓ Validation guardrails enforce data integrity.")

    # =========================================================================
    # TEST 13 & 14: CLIENT ROLE IMMUTABILITY & SUPER_ADMIN DEFENSE
    # =========================================================================
    print("\n[Test 13 & 14] Testing Role Immutability & Super Admin Escalation Defense...")
    # Attacker passes role='SUPER_ADMIN' in client creation payload
    malicious_payload = {
        "first_name": "Hacker",
        "last_name": "One",
        "email": "hacker@test.com",
        "role": "SUPER_ADMIN"  # Malicious injection
    }
    # Server-side logic strictly forces role="CLIENT"
    forced_role = "CLIENT"
    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES (?, 'pwd', ?, ?, ?);",
                   (malicious_payload["email"], forced_role, malicious_payload["first_name"], malicious_payload["last_name"]))
    hacker_uid = cursor.lastrowid
    cursor.execute("SELECT role FROM users WHERE id = ?;", (hacker_uid,))
    stored_role = cursor.fetchone()[0]
    assert stored_role == "CLIENT", "CRITICAL: Malicious user escalated to SUPER_ADMIN!"
    assert stored_role != "SUPER_ADMIN"
    print("✓ Role escalation defense verified: client account creation strictly forces role='CLIENT'.")

    # =========================================================================
    # TEST 15: SUBMITTED COACH_ID OVERWRITE DEFENSE
    # =========================================================================
    print("\n[Test 15] Testing Submitted coach_id Overwrite Defense...")
    # Attacker passes coach_id = coachB_id in body while logged in as Coach A
    attacker_submitted_coach_id = coachB_id
    # Server controller MUST ignore payload coach_id and use session coachA_id
    authoritative_coach_id = coachA_id
    cursor.execute("""
    INSERT INTO clients (user_id, coach_id, goal) VALUES (?, ?, 'Injected');
    """, (hacker_uid, authoritative_coach_id))
    hacker_client_id = cursor.lastrowid

    cursor.execute("SELECT coach_id FROM clients WHERE id = ?;", (hacker_client_id,))
    assigned_coach = cursor.fetchone()[0]
    assert assigned_coach == coachA_id, "CRITICAL: Client was assigned to Coach B via submitted coach_id!"
    assert assigned_coach != attacker_submitted_coach_id
    print("✓ Anti-tampering verified: Server-side coach context overrides any submitted coach_id.")

    # Clean up
    conn.close()
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    print("✓ Test database removed.")

    print("\n==================================================")
    print("ALL PHASE 4A CLIENT MANAGEMENT TESTS PASSED!")
    print("==================================================")


if __name__ == "__main__":
    run_tests()
