"""
Public Routes Blueprint
Handles public website pages: Homepage, Discovery, Public Tools, Info
"""
from flask import Blueprint, render_template, jsonify

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def index():
    """Render the public SaaS landing page."""
    return render_template("public/index.html")


@public_bp.route("/health")
def health():
    """Service health check endpoint for cloud monitoring and deployment probes."""
    return jsonify({
        "status": "healthy",
        "service": "FitPulse SaaS Engine",
        "phase": "Phase 1 - Foundation & Landing Architecture",
        "multi_tenant_ready": True
    }), 200


@public_bp.route("/api/v1/meta")
def meta_info():
    """Public platform metadata endpoint."""
    return jsonify({
        "platform": "FitPulse SaaS",
        "version": "1.0.0-phase1",
        "target_audience": "Independent Fitness Coaches and Personal Trainers",
        "free_tools": [
            "Food Alternatives Finder",
            "Historical Diet & Progress Analyzer",
            "Injury & Exercise Safety Guide"
        ]
    }), 200
