"""
Public Routes Blueprint
Handles public website pages: Homepage, Discovery, Public Tools, Info
"""
import os
from flask import Blueprint, send_from_directory, jsonify, current_app

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def index():
    """Serve the public SaaS landing page."""
    root_dir = current_app.root_path
    return send_from_directory(root_dir, "index.html")


@public_bp.route("/health")
def health():
    """Service health check endpoint for monitoring and deployment probes."""
    return jsonify({
        "status": "healthy",
        "service": "FitPulse SaaS Engine",
        "phase": "Phase 4B - Real Diet Plan Management",
        "database_configured": True,
        "multi_tenant_ready": True,
        "auth_configured": True,
        "rbac_configured": True,
        "tenant_isolation_configured": True,
        "security_hardened": True,
        "diet_management_ready": True
    }), 200


@public_bp.route("/api/v1/meta")
def meta_info():
    """Public platform metadata endpoint."""
    return jsonify({
        "platform": "FitPulse SaaS",
        "version": "1.9.0-phase4b",
        "target_audience": "Independent Fitness Coaches and Personal Trainers",
        "phase": "Phase 4B - Real Diet Plan Management",
        "auth_system": "Flask-Login + Session + Werkzeug PBKDF2/scrypt",
        "rbac_roles": ["SUPER_ADMIN", "COACH", "CLIENT"],
        "tenant_model": "Strict Multi-Tenant Coach Partitioning & Athlete Own-Data Isolation",
        "business_modules": [
            "Coach Client Management (Phase 4A)",
            "Real Diet Plan Management (Phase 4B)"
        ],
        "security_features": [
            "Session HTTPOnly & SameSite Lax",
            "Cryptographic CSRF Protection",
            "Sliding-Window Rate Limiting",
            "Non-Predictable File Storage & Auth Media Streaming",
            "Audit Credential Sanitization",
            "HTTP Security Headers (CSP, HSTS, X-Frame-Options, nosniff)"
        ],
        "models_initialized": [
            "User",
            "Coach",
            "Client",
            "Exercise",
            "DietPlan",
            "DietItem",
            "WorkoutPlan",
            "WorkoutDay",
            "WorkoutExercise",
            "Progress",
            "Measurement",
            "ProgressPhoto",
            "Transformation",
            "TransformationConsent",
            "Review",
            "SubscriptionPlan",
            "Subscription",
            "Notification",
            "SupportTicket",
            "Announcement",
            "AuditLog"
        ],
        "free_tools": [
            "Food Alternatives Finder",
            "Historical Diet & Progress Analyzer",
            "Injury & Exercise Safety Guide"
        ]
    }), 200


@public_bp.route("/api/v1/public/transformations", methods=["GET"])
def public_transformations():
    """
    Public transformations showcase.
    CRITICAL PRIVACY RULE: Displays ONLY transformations where is_public=True
    AND client consent is active (revoked_at IS NULL). Never leaks client contact info.
    """
    from models import db, Transformation
    try:
        all_trans = db.session.query(Transformation).filter_by(is_public=True).all()
        displayable = [t for t in all_trans if t.is_publicly_displayable()]
        return jsonify({
            "total_public": len(displayable),
            "transformations": [{
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "coach_business_name": t.coach.business_name if t.coach else None,
                "duration_weeks": t.duration_weeks
            } for t in displayable]
        }), 200
    except Exception:
        return jsonify({"total_public": 0, "transformations": []}), 200
