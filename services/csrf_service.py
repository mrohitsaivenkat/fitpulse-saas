"""
FitPulse SaaS - CSRF Protection Service (Phase 3D)
Provides cryptographically secure Cross-Site Request Forgery (CSRF) protection:
- Token generation using secrets.token_urlsafe(32) tied to user session.
- Constant-time comparison via hmac.compare_digest to prevent timing attacks.
- Supports both HTML form submissions (csrf_token field) and AJAX/JSON API requests (X-CSRF-Token / X-CSRFToken headers).
- Safe exemptions for read-only idempotent methods (GET, HEAD, OPTIONS).
"""
import secrets
import hmac
from typing import Optional
from functools import wraps

try:
    from flask import request, session, jsonify, render_template, current_app, g
    _HAS_FLASK = True
except ImportError:
    _HAS_FLASK = False
    request = None
    session = {}
    jsonify = None
    render_template = None
    current_app = None
    g = None


CSRF_SESSION_KEY = "_csrf_token"
CSRF_HEADER_NAMES = ("X-CSRF-Token", "X-CSRFToken", "X-XSRF-Token")


def generate_csrf_token() -> str:
    """
    Generate or retrieve a cryptographically secure CSRF token for the active session.
    Token is stored in session and reused across requests until invalidated.
    """
    if not _HAS_FLASK or session is None:
        return secrets.token_urlsafe(32)

    token = session.get(CSRF_SESSION_KEY)
    if not token or not isinstance(token, str):
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token


def validate_csrf_token(provided_token: Optional[str] = None) -> bool:
    """
    Validate a provided CSRF token against the token stored in the session.
    Uses constant-time comparison to prevent timing side-channel attacks.
    """
    if not _HAS_FLASK or session is None:
        return True

    expected_token = session.get(CSRF_SESSION_KEY)
    if not expected_token or not isinstance(expected_token, str):
        return False

    if not provided_token and request:
        # 1. Check form payload
        if request.form and "csrf_token" in request.form:
            provided_token = request.form.get("csrf_token")
        # 2. Check JSON payload
        elif request.is_json and request.json and isinstance(request.json, dict) and "csrf_token" in request.json:
            provided_token = request.json.get("csrf_token")
        # 3. Check HTTP headers
        else:
            for header_name in CSRF_HEADER_NAMES:
                val = request.headers.get(header_name)
                if val:
                    provided_token = val
                    break

    if not provided_token or not isinstance(provided_token, str):
        return False

    return hmac.compare_digest(expected_token, provided_token)


def csrf_protect_required(f):
    """
    Route decorator explicitly enforcing CSRF token validation.
    Applies to state-changing operations (POST, PUT, PATCH, DELETE).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not _HAS_FLASK:
            return f(*args, **kwargs)

        # Allow idempotent safe methods
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return f(*args, **kwargs)

        # Check if testing config disables CSRF
        if current_app and current_app.config.get("WTF_CSRF_ENABLED") is False:
            return f(*args, **kwargs)

        if not validate_csrf_token():
            if request.path.startswith("/api/") or request.is_json:
                return jsonify({
                    "error": "CSRF validation failed. Missing or invalid CSRF token.",
                    "status_code": 403
                }), 403
            return jsonify({
                "error": "Session security verification failed. Please refresh the page and try again.",
                "status_code": 403
            }), 403

        return f(*args, **kwargs)
    return decorated_function


def init_csrf_app(app):
    """
    Initialize CSRF protections with the Flask application.
    Injects csrf_token() into Jinja template rendering contexts.
    """
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf_token)
