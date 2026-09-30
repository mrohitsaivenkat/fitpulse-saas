"""
FitPulse SaaS - Coach Routes (Phase 3C Multi-Tenant Isolated)
Strictly enforces tenant isolation:
- A coach can access ONLY their own clients, diet plans, workout plans, progress records,
  transformations, and reviews.
- Any attempt to access another coach's data via URL parameter or payload manipulation
  is blocked with a non-disclosing 404/403 response.
- All create operations force coach_id = authenticated_coach.id, discarding client input.
"""
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, g, current_app
from models import db, User, Coach, Client, DietPlan, WorkoutPlan, Progress, Transformation, Review
from services.auth_decorators import get_authenticated_user
from services.tenant_service import (
    require_coach_tenant,
    verify_coach_owns_client,
    verify_coach_owns_diet_plan,
    verify_coach_owns_workout_plan,
    verify_coach_owns_progress,
    verify_coach_owns_transformation,
    verify_coach_owns_review,
    tenant_access_denied
)
from services.client_service import (
    create_coach_client,
    update_coach_client,
    toggle_client_status,
    get_filtered_clients,
    validate_client_input
)
from services.diet_service import (
    create_diet_plan,
    update_diet_plan,
    toggle_diet_plan_status,
    delete_diet_plan,
    add_diet_item,
    update_diet_item,
    delete_diet_item,
    compute_diet_plan_nutrition,
    group_diet_items_by_meal,
    validate_diet_plan_input,
    validate_diet_item_input
)
from services.csrf_service import validate_csrf_token

coach_bp = Blueprint("coach", __name__, url_prefix="/coach")


# =========================================================================
# WORKSPACE OVERVIEW
# =========================================================================

@coach_bp.route("", methods=["GET"])
@coach_bp.route("/portal", methods=["GET"])
@require_coach_tenant
def coach_portal():
    """Coach Workspace Portal Overview."""
    user = get_authenticated_user()
    if request.is_json or request.headers.get("Accept") == "application/json":
        return jsonify({
            "message": "Welcome to Coach Workspace.",
            "role": user.role,
            "coach_id": g.coach_id,
            "coach_name": user.full_name,
            "business_name": g.coach.business_name
        }), 200

    return render_template("coach_portal.html", user=user, coach=g.coach)


@coach_bp.route("/api/v1/workspace-summary", methods=["GET"])
@require_coach_tenant
def api_workspace_summary():
    """Summary metrics strictly partitioned to current coach."""
    client_count = db.session.query(Client).filter_by(coach_id=g.coach_id).count()
    diet_count = db.session.query(DietPlan).filter_by(coach_id=g.coach_id).count()
    workout_count = db.session.query(WorkoutPlan).filter_by(coach_id=g.coach_id).count()

    return jsonify({
        "role_authorized": "COACH",
        "coach_id": g.coach_id,
        "coach_name": g.coach.user.full_name,
        "business_name": g.coach.business_name,
        "specialization": g.coach.specialization,
        "summary": {
            "active_clients": client_count,
            "diet_protocols": diet_count,
            "workout_blocks": workout_count
        }
    }), 200


# =========================================================================
# CLIENT ROSTER (TENANT ISOLATED - PHASE 4A)
# =========================================================================

@coach_bp.route("/clients", methods=["GET", "POST"])
@coach_bp.route("/api/v1/clients", methods=["GET", "POST"])
@require_coach_tenant
def manage_clients():
    """
    GET: List all clients strictly belonging to current coach with optional search/status filtering.
    POST: Enroll a new client under current coach (forces coach_id = current_coach.id).
    """
    user = get_authenticated_user()

    if request.method == "POST":
        # Check CSRF for form posts
        if not request.is_json and current_app.config.get("WTF_CSRF_ENABLED", True):
            token = request.form.get("csrf_token")
            if token and not validate_csrf_token(token):
                return jsonify({"error": "Security token expired. Please refresh.", "status_code": 403}), 403

        data = request.get_json() if request.is_json else request.form.to_dict()
        new_client, err = create_coach_client(g.coach_id, data, db.session)
        if err or not new_client:
            if request.is_json:
                return jsonify({"error": err or "Failed to create client.", "status_code": 400}), 400
            # For HTML post error, re-render roster with error
            all_clients = get_filtered_clients(g.coach_id, db_session=db.session)
            active_c = sum(1 for c in all_clients if c.is_active)
            return render_template(
                "coach_clients.html",
                user=user,
                coach=g.coach,
                clients=all_clients,
                active_count=active_c,
                inactive_count=len(all_clients) - active_c,
                error=err
            ), 400

        if request.is_json or request.headers.get("Accept") == "application/json":
            client_dict = new_client.to_dict()
            if new_client.user:
                client_dict["full_name"] = new_client.user.full_name
                client_dict["email"] = new_client.user.email
            return jsonify({
                "success": True,
                "message": "Client registered successfully.",
                "client": client_dict
            }), 201

        return redirect(url_for("coach.client_detail", client_id=new_client.id))

    # GET Request: Filter by search query and status
    search_q = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all").strip().lower()
    clients = get_filtered_clients(g.coach_id, q=search_q, status=status_filter, db_session=db.session)

    all_coach_clients = db.session.query(Client).filter_by(coach_id=g.coach_id).all()
    active_count = sum(1 for c in all_coach_clients if c.is_active)
    inactive_count = len(all_coach_clients) - active_count

    if request.is_json or request.headers.get("Accept") == "application/json":
        serialized = []
        for c in clients:
            cd = c.to_dict()
            if c.user:
                cd["full_name"] = c.user.full_name
                cd["email"] = c.user.email
                cd["phone"] = c.user.phone
            serialized.append(cd)
        return jsonify({
            "coach_id": g.coach_id,
            "total_clients": len(serialized),
            "clients": serialized
        }), 200

    return render_template(
        "coach_clients.html",
        user=user,
        coach=g.coach,
        clients=clients,
        active_count=active_count,
        inactive_count=inactive_count,
        search_query=search_q,
        current_status=status_filter
    )


@coach_bp.route("/clients/<int:client_id>", methods=["GET", "DELETE"])
@coach_bp.route("/api/v1/clients/<int:client_id>", methods=["GET", "DELETE"])
@require_coach_tenant
def client_detail(client_id: int):
    """
    GET: View client profile if and only if owned by this coach.
    DELETE: Remove client if and only if owned by this coach.
    """
    is_owner, client = verify_coach_owns_client(g.coach_id, client_id)
    if not is_owner or not client:
        return tenant_access_denied("Client")

    if request.method == "DELETE":
        db.session.delete(client)
        db.session.commit()
        return jsonify({"success": True, "message": "Client removed from your roster."}), 200

    if request.is_json or request.headers.get("Accept") == "application/json":
        cd = client.to_dict()
        if client.user:
            cd["full_name"] = client.user.full_name
            cd["first_name"] = client.user.first_name
            cd["last_name"] = client.user.last_name
            cd["email"] = client.user.email
            cd["phone"] = client.user.phone
            cd["user_active"] = client.user.is_active
        return jsonify({
            "success": True,
            "client": cd
        }), 200

    user = get_authenticated_user()
    return render_template("coach_client_profile.html", user=user, coach=g.coach, client=client)


@coach_bp.route("/clients/<int:client_id>/edit", methods=["POST", "PUT", "PATCH"])
@coach_bp.route("/api/v1/clients/<int:client_id>", methods=["PUT", "PATCH"])
@require_coach_tenant
def edit_client(client_id: int):
    """
    Update demographic, physical, and goal attributes for an owned client.
    Guarantees coach_id, user_id, and user role cannot be manipulated.
    """
    is_owner, client = verify_coach_owns_client(g.coach_id, client_id)
    if not is_owner or not client:
        return tenant_access_denied("Client")

    # Check CSRF for form posts
    if not request.is_json and current_app.config.get("WTF_CSRF_ENABLED", True):
        token = request.form.get("csrf_token")
        if token and not validate_csrf_token(token):
            return jsonify({"error": "Security token expired. Please refresh.", "status_code": 403}), 403

    data = request.get_json() if request.is_json else request.form.to_dict()
    updated_client, err = update_coach_client(g.coach_id, client_id, data, db.session)
    if err or not updated_client:
        return jsonify({"error": err or "Failed to update client.", "status_code": 400}), 400

    if request.is_json or request.headers.get("Accept") == "application/json":
        cd = updated_client.to_dict()
        if updated_client.user:
            cd["full_name"] = updated_client.user.full_name
            cd["email"] = updated_client.user.email
        return jsonify({
            "success": True,
            "message": "Client profile updated successfully.",
            "client": cd
        }), 200

    return redirect(url_for("coach.client_detail", client_id=client_id))


@coach_bp.route("/clients/<int:client_id>/toggle-status", methods=["POST"])
@coach_bp.route("/api/v1/clients/<int:client_id>/toggle-status", methods=["POST"])
@require_coach_tenant
def toggle_client_status_view(client_id: int):
    """
    Toggle a client's enrollment status (active <-> inactive).
    Preserves all historical logs and biometrics without deleting records.
    """
    is_owner, client = verify_coach_owns_client(g.coach_id, client_id)
    if not is_owner or not client:
        return tenant_access_denied("Client")

    # Check CSRF for form posts
    if not request.is_json and current_app.config.get("WTF_CSRF_ENABLED", True):
        token = request.form.get("csrf_token")
        if token and not validate_csrf_token(token):
            return jsonify({"error": "Security token expired. Please refresh.", "status_code": 403}), 403

    updated_client, err = toggle_client_status(g.coach_id, client_id, db.session)
    if err or not updated_client:
        return jsonify({"error": err or "Failed to toggle status.", "status_code": 400}), 400

    if request.is_json or request.headers.get("Accept") == "application/json":
        return jsonify({
            "success": True,
            "is_active": updated_client.is_active,
            "message": f"Client status updated to {'active' if updated_client.is_active else 'inactive'}."
        }), 200

    return redirect(url_for("coach.client_detail", client_id=client_id))


# =========================================================================
# DIET PLANS (TENANT ISOLATED - PHASE 4B)
# =========================================================================

@coach_bp.route("/diets", methods=["GET", "POST"])
@coach_bp.route("/api/v1/diets", methods=["GET", "POST"])
@require_coach_tenant
def manage_diets():
    """
    GET: List diet plans created by current coach with client and status filtering.
    POST: Create a diet plan for one of current coach's clients.
    """
    user = get_authenticated_user()

    if request.method == "POST":
        # Check CSRF for form posts
        if not request.is_json and current_app.config.get("WTF_CSRF_ENABLED", True):
            token = request.form.get("csrf_token")
            if token and not validate_csrf_token(token):
                return jsonify({"error": "Security token expired. Please refresh.", "status_code": 403}), 403

        data = request.get_json() if request.is_json else request.form.to_dict()
        try:
            client_id = int(data.get("client_id", 0))
        except (ValueError, TypeError):
            client_id = 0

        if not client_id:
            return jsonify({"error": "A valid client_id is required.", "status_code": 400}), 400

        new_plan, err = create_diet_plan(g.coach_id, client_id, data, db.session)
        if err or not new_plan:
            if request.is_json:
                return jsonify({"error": err or "Failed to create diet plan.", "status_code": 400}), 400
            # For HTML post error
            coach_clients = db.session.query(Client).filter_by(coach_id=g.coach_id).all()
            all_plans = db.session.query(DietPlan).filter_by(coach_id=g.coach_id).all()
            active_c = sum(1 for p in all_plans if p.is_active)
            return render_template(
                "coach_diets.html",
                user=user,
                coach=g.coach,
                plans=all_plans,
                clients=coach_clients,
                selected_client_id=client_id,
                active_count=active_c,
                inactive_count=len(all_plans) - active_c,
                error=err
            ), 400

        if request.is_json or request.headers.get("Accept") == "application/json":
            return jsonify({
                "success": True,
                "message": "Diet plan created successfully.",
                "diet_plan": new_plan.to_dict(include_items=True)
            }), 201

        return redirect(url_for("coach.diet_detail", plan_id=new_plan.id))

    # GET Request: Filter by client, status, and search query
    query = db.session.query(DietPlan).filter_by(coach_id=g.coach_id)

    client_filter_raw = request.args.get("client_id")
    selected_client_id = None
    if client_filter_raw:
        try:
            selected_client_id = int(client_filter_raw)
            query = query.filter_by(client_id=selected_client_id)
        except ValueError:
            pass

    status_filter = request.args.get("status", "all").strip().lower()
    if status_filter == "active":
        query = query.filter_by(is_active=True)
    elif status_filter == "inactive":
        query = query.filter_by(is_active=False)

    search_q = request.args.get("q", "").strip()
    if search_q:
        query = query.filter(
            (DietPlan.name.ilike(f"%{search_q}%")) | (DietPlan.description.ilike(f"%{search_q}%"))
        )

    plans = query.order_by(DietPlan.created_at.desc()).all()

    all_coach_plans = db.session.query(DietPlan).filter_by(coach_id=g.coach_id).all()
    active_count = sum(1 for p in all_coach_plans if p.is_active)
    inactive_count = len(all_coach_plans) - active_count

    coach_clients = db.session.query(Client).filter_by(coach_id=g.coach_id).all()

    if request.is_json or request.headers.get("Accept") == "application/json":
        return jsonify({
            "coach_id": g.coach_id,
            "total_diet_plans": len(plans),
            "diet_plans": [p.to_dict(include_items=True) for p in plans]
        }), 200

    return render_template(
        "coach_diets.html",
        user=user,
        coach=g.coach,
        plans=plans,
        clients=coach_clients,
        selected_client_id=selected_client_id,
        current_status=status_filter,
        search_query=search_q,
        active_count=active_count,
        inactive_count=inactive_count
    )


@coach_bp.route("/diets/<int:plan_id>", methods=["GET", "PUT", "PATCH", "DELETE"])
@coach_bp.route("/api/v1/diets/<int:plan_id>", methods=["GET", "PUT", "PATCH", "DELETE"])
@require_coach_tenant
def diet_detail(plan_id: int):
    """View, update, or delete a diet plan if and only if owned by this coach."""
    is_owner, plan = verify_coach_owns_diet_plan(g.coach_id, plan_id)
    if not is_owner or not plan:
        return tenant_access_denied("Diet Plan")

    if request.method == "DELETE":
        success, err = delete_diet_plan(g.coach_id, plan_id, db.session)
        if not success:
            return jsonify({"error": err or "Failed to delete plan.", "status_code": 400}), 400
        return jsonify({"success": True, "message": "Diet plan deleted."}), 200

    if request.method in ("PUT", "PATCH"):
        data = request.get_json() if request.is_json else request.form.to_dict()
        updated_plan, err = update_diet_plan(g.coach_id, plan_id, data, db.session)
        if err or not updated_plan:
            return jsonify({"error": err or "Failed to update diet plan.", "status_code": 400}), 400
        return jsonify({"success": True, "diet_plan": updated_plan.to_dict(include_items=True)}), 200

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
        "coach_diet_detail.html",
        user=user,
        coach=g.coach,
        plan=plan,
        nutrition=nutrition,
        grouped_meals=grouped_meals
    )


@coach_bp.route("/diets/<int:plan_id>/edit", methods=["POST"])
@coach_bp.route("/api/v1/diets/<int:plan_id>/edit", methods=["POST"])
@require_coach_tenant
def edit_diet_plan_view(plan_id: int):
    """Update diet plan details and macro targets."""
    is_owner, plan = verify_coach_owns_diet_plan(g.coach_id, plan_id)
    if not is_owner or not plan:
        return tenant_access_denied("Diet Plan")

    if not request.is_json and current_app.config.get("WTF_CSRF_ENABLED", True):
        token = request.form.get("csrf_token")
        if token and not validate_csrf_token(token):
            return jsonify({"error": "Security token expired. Please refresh.", "status_code": 403}), 403

    data = request.get_json() if request.is_json else request.form.to_dict()
    updated_plan, err = update_diet_plan(g.coach_id, plan_id, data, db.session)
    if err or not updated_plan:
        return jsonify({"error": err or "Failed to update diet plan.", "status_code": 400}), 400

    if request.is_json or request.headers.get("Accept") == "application/json":
        return jsonify({"success": True, "diet_plan": updated_plan.to_dict(include_items=True)}), 200

    return redirect(url_for("coach.diet_detail", plan_id=plan_id))


@coach_bp.route("/diets/<int:plan_id>/toggle-status", methods=["POST"])
@coach_bp.route("/api/v1/diets/<int:plan_id>/toggle-status", methods=["POST"])
@require_coach_tenant
def toggle_diet_plan_status_view(plan_id: int):
    """Toggle a diet plan's active status (archive / reactivate)."""
    is_owner, plan = verify_coach_owns_diet_plan(g.coach_id, plan_id)
    if not is_owner or not plan:
        return tenant_access_denied("Diet Plan")

    if not request.is_json and current_app.config.get("WTF_CSRF_ENABLED", True):
        token = request.form.get("csrf_token")
        if token and not validate_csrf_token(token):
            return jsonify({"error": "Security token expired. Please refresh.", "status_code": 403}), 403

    updated_plan, err = toggle_diet_plan_status(g.coach_id, plan_id, db.session)
    if err or not updated_plan:
        return jsonify({"error": err or "Failed to toggle plan status.", "status_code": 400}), 400

    if request.is_json or request.headers.get("Accept") == "application/json":
        return jsonify({
            "success": True,
            "is_active": updated_plan.is_active,
            "message": f"Plan status updated to {'active' if updated_plan.is_active else 'inactive'}."
        }), 200

    return redirect(url_for("coach.diet_detail", plan_id=plan_id))


@coach_bp.route("/diets/<int:plan_id>/items", methods=["POST"])
@coach_bp.route("/api/v1/diets/<int:plan_id>/items", methods=["POST"])
@require_coach_tenant
def add_diet_item_view(plan_id: int):
    """Add a food item to a diet plan owned by current coach."""
    is_owner, plan = verify_coach_owns_diet_plan(g.coach_id, plan_id)
    if not is_owner or not plan:
        return tenant_access_denied("Diet Plan")

    if not request.is_json and current_app.config.get("WTF_CSRF_ENABLED", True):
        token = request.form.get("csrf_token")
        if token and not validate_csrf_token(token):
            return jsonify({"error": "Security token expired. Please refresh.", "status_code": 403}), 403

    data = request.get_json() if request.is_json else request.form.to_dict()
    item, err = add_diet_item(g.coach_id, plan_id, data, db.session)
    if err or not item:
        return jsonify({"error": err or "Failed to add food item.", "status_code": 400}), 400

    if request.is_json or request.headers.get("Accept") == "application/json":
        return jsonify({"success": True, "item": item.to_dict()}), 201

    return redirect(url_for("coach.diet_detail", plan_id=plan_id))


@coach_bp.route("/diets/<int:plan_id>/items/<int:item_id>/edit", methods=["POST", "PUT"])
@coach_bp.route("/api/v1/diets/<int:plan_id>/items/<int:item_id>", methods=["PUT", "PATCH"])
@require_coach_tenant
def edit_diet_item_view(plan_id: int, item_id: int):
    """Update a food item inside a diet plan owned by current coach."""
    is_owner, plan = verify_coach_owns_diet_plan(g.coach_id, plan_id)
    if not is_owner or not plan:
        return tenant_access_denied("Diet Plan")

    if not request.is_json and current_app.config.get("WTF_CSRF_ENABLED", True):
        token = request.form.get("csrf_token")
        if token and not validate_csrf_token(token):
            return jsonify({"error": "Security token expired. Please refresh.", "status_code": 403}), 403

    data = request.get_json() if request.is_json else request.form.to_dict()
    item, err = update_diet_item(g.coach_id, plan_id, item_id, data, db.session)
    if err or not item:
        return jsonify({"error": err or "Failed to update food item.", "status_code": 400}), 400

    if request.is_json or request.headers.get("Accept") == "application/json":
        return jsonify({"success": True, "item": item.to_dict()}), 200

    return redirect(url_for("coach.diet_detail", plan_id=plan_id))


@coach_bp.route("/diets/<int:plan_id>/items/<int:item_id>/delete", methods=["POST", "DELETE"])
@coach_bp.route("/api/v1/diets/<int:plan_id>/items/<int:item_id>", methods=["DELETE"])
@require_coach_tenant
def delete_diet_item_view(plan_id: int, item_id: int):
    """Delete a food item from a diet plan owned by current coach."""
    is_owner, plan = verify_coach_owns_diet_plan(g.coach_id, plan_id)
    if not is_owner or not plan:
        return tenant_access_denied("Diet Plan")

    if request.method == "POST" and not request.is_json and current_app.config.get("WTF_CSRF_ENABLED", True):
        token = request.form.get("csrf_token")
        if token and not validate_csrf_token(token):
            return jsonify({"error": "Security token expired. Please refresh.", "status_code": 403}), 403

    success, err = delete_diet_item(g.coach_id, plan_id, item_id, db.session)
    if not success:
        return jsonify({"error": err or "Failed to delete food item.", "status_code": 400}), 400

    if request.is_json or request.headers.get("Accept") == "application/json":
        return jsonify({"success": True, "message": "Food item deleted."}), 200

    return redirect(url_for("coach.diet_detail", plan_id=plan_id))


# =========================================================================
# WORKOUT PLANS (TENANT ISOLATED)
# =========================================================================

@coach_bp.route("/workouts", methods=["GET", "POST"])
@coach_bp.route("/api/v1/workouts", methods=["GET", "POST"])
@require_coach_tenant
def manage_workouts():
    """
    GET: List workout plans created by current coach.
    POST: Create workout plan for one of current coach's clients.
    """
    if request.method == "POST":
        data = request.get_json() if request.is_json else request.form.to_dict()
        client_id = int(data.get("client_id", 0))
        name = (data.get("name") or "").strip()

        if not name or not client_id:
            return jsonify({"error": "Plan name and valid client_id are required.", "status_code": 400}), 400

        # Verify client belongs to current coach
        is_owner, client = verify_coach_owns_client(g.coach_id, client_id)
        if not is_owner or not client:
            return tenant_access_denied("Client")

        # Create workout plan: Authoritatively forces coach_id = g.coach_id
        new_plan = WorkoutPlan(
            coach_id=g.coach_id,  # Authoritative backend assignment
            client_id=client_id,
            name=name,
            description=data.get("description"),
            split_type=data.get("split_type", "PPL"),
            difficulty_level=data.get("difficulty_level", "INTERMEDIATE"),
            is_active=True
        )
        db.session.add(new_plan)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Workout plan created successfully.",
            "workout_plan": new_plan.to_dict()
        }), 201

    plans = db.session.query(WorkoutPlan).filter_by(coach_id=g.coach_id).all()
    return jsonify({
        "coach_id": g.coach_id,
        "total_workout_plans": len(plans),
        "workout_plans": [p.to_dict() for p in plans]
    }), 200


@coach_bp.route("/workouts/<int:plan_id>", methods=["GET", "PUT", "PATCH", "DELETE"])
@coach_bp.route("/api/v1/workouts/<int:plan_id>", methods=["GET", "PUT", "PATCH", "DELETE"])
@require_coach_tenant
def workout_detail(plan_id: int):
    """View, update, or delete a workout plan if and only if owned by this coach."""
    is_owner, plan = verify_coach_owns_workout_plan(g.coach_id, plan_id)
    if not is_owner or not plan:
        return tenant_access_denied("Workout Plan")

    if request.method == "DELETE":
        db.session.delete(plan)
        db.session.commit()
        return jsonify({"success": True, "message": "Workout plan deleted."}), 200

    if request.method in ("PUT", "PATCH"):
        data = request.get_json() if request.is_json else request.form.to_dict()
        if "name" in data:
            plan.name = data["name"].strip()
        if "difficulty_level" in data:
            plan.difficulty_level = data["difficulty_level"]
        # Ownership fields (coach_id, client_id) CANNOT be changed
        db.session.commit()
        return jsonify({"success": True, "workout_plan": plan.to_dict()}), 200

    return jsonify({"success": True, "workout_plan": plan.to_dict()}), 200


# =========================================================================
# CLIENT BIOMETRICS & PROGRESS INSPECTION (TENANT ISOLATED)
# =========================================================================

@coach_bp.route("/clients/<int:client_id>/progress", methods=["GET"])
@coach_bp.route("/api/v1/clients/<int:client_id>/progress", methods=["GET"])
@require_coach_tenant
def client_progress_list(client_id: int):
    """Coach viewing progress history of a client. Rejects cross-tenant queries."""
    is_owner, client = verify_coach_owns_client(g.coach_id, client_id)
    if not is_owner or not client:
        return tenant_access_denied("Client Progress")

    records = db.session.query(Progress).filter_by(client_id=client_id).order_by(Progress.date.desc()).all()
    return jsonify({
        "coach_id": g.coach_id,
        "client_id": client_id,
        "total_records": len(records),
        "progress_records": [p.to_dict() for p in records]
    }), 200


@coach_bp.route("/progress/<int:progress_id>", methods=["GET"])
@coach_bp.route("/api/v1/progress/<int:progress_id>", methods=["GET"])
@require_coach_tenant
def progress_detail(progress_id: int):
    """Coach viewing a single progress entry. Verifies client belongs to this coach."""
    is_owner, progress = verify_coach_owns_progress(g.coach_id, progress_id)
    if not is_owner or not progress:
        return tenant_access_denied("Progress Entry")

    return jsonify({
        "success": True,
        "progress": progress.to_dict()
    }), 200
