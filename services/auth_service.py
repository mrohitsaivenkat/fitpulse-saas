"""
FitPulse SaaS - Authentication Service
Encapsulates cryptographic password hashing, constant-time verification,
input validation, and credential verification.
Guarantees:
- Passwords are never stored or logged in plaintext.
- Generic error messages to prevent email enumeration attacks.
- Public registration strictly rejects SUPER_ADMIN elevation.
"""
import re
import secrets
import hashlib
from datetime import datetime, timezone
from typing import Tuple, Optional, Any

# Try importing Werkzeug security utilities, with fallback to standard library hashlib
try:
    from werkzeug.security import generate_password_hash as _wz_gen_hash
    from werkzeug.security import check_password_hash as _wz_chk_hash
    _HAS_WERKZEUG = True
except ImportError:
    _HAS_WERKZEUG = False

# Password strength regex: min 8 characters, at least 1 digit, at least 1 letter
PASSWORD_LETTER_REGEX = re.compile(r"[a-zA-Z]")
PASSWORD_DIGIT_REGEX = re.compile(r"[0-9]")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def hash_password(password: str) -> str:
    """
    Generate a cryptographic hash using PBKDF2-HMAC-SHA256 with 600,000 iterations.
    Compatible with Werkzeug standard hash representation.
    """
    if not password:
        raise ValueError("Password cannot be empty.")

    if _HAS_WERKZEUG:
        return _wz_gen_hash(password, method="pbkdf2:sha256:600000")

    # Native Python 3.11 Standard Library implementation
    salt = secrets.token_hex(16)
    iterations = 600000
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return f"pbkdf2:sha256:{iterations}${salt}${derived.hex()}"


def verify_password(password_hash: str, password: str) -> bool:
    """
    Verify candidate password against cryptographic hash in constant time.
    Prevents timing attacks.
    """
    if not password_hash or not password:
        return False

    if _HAS_WERKZEUG:
        try:
            return _wz_chk_hash(password_hash, password)
        except Exception:
            pass

    # Standard Library fallback verification
    try:
        parts = password_hash.split("$")
        if len(parts) != 3:
            return False
        algo_info, salt, stored_hash = parts
        # Parse algo: e.g., pbkdf2:sha256:600000
        algo_parts = algo_info.split(":")
        if len(algo_parts) == 3 and algo_parts[0] == "pbkdf2":
            hash_name = algo_parts[1]
            iterations = int(algo_parts[2])
            candidate = hashlib.pbkdf2_hmac(hash_name, password.encode("utf-8"), salt.encode("utf-8"), iterations).hex()
            return secrets.compare_digest(candidate, stored_hash)
    except Exception:
        return False

    return False


def normalize_email(email: str) -> str:
    """Strip whitespace and convert to lowercase for case-insensitive identity lookup."""
    if not email:
        return ""
    return email.strip().lower()


def validate_email_format(email: str) -> bool:
    """Validate that the normalized email adheres to standard address structure."""
    if not email or len(email) > 255:
        return False
    return bool(EMAIL_REGEX.match(email))


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """
    Enforce security requirements on prospective user passwords:
    - Minimum 8 characters
    - At least one alphabetical character
    - At least one numeric digit
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if len(password) > 128:
        return False, "Password cannot exceed 128 characters."
    if not PASSWORD_LETTER_REGEX.search(password):
        return False, "Password must contain at least one letter."
    if not PASSWORD_DIGIT_REGEX.search(password):
        return False, "Password must contain at least one number."
    return True, None


def authenticate_user(db_session, UserModel, email: str, password: str) -> Tuple[Optional[Any], Optional[str]]:
    """
    Verify user credentials and account status.
    Uses timing-resistant dummy verification to prevent user enumeration.
    Returns (user, error_message).
    """
    normalized = normalize_email(email)
    if not normalized or not password:
        return None, "Please provide both email and password."

    # Look up user by unique indexed email
    user = db_session.query(UserModel).filter_by(email=normalized).first()

    if not user:
        # Dummy verification to prevent timing analysis
        verify_password("pbkdf2:sha256:600000$deadbeef$deadbeef", password)
        return None, "Invalid email or password."

    # Verify password hash
    if not user.check_password(password):
        return None, "Invalid email or password."

    # Account state verification
    if not user.is_active:
        return None, "Your account is deactivated. Please contact support."

    return user, None


def register_coach_account(
    db_session,
    UserModel,
    CoachModel,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    business_name: str,
    phone: Optional[str] = None,
    specialization: Optional[str] = None
) -> Tuple[Optional[Any], Optional[str]]:
    """
    Register a new Coach user and initialize their dedicated coaching workspace.
    Explicitly prohibits arbitrary registration as SUPER_ADMIN.
    """
    normalized = normalize_email(email)
    if not validate_email_format(normalized):
        return None, "Please enter a valid email address."

    is_valid, pwd_error = validate_password_strength(password)
    if not is_valid:
        return None, pwd_error

    if not first_name or not first_name.strip():
        return None, "First name is required."
    if not last_name or not last_name.strip():
        return None, "Last name is required."
    if not business_name or not business_name.strip():
        return None, "Coaching business name is required."

    # Prevent duplicate accounts
    existing = db_session.query(UserModel).filter_by(email=normalized).first()
    if existing:
        return None, "An account with this email address already exists."

    # Create User with strictly enforced COACH role
    new_user = UserModel(
        email=normalized,
        role="COACH",  # Hardcoded: NEVER allows SUPER_ADMIN
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        phone=phone.strip() if phone else None,
        is_active=True,
        is_verified=False
    )
    new_user.set_password(password)
    db_session.add(new_user)
    db_session.flush()

    # Create dedicated Coach tenant entity
    new_coach = CoachModel(
        user_id=new_user.id,
        business_name=business_name.strip(),
        specialization=specialization.strip() if specialization else None,
        is_public=True
    )
    db_session.add(new_coach)
    db_session.commit()

    return new_user, None


def get_post_login_redirect(user, requested_next: Optional[str] = None) -> str:
    """
    Determine safe post-login redirect URL based on authoritative database role.
    Prevents open redirect vulnerabilities and routes each role to their portal.
    """
    role = str(user.role).upper() if user and getattr(user, "role", None) else ""
    default_destinations = {
        "SUPER_ADMIN": "/admin",
        "COACH": "/coach",
        "CLIENT": "/client",
    }
    role_home = default_destinations.get(role, "/")

    if requested_next:
        # Validate that the redirect target is strictly local and safe
        if requested_next.startswith("/") and not requested_next.startswith("//") and not requested_next.startswith("/\\"):
            # Role boundary check for requested target
            if requested_next.startswith("/admin") and role != "SUPER_ADMIN":
                return role_home
            if requested_next.startswith("/coach") and role not in ("COACH", "SUPER_ADMIN"):
                return role_home
            if requested_next.startswith("/client") and role not in ("CLIENT", "SUPER_ADMIN"):
                return role_home
            return requested_next

    return role_home

