"""
FitPulse SaaS - Super Admin Routes (Phase 3B)
Protected exclusively for users with the SUPER_ADMIN role.
Rejects COACH and CLIENT roles with HTTP 403 Forbidden.
"""
from flask import Blueprint, render_template, jsonify, request
from services.auth_decorators import admin_required, get_authenticated_user
from models import db, User, Coach, Client, Subscription, SupportTicket, AuditLog

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("", methods=["GET"])
@admin_bp.route("/overview", methods=["GET"])
@admin_required
def admin_overview():
    """
    Platform Administration Overview.
    Accessible ONLY to users with SUPER_ADMIN role.
    """
    user = get_authenticated_user()
    if request.is_json or request.headers.get("Accept") == "application/json":
        return jsonify({
            "message": "Welcome to FitPulse Platform Administration.",
            "role": user.role,
            "admin_name": user.full_name
        }), 200

    return render_template("admin_overview.html", user=user)


@admin_bp.route("/api/v1/overview", methods=["GET"])
@admin_required
def api_admin_overview():
    """
    Super Admin API summary endpoint.
    Returns high-level system telemetry counts.
    """
    user = get_authenticated_user()
    try:
        user_count = db.session.query(User).count()
        coach_count = db.session.query(Coach).count()
        client_count = db.session.query(Client).count()
        subscription_count = db.session.query(Subscription).count()
        ticket_count = db.session.query(SupportTicket).count()
        audit_count = db.session.query(AuditLog).count()
    except Exception:
        user_count = coach_count = client_count = subscription_count = ticket_count = audit_count = 0

    return jsonify({
        "platform": "FitPulse SaaS",
        "role_authorized": "SUPER_ADMIN",
        "admin_user": user.email,
        "metrics": {
            "total_users": user_count,
            "total_coaches": coach_count,
            "total_clients": client_count,
            "total_subscriptions": subscription_count,
            "total_support_tickets": ticket_count,
            "total_audit_logs": audit_count
        }
    }), 200
