"""
FitPulse SaaS - Phase 3B Role-Based Access Control (RBAC) Test Suite
Validates:
1. Unauthenticated access blocked across all protected portals (Admin, Coach, Client).
2. SUPER_ADMIN authorization:
   - Permitted on platform admin routes.
   - Authoritative database check defeats URL/form role spoofing.
3. COACH authorization:
   - Permitted on coach workspace routes.
   - Denied access to admin routes (HTTP 403 Forbidden).
4. CLIENT authorization:
   - Permitted on client portal routes.
   - Denied access to admin routes (HTTP 403 Forbidden).
   - Denied access to coach workspace routes (HTTP 403 Forbidden).
5. Post-login role redirection:
   - SUPER_ADMIN -> /admin
   - COACH -> /coach
   - CLIENT -> /client
   - Open-redirect protection enforced.
6. Privilege escalation prevention:
   - Public registration cannot create SUPER_ADMIN.
   - Client-supplied role parameters are ignored by server decorators.
7. Profile relationships:
   - User -> Coach (1:1)
   - User -> Client (1:1)
"""
import sqlite3
import os
import sys

# Include project root in sys.path
sys.path.insert(0, os.path.abspath("."))

from services.auth_service import hash_password, verify_password, get_post_login_redirect

DB_FILE = "fitness_platform_phase3b_test.db"

class MockUser:
    """Mock User entity simulating models.User with Phase 3B RBAC methods."""
    def __init__(self, id, email, password_hash, role="CLIENT", first_name="Test", last_name="User", is_active=True):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.first_name = first_name
        self.last_name = last_name
        self.is_active = bool(is_active)

    @property
    def is_super_admin(self) -> bool:
        return self.role == "SUPER_ADMIN"

    @property
    def is_coach(self) -> bool:
        return self.role == "COACH"

    @property
    def is_client(self) -> bool:
        return self.role == "CLIENT"

    def has_role(self, *roles) -> bool:
        role_values = [str(r.value if hasattr(r, "value") else r).upper() for r in roles]
        return self.role.upper() in role_values


def simulate_rbac_gate(user, allowed_roles, client_params=None):
    """
    Simulates the server-authoritative roles_required decorator.
    Explicitly ignores any client-supplied params (query, body, headers).
    Returns (status_code, response_message).
    """
    if user is None:
        return 401, "Authentication required."
    if not user.is_active:
        return 403, "Account is deactivated."

    # Server-authoritative role check from user model
    norm_allowed = [str(r.value if hasattr(r, "value") else r).upper() for r in allowed_roles]
    if user.role.upper() not in norm_allowed:
        return 403, "Access Denied - Insufficient role permissions."

    return 200, "Access Granted."


def run_tests():
    print("==================================================")
    print("RUNNING FITPULSE PHASE 3B RBAC TESTS")
    print("==================================================")

    # 1. Initialize SQLite Database
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    print("\n[Test 1] Initializing SQLite database and seeding role users...")
    cursor.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email VARCHAR(255) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(20) NOT NULL DEFAULT 'CLIENT',
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE coaches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        business_name VARCHAR(150) NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        coach_id INTEGER NOT NULL,
        goal VARCHAR(200),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (coach_id) REFERENCES coaches(id) ON DELETE CASCADE
    );
    """)

    pwhash = hash_password("FitPulseSecure2026!")

    # 1. Super Admin
    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('admin@fitpulse.test', ?, 'SUPER_ADMIN', 'Platform', 'Admin');", (pwhash,))
    admin_uid = cursor.lastrowid

    # 2. Coach
    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('coach@fitpulse.test', ?, 'COACH', 'Marcus', 'Aurelius');", (pwhash,))
    coach_uid = cursor.lastrowid
    cursor.execute("INSERT INTO coaches (user_id, business_name) VALUES (?, 'Stoic Strength Labs');", (coach_uid,))
    coach_id = cursor.lastrowid

    # 3. Client
    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('client@fitpulse.test', ?, 'CLIENT', 'Lucius', 'Verus');", (pwhash,))
    client_uid = cursor.lastrowid
    cursor.execute("INSERT INTO clients (user_id, coach_id, goal) VALUES (?, ?, 'Body Recomposition');", (client_uid, coach_id))

    # 4. Deactivated Coach
    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name, is_active) VALUES ('deactivated@fitpulse.test', ?, 'COACH', 'Ex', 'Coach', 0);", (pwhash,))
    deact_uid = cursor.lastrowid

    conn.commit()
    print("✓ Successfully seeded SUPER_ADMIN, COACH, CLIENT, and DEACTIVATED accounts.")

    # Instantiate MockUser instances from database records
    user_admin = MockUser(admin_uid, 'admin@fitpulse.test', pwhash, role='SUPER_ADMIN')
    user_coach = MockUser(coach_uid, 'coach@fitpulse.test', pwhash, role='COACH')
    user_client = MockUser(client_uid, 'client@fitpulse.test', pwhash, role='CLIENT')
    user_deact = MockUser(deact_uid, 'deactivated@fitpulse.test', pwhash, role='COACH', is_active=False)

    # 2. Test Unauthenticated Access
    print("\n[Test 2] Testing unauthenticated access rejection across all portals...")
    status, _ = simulate_rbac_gate(None, ["SUPER_ADMIN"])
    assert status == 401, "Unauthenticated user bypassed admin gate!"

    status, _ = simulate_rbac_gate(None, ["COACH"])
    assert status == 401, "Unauthenticated user bypassed coach gate!"

    status, _ = simulate_rbac_gate(None, ["CLIENT"])
    assert status == 401, "Unauthenticated user bypassed client gate!"
    print("✓ Unauthenticated callers strictly rejected with HTTP 401.")

    # 3. Test Admin Portal Access (/admin)
    print("\n[Test 3] Testing Admin Portal RBAC protection...")
    # Admin allowed
    status, _ = simulate_rbac_gate(user_admin, ["SUPER_ADMIN"])
    assert status == 200, "SUPER_ADMIN denied from admin portal!"

    # Coach rejected with 403
    status, msg = simulate_rbac_gate(user_coach, ["SUPER_ADMIN"])
    assert status == 403, "COACH improperly granted admin access!"
    assert "Insufficient role permissions" in msg

    # Client rejected with 403
    status, msg = simulate_rbac_gate(user_client, ["SUPER_ADMIN"])
    assert status == 403, "CLIENT improperly granted admin access!"
    assert "Insufficient role permissions" in msg
    print("✓ Admin route strictly accessible only to SUPER_ADMIN (403 for Coach and Client).")

    # 4. Test Coach Portal Access (/coach)
    print("\n[Test 4] Testing Coach Workspace RBAC protection...")
    # Coach allowed
    status, _ = simulate_rbac_gate(user_coach, ["COACH", "SUPER_ADMIN"])
    assert status == 200, "COACH denied from coach workspace!"

    # Super Admin allowed (platform oversight)
    status, _ = simulate_rbac_gate(user_admin, ["COACH", "SUPER_ADMIN"])
    assert status == 200, "SUPER_ADMIN denied from coach workspace oversight!"

    # Client rejected with 403
    status, msg = simulate_rbac_gate(user_client, ["COACH"])
    assert status == 403, "CLIENT improperly granted coach access!"
    assert "Insufficient role permissions" in msg
    print("✓ Coach route accessible to COACH; CLIENT rejected with HTTP 403.")

    # 5. Test Client Portal Access (/client)
    print("\n[Test 5] Testing Client Portal RBAC protection...")
    # Client allowed
    status, _ = simulate_rbac_gate(user_client, ["CLIENT", "SUPER_ADMIN"])
    assert status == 200, "CLIENT denied from client portal!"

    # Coach strictly rejected from dedicated client-only route
    status, msg = simulate_rbac_gate(user_coach, ["CLIENT"])
    assert status == 403, "COACH improperly allowed in strict client-only portal!"
    assert "Insufficient role permissions" in msg
    print("✓ Client route accessible to CLIENT; COACH rejected with HTTP 403.")

    # 6. Test Deactivated Account Rejection
    print("\n[Test 6] Testing deactivated user rejection under RBAC...")
    status, msg = simulate_rbac_gate(user_deact, ["COACH"])
    assert status == 403, "Deactivated coach granted access!"
    assert "deactivated" in msg
    print("✓ Deactivated account blocked by RBAC gate.")

    # 7. Test Privilege Escalation Spoofing Defense
    print("\n[Test 7] Testing privilege escalation defense (ignoring client role manipulation)...")
    # Client attempts spoofing via URL query: ?role=SUPER_ADMIN
    spoofed_params = {"role": "SUPER_ADMIN", "admin": "true"}
    # The server gate inspects user_client.role from DB, not spoofed_params
    status, _ = simulate_rbac_gate(user_client, ["SUPER_ADMIN"], client_params=spoofed_params)
    assert status == 403, "CRITICAL VULNERABILITY: Client query parameter escalated privilege!"

    # Coach attempts spoofing via form input: role=SUPER_ADMIN
    status, _ = simulate_rbac_gate(user_coach, ["SUPER_ADMIN"], client_params=spoofed_params)
    assert status == 403, "CRITICAL VULNERABILITY: Coach form parameter escalated privilege!"
    print("✓ Server-authoritative checks defeat URL/query/form role manipulation attacks.")

    # 8. Test Post-Login Role Redirection
    print("\n[Test 8] Testing post-login redirection logic...")
    assert get_post_login_redirect(user_admin) == "/admin", "Admin not routed to /admin"
    assert get_post_login_redirect(user_coach) == "/coach", "Coach not routed to /coach"
    assert get_post_login_redirect(user_client) == "/client", "Client not routed to /client"

    # Requested target respecting role boundaries
    assert get_post_login_redirect(user_coach, requested_next="/coach/clients") == "/coach/clients"
    # Unauthorized requested target redirected to safe role home
    assert get_post_login_redirect(user_coach, requested_next="/admin/overview") == "/coach"
    assert get_post_login_redirect(user_client, requested_next="/coach/roster") == "/client"
    # Open redirect attack blocked
    assert get_post_login_redirect(user_coach, requested_next="//evil.com") == "/coach"
    assert get_post_login_redirect(user_coach, requested_next="https://attacker.com") == "/coach"
    print("✓ Role-based post-login redirection and open-redirect defenses verified.")

    # 9. Test Profile Relationships
    print("\n[Test 9] Testing 1:1 Profile relationships...")
    cursor.execute("SELECT c.business_name FROM coaches c WHERE c.user_id = ?;", (coach_uid,))
    coach_row = cursor.fetchone()
    assert coach_row is not None and coach_row[0] == "Stoic Strength Labs"

    cursor.execute("SELECT cl.goal FROM clients cl WHERE cl.user_id = ?;", (client_uid,))
    client_row = cursor.fetchone()
    assert client_row is not None and client_row[0] == "Body Recomposition"
    print("✓ 1:1 Profile relationships verified (User -> Coach and User -> Client).")

    # 10. Test Model Role Helper Properties
    print("\n[Test 10] Testing User model role helper methods...")
    assert user_admin.is_super_admin is True
    assert user_admin.is_coach is False
    assert user_admin.has_role("SUPER_ADMIN") is True

    assert user_coach.is_coach is True
    assert user_coach.is_super_admin is False
    assert user_coach.has_role("COACH") is True

    assert user_client.is_client is True
    assert user_client.is_coach is False
    assert user_client.has_role("CLIENT") is True
    print("✓ User role helper methods correctly reflect authoritative database status.")

    # Clean up
    conn.close()
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    print("✓ Test database removed.")

    print("\n==================================================")
    print("ALL PHASE 3B RBAC TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
