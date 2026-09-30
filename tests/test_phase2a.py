"""
FitPulse SaaS - Phase 2A Test Suite
Validates database schema creation, constraints, relationships, and multi-tenant isolation.
Runs standalone using Python's standard library (sqlite3) to verify schema integrity.
"""
import sqlite3
import os
import sys

DB_FILE = "fitness_platform_test.db"

def run_tests():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    print("==================================================")
    print("RUNNING FITPULSE PHASE 2A DATABASE SCHEMA TESTS")
    print("==================================================")

    # 1. Create Tables
    print("\n[Test 1] Creating 'users' table...")
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
    cursor.execute("CREATE UNIQUE INDEX ix_users_email ON users(email);")
    cursor.execute("CREATE INDEX ix_users_role ON users(role);")
    print("✓ 'users' table and indexes created successfully.")

    print("\n[Test 2] Creating 'coaches' table (Tenant entity)...")
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
    cursor.execute("CREATE UNIQUE INDEX ix_coaches_user_id ON coaches(user_id);")
    cursor.execute("CREATE INDEX ix_coaches_is_public ON coaches(is_public);")
    print("✓ 'coaches' table and indexes created successfully.")

    print("\n[Test 3] Creating 'clients' table (Tenant-scoped member)...")
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
    cursor.execute("CREATE UNIQUE INDEX ix_clients_user_id ON clients(user_id);")
    cursor.execute("CREATE INDEX ix_clients_coach_id ON clients(coach_id);")
    cursor.execute("CREATE INDEX ix_clients_is_active ON clients(is_active);")
    print("✓ 'clients' table and indexes created successfully.")

    # 2. Insert Test Records
    print("\n[Test 4] Seeding test users (2 Coaches, 3 Clients)...")
    # Coach 1 User
    cursor.execute("""
    INSERT INTO users (email, password_hash, role, first_name, last_name)
    VALUES ('coach.david@fitpulse.test', 'pbkdf2:sha256:test_hash_1', 'COACH', 'David', 'Miller');
    """)
    coach1_user_id = cursor.lastrowid

    # Coach 1 Profile
    cursor.execute("""
    INSERT INTO coaches (user_id, business_name, specialization, experience_years, location)
    VALUES (?, 'IronPeak Fitness', 'Hypertrophy & Strength', 8, 'Seattle, WA');
    """, (coach1_user_id,))
    coach1_id = cursor.lastrowid

    # Coach 2 User
    cursor.execute("""
    INSERT INTO users (email, password_hash, role, first_name, last_name)
    VALUES ('coach.sarah@fitpulse.test', 'pbkdf2:sha256:test_hash_2', 'COACH', 'Sarah', 'Jenkins');
    """)
    coach2_user_id = cursor.lastrowid

    # Coach 2 Profile
    cursor.execute("""
    INSERT INTO coaches (user_id, business_name, specialization, experience_years, location)
    VALUES (?, 'Apex Strength Studio', 'Powerlifting & Biomechanics', 10, 'Austin, TX');
    """, (coach2_user_id,))
    coach2_id = cursor.lastrowid

    # Client A1 (belongs to Coach 1)
    cursor.execute("""
    INSERT INTO users (email, password_hash, role, first_name, last_name)
    VALUES ('marcus.t@client.test', 'pbkdf2:sha256:test_hash_c1', 'CLIENT', 'Marcus', 'Turner');
    """)
    client_a1_uid = cursor.lastrowid
    cursor.execute("""
    INSERT INTO clients (user_id, coach_id, goal, current_weight, height)
    VALUES (?, ?, 'Lean Bulk', 83.5, 182.0);
    """, (client_a1_uid, coach1_id))

    # Client A2 (belongs to Coach 1)
    cursor.execute("""
    INSERT INTO users (email, password_hash, role, first_name, last_name)
    VALUES ('elena.r@client.test', 'pbkdf2:sha256:test_hash_c2', 'CLIENT', 'Elena', 'Rostova');
    """)
    client_a2_uid = cursor.lastrowid
    cursor.execute("""
    INSERT INTO clients (user_id, coach_id, goal, current_weight, height)
    VALUES (?, ?, 'Fat Loss & Conditioning', 62.0, 168.0);
    """, (client_a2_uid, coach1_id))

    # Client B1 (belongs to Coach 2)
    cursor.execute("""
    INSERT INTO users (email, password_hash, role, first_name, last_name)
    VALUES ('jordan.k@client.test', 'pbkdf2:sha256:test_hash_c3', 'CLIENT', 'Jordan', 'Kemp');
    """)
    client_b1_uid = cursor.lastrowid
    cursor.execute("""
    INSERT INTO clients (user_id, coach_id, goal, current_weight, height)
    VALUES (?, ?, 'Powerlifting Meet Prep', 95.0, 185.0);
    """, (client_b1_uid, coach2_id))

    conn.commit()
    print("✓ Successfully created Coach David (IronPeak), Coach Sarah (Apex), and their respective clients.")

    # 3. Multi-Tenant Isolation Verification
    print("\n[Test 5] Verifying Multi-Tenant Isolation...")
    cursor.execute("""
    SELECT c.id, u.first_name, u.last_name, c.goal, ch.business_name
    FROM clients c
    JOIN users u ON c.user_id = u.id
    JOIN coaches ch ON c.coach_id = ch.id
    WHERE c.coach_id = ?
    """, (coach1_id,))
    coach1_clients = cursor.fetchall()

    print(f"Coach 1 (IronPeak) Clients Query Count: {len(coach1_clients)}")
    for row in coach1_clients:
        print(f"  -> Client ID: {row[0]}, Name: {row[1]} {row[2]}, Goal: '{row[3]}', Tenant: '{row[4]}'")

    assert len(coach1_clients) == 2, f"Expected 2 clients for Coach 1, got {len(coach1_clients)}"
    client_names_1 = [f"{r[1]} {r[2]}" for r in coach1_clients]
    assert "Marcus Turner" in client_names_1
    assert "Elena Rostova" in client_names_1
    assert "Jordan Kemp" not in client_names_1, "TENANT LEAK: Jordan Kemp (Coach 2 client) appeared in Coach 1 query!"

    cursor.execute("""
    SELECT c.id, u.first_name, u.last_name, c.goal, ch.business_name
    FROM clients c
    JOIN users u ON c.user_id = u.id
    JOIN coaches ch ON c.coach_id = ch.id
    WHERE c.coach_id = ?
    """, (coach2_id,))
    coach2_clients = cursor.fetchall()

    print(f"Coach 2 (Apex) Clients Query Count: {len(coach2_clients)}")
    for row in coach2_clients:
        print(f"  -> Client ID: {row[0]}, Name: {row[1]} {row[2]}, Goal: '{row[3]}', Tenant: '{row[4]}'")

    assert len(coach2_clients) == 1, f"Expected 1 client for Coach 2, got {len(coach2_clients)}"
    assert coach2_clients[0][1] == "Jordan"
    print("✓ Multi-tenant isolation verified: Coach A only sees Coach A's clients; Coach B only sees Coach B's clients.")

    # 4. Foreign Key & Cascade Constraint Verification
    print("\n[Test 6] Verifying Cascade Delete Constraints...")
    # Delete Client A1 User -> should cascade and delete from clients table
    cursor.execute("DELETE FROM users WHERE id = ?;", (client_a1_uid,))
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM clients WHERE user_id = ?;", (client_a1_uid,))
    client_count = cursor.fetchone()[0]
    assert client_count == 0, "Cascade failed: Client record was not deleted when User was deleted!"
    print("✓ User deletion cleanly cascaded to Client record.")

    # 5. Clean up test database
    conn.close()
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    print("✓ Test database cleaned up.")

    print("\n==================================================")
    print("ALL PHASE 2A DATABASE TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
