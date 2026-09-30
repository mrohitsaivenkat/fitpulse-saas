"""
FitPulse SaaS - Coach Client Management Service (Phase 4A)
Authoritatively handles client onboarding, demographic validation, roster filtering,
profile updates, and account status toggling for the authenticated Coach tenant.

SECURITY GUARANTEES:
- All actions require and enforce coach_id derived from server-side authenticated context.
- User role for clients is strictly forced to UserRole.CLIENT ("CLIENT").
- Rejects role escalation, duplicate emails, and arbitrary coach reassignment.
"""
import re
import secrets
from datetime import datetime, date
from typing import Optional, Tuple, Dict, Any, List

try:
    from sqlalchemy import or_, and_
    _HAS_SQLA = True
except ImportError:
    _HAS_SQLA = False
    or_ = None
    and_ = None

try:
    from models import db, User, Coach, Client
    from services.auth_service import hash_password, normalize_email
    _HAS_MODELS = True
except ImportError:
    _HAS_MODELS = False
    db = None
    User = None
    Coach = None
    Client = None
    def hash_password(pwd): return f"mock_{pwd}"
    def normalize_email(em): return (em or "").strip().lower()

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

ALLOWED_GENDERS = {"Male", "Female", "Non-Binary", "Other", "Prefer not to say"}
ALLOWED_ACTIVITY_LEVELS = {
    "Sedentary",
    "Lightly Active",
    "Moderately Active",
    "Very Active",
    "Extremely Active"
}


def validate_client_input(data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Validate and sanitize client input fields.
    Returns (is_valid, error_message, sanitized_dict).
    """
    sanitized: Dict[str, Any] = {}

    # 1. Names
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()

    if not is_update or "first_name" in data:
        if not first_name:
            return False, "First name is required.", {}
        if len(first_name) > 100:
            return False, "First name must not exceed 100 characters.", {}
        sanitized["first_name"] = first_name

    if not is_update or "last_name" in data:
        if not last_name:
            return False, "Last name is required.", {}
        if len(last_name) > 100:
            return False, "Last name must not exceed 100 characters.", {}
        sanitized["last_name"] = last_name

    # 2. Email (only validated on creation or when explicitly provided)
    if not is_update or "email" in data:
        email = normalize_email(data.get("email", ""))
        if not email:
            return False, "Email address is required.", {}
        if not EMAIL_REGEX.match(email):
            return False, "Please enter a valid email address.", {}
        if len(email) > 255:
            return False, "Email address must not exceed 255 characters.", {}
        sanitized["email"] = email

    # 3. Phone (optional)
    if "phone" in data and data["phone"]:
        phone = str(data["phone"]).strip()
        if len(phone) > 30:
            return False, "Phone number must not exceed 30 characters.", {}
        sanitized["phone"] = phone
    else:
        sanitized["phone"] = None

    # 4. Date of Birth (optional)
    dob_raw = data.get("date_of_birth")
    if dob_raw:
        if isinstance(dob_raw, date):
            sanitized["date_of_birth"] = dob_raw
        elif isinstance(dob_raw, str) and dob_raw.strip():
            try:
                parsed_dob = datetime.strptime(dob_raw.strip(), "%Y-%m-%d").date()
                if parsed_dob > date.today():
                    return False, "Date of birth cannot be in the future.", {}
                if parsed_dob.year < 1900:
                    return False, "Please provide a realistic date of birth.", {}
                sanitized["date_of_birth"] = parsed_dob
            except ValueError:
                return False, "Date of birth must be formatted as YYYY-MM-DD.", {}
        else:
            sanitized["date_of_birth"] = None
    else:
        sanitized["date_of_birth"] = None

    # 5. Gender (optional)
    gender = (data.get("gender") or "").strip()
    if gender:
        if gender not in ALLOWED_GENDERS:
            # Normalize title case or validate length
            if len(gender) > 20:
                return False, "Gender value exceeds allowed length.", {}
        sanitized["gender"] = gender
    else:
        sanitized["gender"] = None

    # 6. Physical metrics: Height & Weight (optional)
    height_raw = data.get("height")
    if height_raw is not None and str(height_raw).strip() != "":
        try:
            height = float(height_raw)
            if height <= 0 or height > 300:
                return False, "Height must be a positive number between 30 cm and 300 cm.", {}
            sanitized["height"] = round(height, 1)
        except ValueError:
            return False, "Height must be a valid numeric value.", {}
    else:
        sanitized["height"] = None

    weight_raw = data.get("current_weight")
    if weight_raw is not None and str(weight_raw).strip() != "":
        try:
            weight = float(weight_raw)
            if weight <= 0 or weight > 500:
                return False, "Weight must be a positive number between 20 kg and 500 kg.", {}
            sanitized["current_weight"] = round(weight, 1)
        except ValueError:
            return False, "Current weight must be a valid numeric value.", {}
    else:
        sanitized["current_weight"] = None

    # 7. Goals & Activity Level
    goal = (data.get("goal") or "").strip()
    if goal:
        if len(goal) > 200:
            return False, "Goal description must not exceed 200 characters.", {}
        sanitized["goal"] = goal
    else:
        sanitized["goal"] = "General Fitness"

    activity_level = (data.get("activity_level") or "").strip()
    if activity_level:
        if activity_level not in ALLOWED_ACTIVITY_LEVELS:
            if len(activity_level) > 50:
                return False, "Activity level must not exceed 50 characters.", {}
        sanitized["activity_level"] = activity_level
    else:
        sanitized["activity_level"] = "Moderately Active"

    # 8. Coach Private Notes (optional)
    notes = data.get("notes")
    if notes is not None:
        sanitized["notes"] = str(notes).strip()
    else:
        sanitized["notes"] = None

    return True, None, sanitized


def create_coach_client(coach_id: int, data: Dict[str, Any], db_session=None) -> Tuple[Optional[Any], Optional[str]]:
    """
    Register and enroll a new Client under the specified coach_id.
    Ensures email uniqueness, generates secure initial credentials, and binds Client to coach.
    """
    session = db_session or db.session
    is_valid, err, clean_data = validate_client_input(data, is_update=False)
    if not is_valid:
        return None, err

    # Duplicate account check
    existing_user = session.query(User).filter_by(email=clean_data["email"]).first()
    if existing_user:
        return None, "An account with this email address already exists."

    # Generate initial password securely (never exposed in plain text in logs or database)
    initial_password = data.get("password") or (secrets.token_urlsafe(12) + "A1!")

    try:
        # Create User entity with strictly forced CLIENT role
        client_user = User(
            email=clean_data["email"],
            role="CLIENT",  # Immutable role assignment
            first_name=clean_data["first_name"],
            last_name=clean_data["last_name"],
            phone=clean_data.get("phone"),
            is_active=True
        )
        client_user.set_password(initial_password)
        session.add(client_user)
        session.flush()  # Populate client_user.id

        # Create Client entity bound strictly to authenticated coach_id
        new_client = Client(
            user_id=client_user.id,
            coach_id=coach_id,  # Authoritative tenant binding
            date_of_birth=clean_data.get("date_of_birth"),
            gender=clean_data.get("gender"),
            height=clean_data.get("height"),
            current_weight=clean_data.get("current_weight"),
            goal=clean_data.get("goal"),
            activity_level=clean_data.get("activity_level"),
            notes=clean_data.get("notes"),
            is_active=True
        )
        session.add(new_client)
        session.commit()
        return new_client, None
    except Exception as e:
        session.rollback()
        return None, f"Failed to register client: {str(e)}"


def update_coach_client(coach_id: int, client_id: int, data: Dict[str, Any], db_session=None) -> Tuple[Optional[Any], Optional[str]]:
    """
    Update an existing client's details.
    Verifies that the client belongs to the authenticated coach.
    Prevents role manipulation or reassignment to another coach.
    """
    session = db_session or db.session
    client = session.query(Client).filter_by(id=client_id, coach_id=coach_id).first()
    if not client:
        return None, "Client not found or access denied."

    is_valid, err, clean_data = validate_client_input(data, is_update=True)
    if not is_valid:
        return None, err

    try:
        # Update User record details
        if client.user:
            if "first_name" in clean_data:
                client.user.first_name = clean_data["first_name"]
            if "last_name" in clean_data:
                client.user.last_name = clean_data["last_name"]
            if "phone" in clean_data:
                client.user.phone = clean_data["phone"]

        # Update Client demographic & physical attributes
        if "date_of_birth" in clean_data:
            client.date_of_birth = clean_data["date_of_birth"]
        if "gender" in clean_data:
            client.gender = clean_data["gender"]
        if "height" in clean_data:
            client.height = clean_data["height"]
        if "current_weight" in clean_data:
            client.current_weight = clean_data["current_weight"]
        if "goal" in clean_data:
            client.goal = clean_data["goal"]
        if "activity_level" in clean_data:
            client.activity_level = clean_data["activity_level"]
        if "notes" in clean_data:
            client.notes = clean_data["notes"]

        # CRITICAL GUARANTEES: coach_id and user_id are never touched
        session.commit()
        return client, None
    except Exception as e:
        session.rollback()
        return None, f"Failed to update client: {str(e)}"


def toggle_client_status(coach_id: int, client_id: int, db_session=None) -> Tuple[Optional[Any], Optional[str]]:
    """
    Toggle a client's active status (deactivate or reactivate).
    Verifies that the client belongs to the authenticated coach.
    Preserves all historical client data upon deactivation.
    """
    session = db_session or db.session
    client = session.query(Client).filter_by(id=client_id, coach_id=coach_id).first()
    if not client:
        return None, "Client not found or access denied."

    try:
        new_status = not client.is_active
        client.is_active = new_status
        if client.user:
            client.user.is_active = new_status
        session.commit()
        return client, None
    except Exception as e:
        session.rollback()
        return None, f"Failed to toggle status: {str(e)}"


def get_filtered_clients(coach_id: int, q: Optional[str] = None, status: Optional[str] = None, db_session=None) -> List[Any]:
    """
    Query clients strictly belonging to coach_id with optional search query and status filter.
    """
    session = db_session or db.session
    query = session.query(Client).join(User, Client.user_id == User.id).filter(Client.coach_id == coach_id)

    # Status filter
    if status == "active":
        query = query.filter(Client.is_active.is_(True))
    elif status == "inactive":
        query = query.filter(Client.is_active.is_(False))

    # Search filter (name, email, or goal)
    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                User.first_name.ilike(term),
                User.last_name.ilike(term),
                User.email.ilike(term),
                Client.goal.ilike(term)
            )
        )

    return query.order_by(Client.created_at.desc()).all()
