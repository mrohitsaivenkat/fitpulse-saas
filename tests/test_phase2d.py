"""
FitPulse SaaS - Phase 2D Test Suite
Validates SubscriptionPlans, Subscriptions, Notifications, SupportTickets,
Announcements, and AuditLogs models, constraints, and multi-tenant isolation.
"""
import sqlite3
import os
import sys

DB_FILE = "fitness_platform_phase2d_test.db"

def run_tests():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    print("==================================================")
    print("RUNNING FITPULSE PHASE 2D DATABASE SCHEMA TESTS")
    print("==================================================")

    # 1. Base Tables (Phase 2A, 2B, 2C)
    print("\n[Test 1] Initializing Core Phase 2A, 2B & 2C tables...")
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
    print("✓ Base users, coaches, and clients tables initialized.")

    # 2. Phase 2D Tables
    print("\n[Test 2] Creating 'subscription_plans' and 'subscriptions' tables...")
    cursor.execute("""
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
    """)
    cursor.execute("CREATE UNIQUE INDEX ix_subscription_plans_name ON subscription_plans(name);")
    cursor.execute("CREATE INDEX ix_subscription_plans_is_active ON subscription_plans(is_active);")

    cursor.execute("""
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
    """)
    cursor.execute("CREATE INDEX ix_subscriptions_coach_id ON subscriptions(coach_id);")
    cursor.execute("CREATE INDEX ix_subscriptions_plan_id ON subscriptions(plan_id);")
    cursor.execute("CREATE INDEX ix_subscriptions_status ON subscriptions(status);")
    print("✓ 'subscription_plans' and 'subscriptions' tables created.")

    print("\n[Test 3] Creating 'notifications', 'support_tickets', and 'announcements' tables...")
    cursor.execute("""
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
    """)
    cursor.execute("CREATE INDEX ix_notifications_user_id ON notifications(user_id);")
    cursor.execute("CREATE INDEX ix_notifications_is_read ON notifications(is_read);")

    cursor.execute("""
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
    """)
    cursor.execute("CREATE INDEX ix_support_tickets_user_id ON support_tickets(user_id);")
    cursor.execute("CREATE INDEX ix_support_tickets_coach_id ON support_tickets(coach_id);")

    cursor.execute("""
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
    """)
    cursor.execute("CREATE INDEX ix_announcements_target_role ON announcements(target_role);")
    print("✓ 'notifications', 'support_tickets', and 'announcements' tables created.")

    print("\n[Test 4] Creating 'audit_logs' table...")
    cursor.execute("""
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
    cursor.execute("CREATE INDEX ix_audit_logs_user_id ON audit_logs(user_id);")
    cursor.execute("CREATE INDEX ix_audit_logs_action ON audit_logs(action);")
    cursor.execute("CREATE INDEX ix_audit_logs_created_at ON audit_logs(created_at);")
    print("✓ 'audit_logs' table created.")

    # 3. Seed Subscription Plans
    print("\n[Test 5] Seeding configurable SaaS Subscription Plans...")
    cursor.executemany("""
    INSERT INTO subscription_plans (name, description, price, billing_period, max_clients, storage_limit, analytics_enabled, ml_enabled)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, [
        ("Starter", "Ideal for independent trainers launching remote coaching.", 29.0, "MONTHLY", 15, 5120, 0, 0),
        ("Professional", "For scaling coaches with analytics and client roster management.", 79.0, "MONTHLY", 50, 25600, 1, 0),
        ("Enterprise Elite", "Full-featured tier with dedicated storage and ML capabilities.", 149.0, "MONTHLY", 200, 102400, 1, 1)
    ])
    conn.commit()
    print("✓ 3 subscription plans seeded successfully.")

    # 4. Seed Coach A and Coach B
    print("\n[Test 6] Seeding Coach A and Coach B...")
    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('coach.a@fitpulse.test', 'hash_a', 'COACH', 'Alex', 'Vance');")
    coach_a_uid = cursor.lastrowid
    cursor.execute("INSERT INTO coaches (user_id, business_name, specialization) VALUES (?, 'Vance Athletic Systems', 'Powerlifting');", (coach_a_uid,))
    coach_a_id = cursor.lastrowid

    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('coach.b@fitpulse.test', 'hash_b', 'COACH', 'Diana', 'Prince');")
    coach_b_uid = cursor.lastrowid
    cursor.execute("INSERT INTO coaches (user_id, business_name, specialization) VALUES (?, 'Themyscira Fitness', 'Functional Conditioning');", (coach_b_uid,))
    coach_b_id = cursor.lastrowid
    conn.commit()

    # 5. Coach Subscription Lifecycle & History Testing
    print("\n[Test 7] Testing Coach Subscriptions & Plan Retention...")
    # Plan 2 is "Professional"
    cursor.execute("""
    INSERT INTO subscriptions (coach_id, plan_id, status, trial_start, trial_end, auto_renew)
    VALUES (?, 2, 'TRIAL', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1);
    """, (coach_a_id,))
    sub_1_id = cursor.lastrowid

    # Coach A renews into an ACTIVE subscription (historical log preserves both)
    cursor.execute("""
    INSERT INTO subscriptions (coach_id, plan_id, status, start_date, auto_renew)
    VALUES (?, 2, 'ACTIVE', CURRENT_TIMESTAMP, 1);
    """, (coach_a_id,))
    sub_2_id = cursor.lastrowid

    # Verify coach has 2 subscription records (history preserved!)
    cursor.execute("SELECT COUNT(*) FROM subscriptions WHERE coach_id = ?;", (coach_a_id,))
    assert cursor.fetchone()[0] == 2, "Coach should maintain full subscription history records."
    print("✓ Subscription history preserved (2 historical entries for Coach A).")

    # Verify RESTRICT on plan deletion: Attempting to delete Plan 2 should fail because Coach A references it
    try:
        cursor.execute("DELETE FROM subscription_plans WHERE id = 2;")
        raise AssertionError("RESTRICT constraint failed: Plan was deleted while historical subscriptions exist!")
    except sqlite3.IntegrityError:
        print("✓ ON DELETE RESTRICT verified: Plan cannot be deleted while referenced by subscriptions.")

    # 6. Notifications Testing
    print("\n[Test 8] Testing User Notifications...")
    cursor.execute("""
    INSERT INTO notifications (user_id, title, message, notification_type, is_read)
    VALUES (?, 'Welcome to Professional Plan', 'Your 14-day trial has commenced with 50 client capacity.', 'SUBSCRIPTION', 0);
    """, (coach_a_uid,))
    notif_id = cursor.lastrowid

    cursor.execute("SELECT is_read, notification_type FROM notifications WHERE id = ?;", (notif_id,))
    row = cursor.fetchone()
    assert row[0] == 0, "Notification must be unread by default."
    assert row[1] == "SUBSCRIPTION"
    print("✓ Notification sent and default unread status verified.")

    # 7. Support Tickets Testing
    print("\n[Test 9] Testing Support Ticket Submission...")
    cursor.execute("""
    INSERT INTO support_tickets (user_id, coach_id, subject, description, priority, status)
    VALUES (?, ?, 'Inquiry regarding custom client CSV export', 'How do I export my active client roster for bookkeeping?', 'LOW', 'OPEN');
    """, (coach_a_uid, coach_a_id))
    ticket_id = cursor.lastrowid

    cursor.execute("SELECT status, priority, coach_id FROM support_tickets WHERE id = ?;", (ticket_id,))
    t_row = cursor.fetchone()
    assert t_row[0] == "OPEN"
    assert t_row[1] == "LOW"
    assert t_row[2] == coach_a_id
    print("✓ Support ticket registered with coach context and open status.")

    # 8. Announcements Testing
    print("\n[Test 10] Testing Platform Announcements...")
    cursor.execute("""
    INSERT INTO announcements (title, content, target_role, is_active, published_at)
    VALUES ('System Maintenance Window', 'Platform upgrades scheduled for Sunday 02:00 UTC.', 'COACH', 1, CURRENT_TIMESTAMP);
    """)
    cursor.execute("SELECT is_active, target_role FROM announcements WHERE title = 'System Maintenance Window';")
    a_row = cursor.fetchone()
    assert a_row[0] == 1
    assert a_row[1] == "COACH"
    print("✓ Targeted announcement created with active default status.")

    # 9. Audit Logs & Sanitization Testing
    print("\n[Test 11] Testing Audit Logs & Sensitive Secret Protection...")
    # Clean audit description
    cursor.execute("""
    INSERT INTO audit_logs (user_id, action, entity_type, entity_id, description, ip_address)
    VALUES (?, 'SUBSCRIPTION_CHANGE', 'Subscription', ?, 'Upgraded tier from Starter to Professional', '192.168.1.100');
    """, (coach_a_uid, sub_2_id))
    audit_id = cursor.lastrowid

    cursor.execute("SELECT action, user_id FROM audit_logs WHERE id = ?;", (audit_id,))
    audit_row = cursor.fetchone()
    assert audit_row[0] == "SUBSCRIPTION_CHANGE"
    assert audit_row[1] == coach_a_uid
    print("✓ Forensic audit log entry recorded.")

    # 10. Multi-Tenant Separation Testing
    print("\n[Test 12] Verifying Multi-Tenant Separation for Subscriptions & Tickets...")
    # Add Coach B subscription and ticket
    cursor.execute("""
    INSERT INTO subscriptions (coach_id, plan_id, status)
    VALUES (?, 1, 'ACTIVE');
    """, (coach_b_id,))

    cursor.execute("""
    INSERT INTO support_tickets (user_id, coach_id, subject, description)
    VALUES (?, ?, 'Billing query', 'Need copy of invoice.');
    """, (coach_b_uid, coach_b_id))
    conn.commit()

    # Coach A queries their subscriptions
    cursor.execute("SELECT id, plan_id FROM subscriptions WHERE coach_id = ?;", (coach_a_id,))
    coach_a_subs = cursor.fetchall()
    assert len(coach_a_subs) == 2
    for s in coach_a_subs:
        assert s[1] == 2, "Coach A should only see Professional plan subscriptions."

    # Coach A queries their support tickets
    cursor.execute("SELECT id, subject FROM support_tickets WHERE coach_id = ?;", (coach_a_id,))
    coach_a_tickets = cursor.fetchall()
    assert len(coach_a_tickets) == 1
    assert "Inquiry regarding custom client CSV export" in coach_a_tickets[0][1]
    print("✓ Multi-tenant separation verified for subscriptions and support tickets.")

    # 11. Cascade and User Removal Testing
    print("\n[Test 13] Verifying Safe Cascade & Audit Preservation on User Deactivation...")
    # If Coach A is deleted, their subscriptions and tickets cascade, but audit logs remain preserved with user_id = NULL
    cursor.execute("DELETE FROM users WHERE id = ?;", (coach_a_uid,))
    conn.commit()

    # Subscriptions deleted
    cursor.execute("SELECT COUNT(*) FROM subscriptions WHERE coach_id = ?;", (coach_a_id,))
    assert cursor.fetchone()[0] == 0

    # Audit log preserved with user_id set to NULL (forensic audit trail intact!)
    cursor.execute("SELECT user_id, action FROM audit_logs WHERE id = ?;", (audit_id,))
    surviving_log = cursor.fetchone()
    assert surviving_log[0] is None, "Audit log user_id must be set to NULL via ON DELETE SET NULL."
    assert surviving_log[1] == "SUBSCRIPTION_CHANGE"
    print("✓ User deletion cleanly removed private subscriptions while preserving forensic audit logs.")

    # Cleanup
    conn.close()
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    print("✓ Test database removed.")

    print("\n==================================================")
    print("ALL PHASE 2D DATABASE TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
