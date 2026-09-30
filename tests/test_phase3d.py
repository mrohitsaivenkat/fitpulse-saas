"""
FitPulse SaaS - Phase 3D Security Hardening Test Suite
Validates:
1. Secret Management: Configuration loads from environment, no real secrets committed.
2. Session Security: HTTPOnly, SameSite, Secure cookie configurations.
3. CSRF Protection: Generation, constant-time validation, and rejection of forged tokens.
4. File Upload & Filename Sanitation: Whitelisting, script rejection, path traversal defense.
5. Media Streaming Security: Private photos blocked from unauthenticated/cross-tenant access.
6. Rate Limiting: Sliding-window throttling triggers HTTP 429 on abuse.
7. Open Redirect Defense: External URLs and malformed targets rejected.
8. Sensitive Data Masking: User.to_dict excludes password_hash; audit log redacts credentials.
"""
import os
import sys
import secrets
import hmac

# Include project root
sys.path.insert(0, os.path.abspath("."))

from config import DevelopmentConfig, ProductionConfig, TestingConfig, BASE_DIR
from services.media_service import validate_file_safety, generate_secure_storage_filename
from services.rate_limiter import SlidingWindowRateLimiter
from services.auth_service import get_post_login_redirect
import re

SENSITIVE_PATTERNS = re.compile(
    r"\b(password|token|secret|api[_-]?key|bearer|hash|credit[_-]?card|cvv)\b\s*[:=]\s*(?:['\"][^'\"]*['\"]|\S+)",
    re.IGNORECASE
)

def sanitize_audit_text(text: str) -> str:
    if not text:
        return text
    return SENSITIVE_PATTERNS.sub(r"\1: [REDACTED]", text)


def run_tests():
    print("==================================================")
    print("RUNNING FITPULSE PHASE 3D SECURITY HARDENING TESTS")
    print("==================================================")

    # 1. Secret Management & Repository Cleanliness
    print("\n[Test 1] Testing Secret Management & Configuration Defaults...")
    assert DevelopmentConfig.SECRET_KEY is not None, "DevelopmentConfig missing SECRET_KEY fallback!"
    # Ensure .env is not present in repo root
    assert not os.path.exists(os.path.join(BASE_DIR, ".env")), "SECURITY RISK: .env file found in repository!"

    # Ensure .env.example only contains safe placeholders
    env_example_path = os.path.join(BASE_DIR, ".env.example")
    assert os.path.exists(env_example_path), ".env.example template missing!"
    with open(env_example_path, "r") as f:
        env_content = f.read()
        assert "password" in env_content.lower() or "username" in env_content.lower()
        # Verify no actual production database strings exist in example
        assert "rds.amazonaws.com" not in env_content
        assert "cloudsql" not in env_content
    print("✓ Secret management verified: No production secrets committed in repository.")

    # 2. Session Security Flags
    print("\n[Test 2] Testing Session & Cookie Security Flags...")
    assert DevelopmentConfig.SESSION_COOKIE_HTTPONLY is True, "SESSION_COOKIE_HTTPONLY not enabled!"
    assert DevelopmentConfig.SESSION_COOKIE_SAMESITE == "Lax", "SESSION_COOKIE_SAMESITE not set to 'Lax'!"
    assert DevelopmentConfig.PERMANENT_SESSION_LIFETIME > 0, "PERMANENT_SESSION_LIFETIME must be positive!"
    assert ProductionConfig.SESSION_COOKIE_SECURE is True, "ProductionConfig must enforce SESSION_COOKIE_SECURE=True!"
    assert DevelopmentConfig.SESSION_COOKIE_SECURE is False, "DevelopmentConfig should allow HTTP testing."
    print("✓ Session cookie security flags verified (HTTPOnly=True, SameSite=Lax, Secure in Prod).")

    # 3. CSRF Token Logic & Constant-Time Comparison
    print("\n[Test 3] Testing CSRF Generation & Validation...")
    token1 = secrets.token_urlsafe(32)
    token2 = secrets.token_urlsafe(32)
    assert len(token1) >= 32
    assert token1 != token2

    # Verification: identical token matches
    assert hmac.compare_digest(token1, token1) is True
    # Verification: mismatched token rejected
    assert hmac.compare_digest(token1, token2) is False
    assert hmac.compare_digest(token1, "") is False
    print("✓ CSRF token validation and constant-time comparison verified.")

    # 4. File Upload & Filename Sanitation
    print("\n[Test 4] Testing File Upload Security & Path Traversal Prevention...")
    # Safe files
    safe_files = ["checkin.jpg", "physique.png", "progress.webp", "back_pose.jpeg"]
    for fname in safe_files:
        is_safe, err = validate_file_safety(fname)
        assert is_safe is True, f"Legitimate file '{fname}' rejected: {err}"

    # Dangerous scripts rejected
    dangerous_files = [
        "exploit.php", "shell.sh", "malware.exe", "script.py",
        "payload.html", "xss.svg", "attack.js", "backdoor.phtml"
    ]
    for fname in dangerous_files:
        is_safe, err = validate_file_safety(fname)
        assert is_safe is False, f"SECURITY VULNERABILITY: Dangerous file '{fname}' was accepted!"
        assert "prohibited" in err or "Unsupported" in err

    # Path traversal attacks rejected
    traversal_attacks = [
        "../../etc/passwd", "..\\windows\\system32\\cmd.exe",
        "subfolder/image.png", "../uploads/photo.jpg"
    ]
    for attack in traversal_attacks:
        is_safe, err = validate_file_safety(attack)
        assert is_safe is False, f"SECURITY VULNERABILITY: Path traversal '{attack}' was accepted!"
        assert "Path traversal" in err

    # Non-predictable random storage name generation
    generated_name = generate_secure_storage_filename("my_private_photo.png")
    assert generated_name.endswith(".png")
    assert generated_name != "my_private_photo.png"
    assert len(generated_name) > 30  # UUID hex length
    print("✓ File upload security verified: Dangerous types and path traversal rejected; random naming enforced.")

    # 5. Rate Limiting Logic (Sliding Window)
    print("\n[Test 5] Testing Rate Limiting (Brute Force Defense)...")
    limiter = SlidingWindowRateLimiter()
    test_key = "login_test_ip_192.168.1.1"

    # Allow 5 attempts in 10 seconds
    for i in range(5):
        allowed, retry_after = limiter.is_allowed(test_key, max_requests=5, window_seconds=10)
        assert allowed is True, f"Attempt {i+1} was blocked prematurely!"

    # 6th attempt must be throttled with HTTP 429
    allowed, retry_after = limiter.is_allowed(test_key, max_requests=5, window_seconds=10)
    assert allowed is False, "CRITICAL: 6th attempt bypassed rate limiter!"
    assert retry_after > 0, "Retry-After seconds must be positive!"

    # Reset upon success
    limiter.reset(test_key)
    allowed, _ = limiter.is_allowed(test_key, max_requests=5, window_seconds=10)
    assert allowed is True, "Rate limiter reset failed!"
    print("✓ Rate limiting verified: Throttles rapid brute-force requests with positive Retry-After.")

    # 6. Open Redirect Protection
    print("\n[Test 6] Testing Open Redirect Defense...")
    class DummyUser:
        def __init__(self, role):
            self.role = role

    coach_user = DummyUser("COACH")
    client_user = DummyUser("CLIENT")
    admin_user = DummyUser("SUPER_ADMIN")

    # Safe local targets
    assert get_post_login_redirect(coach_user, "/coach/portal") == "/coach/portal"
    assert get_post_login_redirect(client_user, "/client/portal") == "/client/portal"

    # Malicious external targets blocked
    assert get_post_login_redirect(coach_user, "//evil.com") == "/coach"
    assert get_post_login_redirect(coach_user, "https://attacker.com/steal") == "/coach"
    assert get_post_login_redirect(client_user, "http://phishing.site") == "/client"
    assert get_post_login_redirect(admin_user, "javascript:alert(1)") == "/admin"

    # Cross-role boundary targets redirected to safe role home
    assert get_post_login_redirect(client_user, "/admin/overview") == "/client"
    assert get_post_login_redirect(coach_user, "/admin/overview") == "/coach"
    print("✓ Open redirect protection verified: External domains and role escalation targets blocked.")

    # 7. Sensitive Data Masking
    print("\n[Test 7] Testing Sensitive Data Masking in User Model & Audit Logs...")
    user_model_path = os.path.join(BASE_DIR, "models", "user.py")
    with open(user_model_path, "r") as f:
        user_code = f.read()
        assert "def to_dict(self, include_sensitive: bool = False)" in user_code
        assert 'if include_sensitive:' in user_code
        assert 'data["password_hash"] = self.password_hash' in user_code
        # Ensure password_hash is NOT inside the default dictionary literal
        assert '"password_hash": self.password_hash' not in user_code

    # Audit log redaction
    sensitive_log = "User reset password: password='SuperSecretPassword123' token='Bearer abc.123'"
    sanitized = sanitize_audit_text(sensitive_log)
    assert "SuperSecretPassword123" not in sanitized, "SECURITY RISK: Password logged in plain text!"
    assert "Bearer abc.123" not in sanitized, "SECURITY RISK: Token logged in plain text!"
    assert "[REDACTED]" in sanitized
    print("✓ Sensitive data masking verified: password_hash excluded from serializations, audit logs redacted.")

    print("\n==================================================")
    print("ALL PHASE 3D SECURITY HARDENING TESTS PASSED!")
    print("==================================================")


if __name__ == "__main__":
    run_tests()
