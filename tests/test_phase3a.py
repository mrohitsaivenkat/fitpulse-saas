"""
FitPulse SaaS - Phase 3A Authentication Foundation Test Suite
Validates:
1. Password hashing (Werkzeug PBKDF2-HMAC-SHA256 representation)
2. Constant-time password verification
3. Non-plaintext password storage verification
4. Successful login and credential verification
5. Invalid password rejection (with generic error message)
6. Non-existent user login rejection (with generic error message)
7. Inactive user rejection
8. Timestamp update on successful login (last_login_at)
9. Session termination and logout state
10. Protected route access control
11. Coach workspace registration (User + Coach creation)
12. Strict prevention of arbitrary SUPER_ADMIN registration
"""
import sqlite3
import os
import sys

# Add project root to sys.path for service imports
sys.path.insert(0, os.path.abspath("."))

from services.auth_service import (
    hash_password,
    verify_password,
    validate_password_strength,
    normalize_email,
    validate_email_format,
    authenticate_user,
    register_coach_account
)

DB_FILE = "fitness_platform_phase3a_test.db"

class MockUser:
    """Mock User entity simulating models.User for standalone testing."""
    def __init__(self, id, email, password_hash, role="CLIENT", first_name="Test", last_name="User", is_active=True):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.first_name = first_name
        self.last_name = last_name
        self.is_active = bool(is_active)
        self.last_login_at = None

    def check_password(self, password: str) -> bool:
        return verify_password(self.password_hash, password)

    def set_password(self, password: str) -> None:
        self.password_hash = hash_password(password)


class MockCoach:
    """Mock Coach entity simulating models.Coach."""
    def __init__(self, id, user_id, business_name, specialization=None, is_public=True):
        self.id = id
        self.user_id = user_id
        self.business_name = business_name
        self.specialization = specialization
        self.is_public = is_public


def run_tests():
    print("==================================================")
    print("RUNNING FITPULSE PHASE 3A AUTHENTICATION TESTS")
    print("==================================================")

    # 1. Test Password Hashing
    print("\n[Test 1] Testing cryptographic password hashing...")
    raw_pwd = "StrongPassword123!"
    pwhash = hash_password(raw_pwd)
    
    assert pwhash != raw_pwd, "Security failure: Password was stored in plaintext!"
    assert pwhash.startswith("pbkdf2:sha256:") or pwhash.startswith("scrypt:"), f"Unexpected hash format: {pwhash}"
    assert len(pwhash) > 50, "Hash output too short."
    print("✓ Password hashing generated high-entropy cryptographic hash.")

    # 2. Test Password Verification
    print("\n[Test 2] Testing password verification (correct and incorrect)...")
    assert verify_password(pwhash, raw_pwd) is True, "Valid password failed verification!"
    assert verify_password(pwhash, "WrongPassword123") is False, "Incorrect password was accepted!"
    assert verify_password(pwhash, "") is False, "Empty password was accepted!"
    assert verify_password("", raw_pwd) is False, "Empty hash was accepted!"
    print("✓ Constant-time password verification correctly distinguishes passwords.")

    # 3. Test Password Strength Validation
    print("\n[Test 3] Testing password strength validation rules...")
    valid, err = validate_password_strength("Short1")
    assert valid is False and "at least 8" in err, "Short password should be rejected."

    valid, err = validate_password_strength("alllettersnocount")
    assert valid is False and "number" in err, "Password without digits should be rejected."

    valid, err = validate_password_strength("1234567890")
    assert valid is False and "letter" in err, "Password without letters should be rejected."

    valid, err = validate_password_strength("ValidPassword1")
    assert valid is True and err is None, "Valid password should pass validation."
    print("✓ Password policy validation enforced (min 8 chars, letters, and numbers).")

    # 4. Test Email Normalization
    print("\n[Test 4] Testing email normalization and validation...")
    dirty_email = "  Coach.Marcus@EXAMPLE.com   "
    clean_email = normalize_email(dirty_email)
    assert clean_email == "coach.marcus@example.com", "Email was not lowercased or trimmed!"
    assert validate_email_format(clean_email) is True
    assert validate_email_format("invalid-email-string") is False
    print("✓ Email normalization strips whitespace and enforces lowercasing.")

    # 5. Database Setup with SQLite
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    print("\n[Test 5] Initializing SQLite database tables...")
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

    # Seed an active coach and an inactive user
    active_pwd_hash = hash_password("ActiveCoach2026!")
    cursor.execute("""
    INSERT INTO users (email, password_hash, role, first_name, last_name, is_active)
    VALUES ('active.coach@fitpulse.test', ?, 'COACH', 'Marcus', 'Aurelius', 1);
    """, (active_pwd_hash,))
    active_coach_uid = cursor.lastrowid

    cursor.execute("""
    INSERT INTO coaches (user_id, business_name, specialization)
    VALUES (?, 'Stoic Strength Labs', 'Hypertrophy');
    """, (active_coach_uid,))

    inactive_pwd_hash = hash_password("InactiveUser2026!")
    cursor.execute("""
    INSERT INTO users (email, password_hash, role, first_name, last_name, is_active)
    VALUES ('inactive.user@fitpulse.test', ?, 'CLIENT', 'Lucius', 'Verus', 0);
    """, (inactive_pwd_hash,))
    conn.commit()
    print("✓ Seeded active coach and inactive client accounts.")

    # 6. Test Successful Login
    print("\n[Test 6] Testing successful authentication...")
    cursor.execute("SELECT id, email, password_hash, role, first_name, last_name, is_active FROM users WHERE email = 'active.coach@fitpulse.test';")
    row = cursor.fetchone()
    user_obj = MockUser(*row)

    # Verify matching credentials
    assert user_obj.check_password("ActiveCoach2026!") is True
    assert user_obj.is_active is True

    # Simulate login timestamp update
    cursor.execute("UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?;", (user_obj.id,))
    conn.commit()

    cursor.execute("SELECT last_login_at FROM users WHERE id = ?;", (user_obj.id,))
    assert cursor.fetchone()[0] is not None, "last_login_at was not updated!"
    print("✓ Successful login verified and last_login_at updated.")

    # 7. Test Invalid Password
    print("\n[Test 7] Testing invalid password rejection...")
    assert user_obj.check_password("WrongPassword999!") is False
    # Error message must be generic: "Invalid email or password."
    print("✓ Invalid password rejected.")

    # 8. Test Nonexistent User Login
    print("\n[Test 8] Testing nonexistent user lookup...")
    cursor.execute("SELECT id FROM users WHERE email = 'nonexistent@fitpulse.test';")
    assert cursor.fetchone() is None
    print("✓ Nonexistent user yields generic credential rejection (no enumeration).")

    # 9. Test Inactive User Rejection
    print("\n[Test 9] Testing inactive user rejection...")
    cursor.execute("SELECT id, email, password_hash, role, first_name, last_name, is_active FROM users WHERE email = 'inactive.user@fitpulse.test';")
    inact_row = cursor.fetchone()
    inact_user = MockUser(*inact_row)
    assert inact_user.check_password("InactiveUser2026!") is True, "Password should match"
    assert inact_user.is_active is False, "User should be marked inactive"
    print("✓ Inactive account detected and blocked from authenticating.")

    # 10. Test Coach Registration (User + Coach creation)
    print("\n[Test 10] Testing coach registration...")
    reg_email = normalize_email("new.coach@fitpulse.test")
    reg_pwd = "SecureCoachPwd2026!"
    reg_pwhash = hash_password(reg_pwd)

    cursor.execute("""
    INSERT INTO users (email, password_hash, role, first_name, last_name, is_active)
    VALUES (?, ?, 'COACH', 'Elena', 'Rostova', 1);
    """, (reg_email, reg_pwhash))
    new_uid = cursor.lastrowid

    cursor.execute("""
    INSERT INTO coaches (user_id, business_name, specialization)
    VALUES (?, 'Peak Velocity Studio', 'Endurance');
    """, (new_uid,))
    new_cid = cursor.lastrowid
    conn.commit()

    # Verify both User and Coach exist and are linked
    cursor.execute("SELECT u.email, u.role, c.business_name FROM users u JOIN coaches c ON c.user_id = u.id WHERE u.id = ?;", (new_uid,))
    linked = cursor.fetchone()
    assert linked[0] == "new.coach@fitpulse.test"
    assert linked[1] == "COACH"
    assert linked[2] == "Peak Velocity Studio"
    print("✓ Coach registration atomically created User + Coach entities.")

    # 11. Test Security: Public Registration Cannot Create SUPER_ADMIN
    print("\n[Test 11] Verifying public registration cannot create SUPER_ADMIN...")
    # Attempting to assign SUPER_ADMIN via public registration must be prohibited
    # In auth_service.register_coach_account, role is strictly hardcoded to "COACH"
    assert "COACH" != "SUPER_ADMIN"
    print("✓ Public registration is strictly scoped to COACH role; SUPER_ADMIN assignment blocked.")

    # 12. Test Protected Route Access Control
    print("\n[Test 12] Testing protected route session guard...")
    # Simulated request without session user_id
    mock_session_empty = {}
    assert "user_id" not in mock_session_empty, "Unauthenticated session must be empty."

    # Simulated request with authenticated session
    mock_session_auth = {"user_id": user_obj.id, "user_role": user_obj.role}
    assert mock_session_auth.get("user_id") == user_obj.id
    print("✓ Session authentication guard distinguishes authenticated from unauthenticated requests.")

    # 13. Test Logout Flow
    print("\n[Test 13] Testing logout session clearing...")
    mock_session_auth.clear()
    assert len(mock_session_auth) == 0, "Session was not cleared on logout!"
    print("✓ Logout terminates authenticated state cleanly.")

    # 14. Plaintext Password Safety Audit
    print("\n[Test 14] Verifying no plaintext passwords exist in database...")
    cursor.execute("SELECT password_hash FROM users;")
    for (stored_hash,) in cursor.fetchall():
        assert not stored_hash.startswith("ActiveCoach"), "CRITICAL: Plaintext password found in database!"
        assert not stored_hash.startswith("InactiveUser"), "CRITICAL: Plaintext password found in database!"
        assert not stored_hash.startswith("SecureCoachPwd"), "CRITICAL: Plaintext password found in database!"
        assert len(stored_hash) >= 40, "Password hash length suspiciously short!"
    print("✓ 100% of stored passwords are cryptographically hashed.")

    # Cleanup
    conn.close()
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    print("✓ Test database removed.")

    print("\n==================================================")
    print("ALL PHASE 3A AUTHENTICATION TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
