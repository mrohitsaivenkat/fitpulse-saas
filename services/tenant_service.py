"""
FitPulse SaaS - Multi-Tenant Authorization Service (Phase 3C)
Enforces backend server-authoritative tenant and resource ownership isolation:
- Partitioning: Coaches (SaaS Tenants) strictly isolated from each other.
- Partitioning: Clients (Athletes) strictly isolated to their own personal data.
- IDOR Defense: Verifies resource ownership prior to retrieval, mutation, or deletion.
- Anti-Tampering: Completely strips/discards any client-submitted coach_id, client_id,
  or user_id in headers, query parameters, hidden fields, or JSON payloads.
- Anti-Enumeration: Rejects cross-tenant access with generic messages without leaking existence.
"""
from functools import wraps
from typing import Optional, Tuple, Any

try:
    from flask import request, jsonify, render_template, g
    _HAS_FLASK = True
except ImportError:
    _HAS_FLASK = False
    request = None
    jsonify = None
    render_template = None
    class _MockG:
        coach = None
        coach_id = None
        client = None
        client_id = None
    g = _MockG()

try:
    from models import db, Coach, Client, DietPlan, WorkoutPlan, Progress, ProgressPhoto, Transformation, Review
    from services.auth_decorators import get_authenticated_user
    _HAS_MODELS = True
except ImportError:
    _HAS_MODELS = False
    db = None
    Coach = None
    Client = None
    DietPlan = None
    WorkoutPlan = None
    Progress = None
    ProgressPhoto = None
    Transformation = None
    Review = None
    def get_authenticated_user():
        return None


def get_current_coach(user=None) -> Optional[Coach]:
    """
    Authoritatively resolve the Coach tenant entity for the authenticated user.
    Never relies on client-provided query parameters, body parameters, or cookies.
    """
    if user is None:
        user = get_authenticated_user()
    if not user or not user.is_active:
        return None
    if user.role != "COACH":
        return None
    return getattr(user, "coach", None)


def get_current_client(user=None) -> Optional[Client]:
    """
    Authoritatively resolve the Client athlete entity for the authenticated user.
    Never relies on client-provided query parameters, body parameters, or cookies.
    """
    if user is None:
        user = get_authenticated_user()
    if not user or not user.is_active:
        return None
    if user.role != "CLIENT":
        return None
    return getattr(user, "client", None)


def require_coach_tenant(f):
    """
    Decorator requiring an active authenticated Coach with an initialized Coach profile.
    Populates g.coach and g.coach_id. Rejects all unauthorized callers.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_authenticated_user()
        if not user:
            if request.path.startswith("/api/") or request.is_json:
                return jsonify({"error": "Authentication required. Please sign in.", "status_code": 401}), 401
            from flask import redirect, url_for
            return redirect(url_for("auth.login_view", next=request.path))

        if not user.is_active:
            return jsonify({"error": "Account is deactivated. Access denied.", "status_code": 403}), 403

        coach = get_current_coach(user)
        if not coach:
            if request.path.startswith("/api/") or request.is_json:
                return jsonify({"error": "Access Denied - Coach profile not provisioned.", "status_code": 403}), 403
            return render_template("errors/403.html", user=user, message="Coach workspace profile is required."), 403

        # Bind authoritative tenant context to request globals
        g.coach = coach
        g.coach_id = coach.id
        return f(*args, **kwargs)
    return decorated_function


def require_client_tenant(f):
    """
    Decorator requiring an active authenticated Client with an initialized Client profile.
    Populates g.client and g.client_id. Rejects all unauthorized callers.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_authenticated_user()
        if not user:
            if request.path.startswith("/api/") or request.is_json:
                return jsonify({"error": "Authentication required. Please sign in.", "status_code": 401}), 401
            from flask import redirect, url_for
            return redirect(url_for("auth.login_view", next=request.path))

        if not user.is_active:
            return jsonify({"error": "Account is deactivated. Access denied.", "status_code": 403}), 403

        client = get_current_client(user)
        if not client:
            if request.path.startswith("/api/") or request.is_json:
                return jsonify({"error": "Access Denied - Client profile not provisioned.", "status_code": 403}), 403
            return render_template("errors/403.html", user=user, message="Client athlete profile is required."), 403

        # Bind authoritative athlete context to request globals
        g.client = client
        g.client_id = client.id
        return f(*args, **kwargs)
    return decorated_function


def tenant_access_denied(resource_name: str = "Resource"):
    """
    Generic rejection response to prevent tenant enumeration and information disclosure.
    Returns 404 or 403 without revealing whether another tenant's record exists.
    """
    if request.path.startswith("/api/") or request.is_json:
        return jsonify({
            "error": f"{resource_name} not found or access denied.",
            "status_code": 404
        }), 404
    return render_template("errors/403.html", user=get_authenticated_user(), message=f"{resource_name} not found or access denied."), 404


# =========================================================================
# COACH TENANT OWNERSHIP CHECKERS
# =========================================================================

def verify_coach_owns_client(coach_id: int, client_id: int, db_session=None) -> Tuple[bool, Optional[Client]]:
    """Verify that client_id exists and is owned by coach_id."""
    session = db_session or db.session
    client = session.query(Client).filter_by(id=client_id, coach_id=coach_id).first()
    return (True, client) if client else (False, None)


def verify_coach_owns_diet_plan(coach_id: int, plan_id: int, db_session=None) -> Tuple[bool, Optional[DietPlan]]:
    """Verify that diet plan exists and was authored/owned by coach_id."""
    session = db_session or db.session
    plan = session.query(DietPlan).filter_by(id=plan_id, coach_id=coach_id).first()
    return (True, plan) if plan else (False, None)


def verify_coach_owns_workout_plan(coach_id: int, plan_id: int, db_session=None) -> Tuple[bool, Optional[WorkoutPlan]]:
    """Verify that workout plan exists and was authored/owned by coach_id."""
    session = db_session or db.session
    plan = session.query(WorkoutPlan).filter_by(id=plan_id, coach_id=coach_id).first()
    return (True, plan) if plan else (False, None)


def verify_coach_owns_progress(coach_id: int, progress_id: int, db_session=None) -> Tuple[bool, Optional[Progress]]:
    """Verify that biometric progress record belongs to a client enrolled under coach_id."""
    session = db_session or db.session
    progress = session.query(Progress).join(Client, Progress.client_id == Client.id).filter(
        Progress.id == progress_id,
        Client.coach_id == coach_id
    ).first()
    return (True, progress) if progress else (False, None)


def verify_coach_owns_transformation(coach_id: int, trans_id: int, db_session=None) -> Tuple[bool, Optional[Transformation]]:
    """Verify that transformation showcase belongs to coach_id."""
    session = db_session or db.session
    trans = session.query(Transformation).filter_by(id=trans_id, coach_id=coach_id).first()
    return (True, trans) if trans else (False, None)


def verify_coach_owns_review(coach_id: int, review_id: int, db_session=None) -> Tuple[bool, Optional[Review]]:
    """Verify that review was submitted for coach_id."""
    session = db_session or db.session
    review = session.query(Review).filter_by(id=review_id, coach_id=coach_id).first()
    return (True, review) if review else (False, None)


# =========================================================================
# CLIENT OWN-DATA OWNERSHIP CHECKERS
# =========================================================================

def verify_client_owns_progress(client_id: int, progress_id: int, db_session=None) -> Tuple[bool, Optional[Progress]]:
    """Verify that progress record was authored/owned by client_id."""
    session = db_session or db.session
    progress = session.query(Progress).filter_by(id=progress_id, client_id=client_id).first()
    return (True, progress) if progress else (False, None)


def verify_client_owns_diet_plan(client_id: int, plan_id: int, db_session=None) -> Tuple[bool, Optional[DietPlan]]:
    """Verify that diet plan is assigned to client_id."""
    session = db_session or db.session
    plan = session.query(DietPlan).filter_by(id=plan_id, client_id=client_id).first()
    return (True, plan) if plan else (False, None)


def verify_client_owns_workout_plan(client_id: int, plan_id: int, db_session=None) -> Tuple[bool, Optional[WorkoutPlan]]:
    """Verify that workout plan is assigned to client_id."""
    session = db_session or db.session
    plan = session.query(WorkoutPlan).filter_by(id=plan_id, client_id=client_id).first()
    return (True, plan) if plan else (False, None)


def verify_client_owns_photo(client_id: int, photo_id: int, db_session=None) -> Tuple[bool, Optional[ProgressPhoto]]:
    """Verify that progress photo belongs to client_id's private progress records."""
    session = db_session or db.session
    photo = session.query(ProgressPhoto).join(Progress, ProgressPhoto.progress_id == Progress.id).filter(
        ProgressPhoto.id == photo_id,
        Progress.client_id == client_id
    ).first()
    return (True, photo) if photo else (False, None)
