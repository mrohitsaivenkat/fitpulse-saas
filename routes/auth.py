"""
FitPulse SaaS - Authentication Routes Blueprint
Implements login, logout, registration, and authenticated user state verification.
Supports standard HTML form workflows and JSON REST API requests.
"""
from datetime import datetime, timezone
from flask import Blueprint, request, render_template, redirect, url_for, jsonify, session, current_app
from sqlalchemy.sql import func
from models import db, User, Coach
from services.auth_service import authenticate_user, register_coach_account, normalize_email, get_post_login_redirect
from services.auth_decorators import login_required, get_authenticated_user
from services.rate_limiter import rate_limit
from services.csrf_service import validate_csrf_token

# Try importing Flask-Login
try:
    from flask_login import login_user, logout_user, current_user
    _HAS_FLASK_LOGIN = True
except ImportError:
    _HAS_FLASK_LOGIN = False

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
@rate_limit(max_requests=15, window_seconds=60)
def login_view():
    """
    User login endpoint.
    GET: Renders login page.
    POST: Verifies credentials, sets session, and updates last_login_at.
    """
    # If user is already authenticated, redirect to home
    current = get_authenticated_user()
    if current:
        if request.is_json:
            return jsonify({"message": "Already authenticated", "user": current.to_dict()}), 200
        return redirect(url_for("public.index"))

    if request.method == "POST":
        # Validate CSRF for standard HTML form posts (when enabled)
        if not request.is_json and current_app.config.get("WTF_CSRF_ENABLED", True):
            form_token = request.form.get("csrf_token")
            if form_token and not validate_csrf_token(form_token):
                return render_template("login.html", error="Security token expired. Please try again."), 403

        # Extract payload (supports both JSON and HTML form post)
        if request.is_json:
            data = request.get_json() or {}
            email = data.get("email", "")
            password = data.get("password", "")
            remember = bool(data.get("remember", False))
        else:
            email = request.form.get("email", "")
            password = request.form.get("password", "")
            remember = bool(request.form.get("remember", False))

        user, error = authenticate_user(db.session, User, email, password)

        if error or not user:
            if request.is_json:
                return jsonify({"error": error or "Invalid credentials.", "status_code": 401}), 401
            return render_template("login.html", error=error or "Invalid email or password.", email=email)

        # Update last_login_at timestamp
        user.last_login_at = datetime.now(timezone.utc)
        db.session.commit()

        # Establish session state
        session.clear()
        session["user_id"] = user.id
        session["user_role"] = user.role
        session["user_name"] = user.full_name
        session.permanent = remember

        if _HAS_FLASK_LOGIN:
            try:
                login_user(user, remember=remember)
            except Exception:
                pass

        # Safe role-based redirect handling (prevent open redirect vulnerabilities)
        requested_target = request.args.get("next") or (request.form.get("next") if not request.is_json else None)
        next_page = get_post_login_redirect(user, requested_target)

        if request.is_json:
            return jsonify({
                "success": True,
                "message": "Authentication successful.",
                "redirect_url": next_page,
                "user": user.to_dict()
            }), 200

        return redirect(next_page)

    # GET request
    registered = request.args.get("registered") == "1"
    logged_out = request.args.get("logged_out") == "1"
    return render_template("login.html", registered=registered, logged_out=logged_out)


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout_view():
    """
    Terminate authenticated session and clean up state.
    """
    session.clear()

    if _HAS_FLASK_LOGIN:
        try:
            logout_user()
        except Exception:
            pass

    if request.is_json:
        return jsonify({"success": True, "message": "Successfully logged out."}), 200

    return redirect(url_for("auth.login_view", logged_out=1))


@auth_bp.route("/register", methods=["GET", "POST"])
@auth_bp.route("/register/coach", methods=["GET", "POST"])
@rate_limit(max_requests=10, window_seconds=60)
def register_view():
    """
    Coach workspace registration endpoint.
    Creates User with strictly enforced COACH role and associated Coach entity.
    """
    current = get_authenticated_user()
    if current:
        return redirect(url_for("public.index"))

    if request.method == "POST":
        # Validate CSRF for standard HTML form posts (when enabled)
        if not request.is_json and current_app.config.get("WTF_CSRF_ENABLED", True):
            form_token = request.form.get("csrf_token")
            if form_token and not validate_csrf_token(form_token):
                return render_template("register.html", error="Security token expired. Please try again."), 403

        if request.is_json:
            data = request.get_json() or {}
            email = data.get("email", "")
            password = data.get("password", "")
            first_name = data.get("first_name", "")
            last_name = data.get("last_name", "")
            business_name = data.get("business_name", "")
            phone = data.get("phone", "")
            specialization = data.get("specialization", "")
        else:
            email = request.form.get("email", "")
            password = request.form.get("password", "")
            first_name = request.form.get("first_name", "")
            last_name = request.form.get("last_name", "")
            business_name = request.form.get("business_name", "")
            phone = request.form.get("phone", "")
            specialization = request.form.get("specialization", "")

        user, error = register_coach_account(
            db_session=db.session,
            UserModel=User,
            CoachModel=Coach,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            business_name=business_name,
            phone=phone,
            specialization=specialization
        )

        if error or not user:
            if request.is_json:
                return jsonify({"error": error, "status_code": 400}), 400
            return render_template(
                "register.html",
                error=error,
                email=email,
                first_name=first_name,
                last_name=last_name,
                business_name=business_name,
                phone=phone,
                specialization=specialization
            )

        if request.is_json:
            return jsonify({
                "success": True,
                "message": "Coach account created successfully.",
                "user": user.to_dict()
            }), 201

        return redirect(url_for("auth.login_view", registered=1))

    # GET request
    return render_template("register.html")


@auth_bp.route("/api/v1/auth/me", methods=["GET"])
@login_required
def get_current_user_profile():
    """
    Protected API endpoint to verify active session and inspect current user profile.
    """
    user = get_authenticated_user()
    return jsonify({
        "authenticated": True,
        "user": user.to_dict()
    }), 200
