"""
FitPulse SaaS - Client Routes (Phase 3C Multi-Tenant Isolated)
Strictly enforces own-data client isolation:
- A client can access ONLY their own personal profile, diet plans, workout plans,
  biometrics, and progress logs.
- Attempting to inspect or modify another athlete's data via URL parameter or payload manipulation
  is blocked with a non-disclosing 404/403 response.
- All biometric/progress creations authoritatively force client_id = authenticated_client.id.
- Clients can NEVER modify their assigned coach_id.
"""
from datetime import date
from flask import Blueprint, render_template, jsonify, request, g
from models import db, Client, DietPlan, WorkoutPlan, Progress
from services.auth_decorators import get_authenticated_user
from services.tenant_service import (
    require_client_tenant,
    verify_client_owns_progress,
    verify_client_owns_diet_plan,
    verify_client_owns_workout_plan,
    tenant_access_denied
)
from services.diet_service import compute_diet_plan_nutrition, group_diet_items_by_meal

client_bp = Blueprint("client", __name__, url_prefix="/client")


# =========================================================================
# ATHLETE PORTAL OVERVIEW
# =========================================================================

@client_bp.route("", methods=["GET"])
@client_bp.route("/portal", methods=["GET"])
@require_client_tenant
def client_portal():
    """Client Athlete Portal Overview."""
    user = get_authenticated_user()
    if request.is_json or request.headers.get("Accept") == "application/json":
        coach = g.client.coach
        return jsonify({
            "message": "Welcome to Client Portal.",
            "role": user.role,
            "client_id": g.client_id,
            "client_name": user.full_name,
            "coach_business_name": coach.business_name if coach else None,
            "goal": g.client.goal
        }), 200

    return render_template("client_portal.html", user=user, client=g.client)


@client_bp.route("/api/v1/my-portal", methods=["GET"])
@require_client_tenant
def api_client_summary():
    """Summary metrics strictly partitioned to current client."""
    user = get_authenticated_user()
    coach = g.client.coach

    diet_count = db.session.query(DietPlan).filter_by(client_id=g.client_id).count()
    workout_count = db.session.query(WorkoutPlan).filter_by(client_id=g.client_id).count()
    progress_count = db.session.query(Progress).filter_by(client_id=g.client_id).count()

    return jsonify({
        "role_authorized": "CLIENT",
        "client_id": g.client_id,
        "client_email": user.email,
        "client_name": user.full_name,
        "goal": g.client.goal or "General Fitness",
        "coach_business_name": coach.business_name if coach else None,
        "summary": {
            "assigned_diets": diet_count,
            "assigned_workouts": workout_count,
            "logged_progress_entries": progress_count
        }
    }), 200


# =========================================================================
# PROFILE MANAGEMENT (IMMUTABLE COACH ASSIGNMENT)
# =========================================================================

@client_bp.route("/profile", methods=["GET", "PUT", "PATCH"])
@client_bp.route("/api/v1/profile", methods=["GET", "PUT", "PATCH"])
@require_client_tenant
def client_profile():
    """
    GET: View own profile.
    PUT/PATCH: Update personal biometrics/goals.
    CRITICAL SECURITY GUARANTEE: coach_id and user_id are strictly immutable.
    """
    if request.method in ("PUT", "PATCH"):
        data = request.get_json() if request.is_json else request.form.to_dict()
        if "goal" in data:
            g.client.goal = data["goal"].strip()
        if "height" in data:
            g.client.height = float(data["height"])
        if "current_weight" in data:
            g.client.current_weight = float(data["current_weight"])
        
        # Explicitly IGNORE any attempt to alter coach_id or user_id
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Profile updated successfully.",
            "profile": g.client.to_dict()
        }), 200

    return jsonify({
        "success": True,
        "profile": g.client.to_dict()
    }), 200


# =========================================================================
# ASSIGNED DIET PLANS (OWN-DATA ISOLATED)
# =========================================================================

@client_bp.route("/diets", methods=["GET"])
@client_bp.route("/api/v1/diets", methods=["GET"])
@require_client_tenant
def my_diets():
    """List only diet plans assigned to current client."""
    plans = db.session.query(DietPlan).filter_by(client_id=g.client_id).order_by(DietPlan.created_at.desc()).all()

    if request.is_json or request.headers.get("Accept") == "application/json":
        return jsonify({
            "client_id": g.client_id,
            "total_diet_plans": len(plans),
            "diet_plans": [p.to_dict(include_items=True) for p in plans]
        }), 200

    user = get_authenticated_user()
    return render_template(
        "client_diets.html",
        user=user,
        client=g.client,
        coach=g.client.coach,
        plans=plans
    )


@client_bp.route("/diets/<int:plan_id>", methods=["GET"])
@client_bp.route("/api/v1/diets/<int:plan_id>", methods=["GET"])
@require_client_tenant
def my_diet_detail(plan_id: int):
    """View assigned diet plan. Rejects plans assigned to other clients."""
    is_owner, plan = verify_client_owns_diet_plan(g.client_id, plan_id)
    if not is_owner or not plan:
        return tenant_access_denied("Diet Plan")

    nutrition = compute_diet_plan_nutrition(plan)
    grouped_meals = group_diet_items_by_meal(plan.items)

    if request.is_json or request.headers.get("Accept") == "application/json":
        return jsonify({
            "success": True,
            "diet_plan": plan.to_dict(include_items=True),
            "nutrition": nutrition
        }), 200

    user = get_authenticated_user()
    return render_template(
        "client_diet_detail.html",
        user=user,
        client=g.client,
        coach=g.client.coach,
        plan=plan,
        nutrition=nutrition,
        grouped_meals=grouped_meals
    )


# =========================================================================
# ASSIGNED WORKOUT PLANS (OWN-DATA ISOLATED)
# =========================================================================

@client_bp.route("/workouts", methods=["GET"])
@client_bp.route("/api/v1/workouts", methods=["GET"])
@require_client_tenant
def my_workouts():
    """List only workout plans assigned to current client."""
    plans = db.session.query(WorkoutPlan).filter_by(client_id=g.client_id).all()
    return jsonify({
        "client_id": g.client_id,
        "total_workout_plans": len(plans),
        "workout_plans": [p.to_dict() for p in plans]
    }), 200


@client_bp.route("/workouts/<int:plan_id>", methods=["GET"])
@client_bp.route("/api/v1/workouts/<int:plan_id>", methods=["GET"])
@require_client_tenant
def my_workout_detail(plan_id: int):
    """View assigned workout plan. Rejects plans assigned to other clients."""
    is_owner, plan = verify_client_owns_workout_plan(g.client_id, plan_id)
    if not is_owner or not plan:
        return tenant_access_denied("Workout Plan")

    return jsonify({
        "success": True,
        "workout_plan": plan.to_dict()
    }), 200


# =========================================================================
# BIOMETRICS & PROGRESS LOGS (OWN-DATA ISOLATED)
# =========================================================================

@client_bp.route("/progress", methods=["GET", "POST"])
@client_bp.route("/api/v1/progress", methods=["GET", "POST"])
@require_client_tenant
def manage_progress():
    """
    GET: List own progress logs.
    POST: Log new biometric entry (authoritatively sets client_id = current_client.id).
    """
    if request.method == "POST":
        data = request.get_json() if request.is_json else request.form.to_dict()
        weight = float(data.get("weight", 0.0))
        if weight <= 0:
            return jsonify({"error": "Valid positive weight is required.", "status_code": 400}), 400

        # Authoritatively assign client_id to current authenticated client
        new_progress = Progress(
            client_id=g.client_id,  # Immutable server-side assignment
            weight=weight,
            body_fat_percentage=float(data.get("body_fat_percentage")) if data.get("body_fat_percentage") else None,
            muscle_mass=float(data.get("muscle_mass")) if data.get("muscle_mass") else None,
            waist=float(data.get("waist")) if data.get("waist") else None,
            chest=float(data.get("chest")) if data.get("chest") else None,
            notes=data.get("notes")
        )
        db.session.add(new_progress)
        db.session.commit()

        # Keep client profile current_weight in sync
        g.client.current_weight = weight
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Biometric progress entry logged.",
            "progress": new_progress.to_dict()
        }), 201

    records = db.session.query(Progress).filter_by(client_id=g.client_id).order_by(Progress.date.desc()).all()
    return jsonify({
        "client_id": g.client_id,
        "total_records": len(records),
        "progress_records": [p.to_dict() for p in records]
    }), 200


@client_bp.route("/progress/<int:progress_id>", methods=["GET", "DELETE"])
@client_bp.route("/api/v1/progress/<int:progress_id>", methods=["GET", "DELETE"])
@require_client_tenant
def progress_detail(progress_id: int):
    """View or delete own progress entry. Rejects cross-client access."""
    is_owner, progress = verify_client_owns_progress(g.client_id, progress_id)
    if not is_owner or not progress:
        return tenant_access_denied("Progress Entry")

    if request.method == "DELETE":
        db.session.delete(progress)
        db.session.commit()
        return jsonify({"success": True, "message": "Progress entry deleted."}), 200

    return jsonify({
        "success": True,
        "progress": progress.to_dict()
    }), 200
