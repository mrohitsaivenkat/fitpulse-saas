"""
FitPulse SaaS - Authentication Decorators
Provides reusable access-control helpers:
- login_required: Enforces authenticated session.
- active_user_required: Enforces active account status.
Compatible with Flask-Login and session-based authentication.
"""
from functools import wraps

try:
    from flask import request, redirect, url_for, jsonify, session, g
    _HAS_FLASK = True
except ImportError:
    _HAS_FLASK = False
    request = None
    redirect = None
    url_for = None
    jsonify = None
    session = {}
    g = None

try:
    from models import db, User
    _HAS_MODELS = True
except ImportError:
    _HAS_MODELS = False
    db = None
    User = None

# Try importing Flask-Login current_user
try:
    from flask_login import current_user
    _HAS_FLASK_LOGIN = True
except ImportError:
    _HAS_FLASK_LOGIN = False
    current_user = None


def get_authenticated_user():
    """Retrieve the currently authenticated user from Flask-Login or session."""
    if _HAS_FLASK_LOGIN and current_user and current_user.is_authenticated:
        return current_user

    # Fallback to session user_id lookup
    user_id = session.get("user_id")
    if user_id:
        if not hasattr(g, "_cached_user"):
            g._cached_user = db.session.query(User).filter_by(id=user_id).first()
        return g._cached_user
    return None


def login_required(f):
    """
    Decorator requiring an active authenticated user session.
    Returns JSON 401 for API requests, redirects to /login for browser requests.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_authenticated_user()
        if not user:
            if request.path.startswith("/api/") or request.is_json:
                return jsonify({"error": "Authentication required. Please log in.", "status_code": 401}), 401
            return redirect(url_for("auth.login_view", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def active_user_required(f):
    """
    Decorator requiring that the authenticated user's account is currently active.
    Returns JSON 403 or redirects to deactivated account notice.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_authenticated_user()
        if not user:
            if request.path.startswith("/api/") or request.is_json:
                return jsonify({"error": "Authentication required.", "status_code": 401}), 401
            return redirect(url_for("auth.login_view", next=request.path))

        if not user.is_active:
            if request.path.startswith("/api/") or request.is_json:
                return jsonify({"error": "Account is deactivated. Access denied.", "status_code": 403}), 403
            return jsonify({"error": "Your account has been deactivated. Please contact support.", "status_code": 403}), 403

        return f(*args, **kwargs)
    return decorated_function


def roles_required(*allowed_roles):
    """
    Authoritative server-side Role-Based Access Control (RBAC) decorator.
    Enforces that the authenticated user possesses one of the allowed roles.
    Rejects:
    - Unauthenticated callers -> Redirects to /login (or HTTP 401 JSON)
    - Inactive accounts -> HTTP 403
    - Unauthorized roles -> HTTP 403 Forbidden
    Never trusts client-provided inputs, URL params, or cookies.
    """
    # Normalize expected role string names
    normalized_roles = set()
    for r in allowed_roles:
        if hasattr(r, "value"):
            normalized_roles.add(str(r.value).upper())
        else:
            normalized_roles.add(str(r).upper())

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_authenticated_user()
            if not user:
                if request.path.startswith("/api/") or request.is_json:
                    return jsonify({"error": "Authentication required. Please log in.", "status_code": 401}), 401
                return redirect(url_for("auth.login_view", next=request.path))

            if not user.is_active:
                if request.path.startswith("/api/") or request.is_json:
                    return jsonify({"error": "Account is deactivated. Access denied.", "status_code": 403}), 403
                return jsonify({"error": "Your account has been deactivated.", "status_code": 403}), 403

            # Authoritative server-side role check from database
            user_role = str(user.role).upper() if user.role else ""
            if user_role not in normalized_roles:
                if request.path.startswith("/api/") or request.is_json:
                    return jsonify({
                        "error": "Access Denied - Insufficient role permissions.",
                        "status_code": 403
                    }), 403
                try:
                    from flask import render_template
                    return render_template("errors/403.html", user=user), 403
                except Exception:
                    return jsonify({"error": "Access Denied - Forbidden", "status_code": 403}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Convenience aliases for common RBAC policies
role_required = roles_required


def admin_required(f):
    """Restricts route exclusively to platform SUPER_ADMIN users."""
    return roles_required("SUPER_ADMIN")(f)


def coach_required(f):
    """Restricts route to COACH users (with SUPER_ADMIN oversight allowed)."""
    return roles_required("COACH", "SUPER_ADMIN")(f)


def client_required(f):
    """Restricts route to CLIENT users (with SUPER_ADMIN oversight allowed)."""
    return roles_required("CLIENT", "SUPER_ADMIN")(f)


def strict_coach_only(f):
    """Strictly coach-only; disallows even SUPER_ADMIN."""
    return roles_required("COACH")(f)


def strict_client_only(f):
    """Strictly client-only; disallows coaches and admins."""
    return roles_required("CLIENT")(f)

