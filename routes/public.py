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
        "phase": "Phase 2B - Exercise, Diet & Workout Database Models",
        "database_configured": True,
        "multi_tenant_ready": True
    }), 200


@public_bp.route("/api/v1/meta")
def meta_info():
    """Public platform metadata endpoint."""
    return jsonify({
        "platform": "FitPulse SaaS",
        "version": "1.2.0-phase2b",
        "target_audience": "Independent Fitness Coaches and Personal Trainers",
        "phase": "Phase 2B - Exercise, Diet & Workout Database Models",
        "models_initialized": [
            "User",
            "Coach",
            "Client",
            "Exercise",
            "DietPlan",
            "DietItem",
            "WorkoutPlan",
            "WorkoutDay",
            "WorkoutExercise"
        ],
        "free_tools": [
            "Food Alternatives Finder",
            "Historical Diet & Progress Analyzer",
            "Injury & Exercise Safety Guide"
        ]
    }), 200
