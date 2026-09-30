"""
FitPulse SaaS - Diet Plan Management Service (Phase 4B)
Authoritatively handles diet plan creation, meal/food item management,
nutritional calculations, and multi-tenant isolation for Coaches and Clients.

SECURITY GUARANTEES:
- Coach ownership: A coach can only create, view, edit, or delete diet plans for clients in their own roster.
- Client ownership: A client can only view diet plans assigned to their own client_id.
- DietItem isolation: An item can only be added, updated, or deleted if the parent DietPlan is owned by the coach.
- Absolute server-side authority: coach_id and client_id in payloads are never trusted over authenticated context.
"""
from datetime import datetime, date
from typing import Optional, Tuple, Dict, Any, List
from collections import OrderedDict

try:
    from models import db, User, Coach, Client, DietPlan, DietItem
    _HAS_MODELS = True
except ImportError:
    _HAS_MODELS = False
    db = None
    User = None
    Coach = None
    Client = None
    DietPlan = None
    DietItem = None


# Allowed common meal category suggestions
DEFAULT_MEAL_NAMES = [
    "Breakfast",
    "Mid-Morning Snack",
    "Lunch",
    "Afternoon Snack",
    "Pre-Workout",
    "Post-Workout",
    "Dinner",
    "Evening Snack"
]


def validate_diet_plan_input(data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Validate and sanitize DietPlan inputs.
    Returns (is_valid, error_message, sanitized_dict).
    """
    sanitized: Dict[str, Any] = {}

    # 1. Plan Name
    name = (data.get("name") or "").strip()
    if not is_update or "name" in data:
        if not name:
            return False, "Plan name is required.", {}
        if len(name) > 150:
            return False, "Plan name must not exceed 150 characters.", {}
        sanitized["name"] = name

    # 2. Description
    if "description" in data:
        desc = data.get("description")
        sanitized["description"] = str(desc).strip() if desc else None

    # 3. Daily Calorie Target (kcal)
    cal_raw = data.get("daily_calorie_target")
    if cal_raw is not None and str(cal_raw).strip() != "":
        try:
            cal = int(float(cal_raw))
            if cal < 0 or cal > 15000:
                return False, "Daily calorie target must be between 0 and 15,000 kcal.", {}
            sanitized["daily_calorie_target"] = cal
        except ValueError:
            return False, "Daily calorie target must be a valid integer.", {}
    elif not is_update:
        sanitized["daily_calorie_target"] = None

    # 4. Macro Targets (Protein, Carbs, Fat in grams)
    macro_fields = [
        ("protein_target", 0.0, 1000.0, "Protein"),
        ("carbs_target", 0.0, 2000.0, "Carbohydrate"),
        ("fat_target", 0.0, 1000.0, "Fat")
    ]
    for field_name, min_val, max_val, label in macro_fields:
        raw_val = data.get(field_name)
        if raw_val is not None and str(raw_val).strip() != "":
            try:
                val = float(raw_val)
                if val < min_val or val > max_val:
                    return False, f"{label} target must be between {int(min_val)}g and {int(max_val)}g.", {}
                sanitized[field_name] = round(val, 1)
            except ValueError:
                return False, f"{label} target must be a valid numeric value.", {}
        elif not is_update:
            sanitized[field_name] = None

    # 5. Scheduling Dates (start_date, end_date)
    start_d = None
    end_d = None

    if "start_date" in data:
        s_raw = data.get("start_date")
        if s_raw:
            if isinstance(s_raw, date):
                start_d = s_raw
            elif isinstance(s_raw, str) and s_raw.strip():
                try:
                    start_d = datetime.strptime(s_raw.strip(), "%Y-%m-%d").date()
                except ValueError:
                    return False, "Start date must be formatted as YYYY-MM-DD.", {}
        sanitized["start_date"] = start_d

    if "end_date" in data:
        e_raw = data.get("end_date")
        if e_raw:
            if isinstance(e_raw, date):
                end_d = e_raw
            elif isinstance(e_raw, str) and e_raw.strip():
                try:
                    end_d = datetime.strptime(e_raw.strip(), "%Y-%m-%d").date()
                except ValueError:
                    return False, "End date must be formatted as YYYY-MM-DD.", {}
        sanitized["end_date"] = end_d

    if start_d and end_d and end_d < start_d:
        return False, "End date cannot be prior to start date.", {}

    # 6. Active Status
    if "is_active" in data:
        val = data.get("is_active")
        if isinstance(val, bool):
            sanitized["is_active"] = val
        elif isinstance(val, str):
            sanitized["is_active"] = val.lower() in ("true", "1", "yes", "on")
        else:
            sanitized["is_active"] = bool(val)
    elif not is_update:
        sanitized["is_active"] = True

    return True, None, sanitized


def validate_diet_item_input(data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Validate and sanitize DietItem inputs.
    Returns (is_valid, error_message, sanitized_dict).
    """
    sanitized: Dict[str, Any] = {}

    # 1. Meal Name
    meal_name = (data.get("meal_name") or "").strip()
    if not is_update or "meal_name" in data:
        if not meal_name:
            return False, "Meal name is required (e.g. Breakfast, Lunch, Dinner).", {}
        if len(meal_name) > 100:
            return False, "Meal name must not exceed 100 characters.", {}
        sanitized["meal_name"] = meal_name

    # 2. Food Name
    food_name = (data.get("food_name") or "").strip()
    if not is_update or "food_name" in data:
        if not food_name:
            return False, "Food name is required (e.g. Rolled Oats, Chicken Breast).", {}
        if len(food_name) > 150:
            return False, "Food name must not exceed 150 characters.", {}
        sanitized["food_name"] = food_name

    # 3. Quantity
    qty_raw = data.get("quantity")
    if not is_update or "quantity" in data:
        if qty_raw is None or str(qty_raw).strip() == "":
            return False, "Quantity is required.", {}
        try:
            qty = float(qty_raw)
            if qty <= 0 or qty > 10000:
                return False, "Quantity must be a positive number greater than 0.", {}
            sanitized["quantity"] = round(qty, 2)
        except ValueError:
            return False, "Quantity must be a valid numeric value.", {}

    # 4. Unit
    unit = (data.get("unit") or "").strip()
    if not is_update or "unit" in data:
        if not unit:
            return False, "Unit is required (e.g. grams, ml, pieces, scoops).", {}
        if len(unit) > 50:
            return False, "Unit must not exceed 50 characters.", {}
        sanitized["unit"] = unit

    # 5. Nutritional values (non-negative)
    cal_raw = data.get("calories")
    if cal_raw is not None and str(cal_raw).strip() != "":
        try:
            cal = int(float(cal_raw))
            if cal < 0:
                return False, "Calories cannot be negative.", {}
            if cal > 10000:
                return False, "Calories must be reasonable (< 10,000 kcal per item).", {}
            sanitized["calories"] = cal
        except ValueError:
            return False, "Calories must be a valid integer.", {}
    elif not is_update:
        sanitized["calories"] = 0

    macro_fields = [
        ("protein", "Protein"),
        ("carbohydrates", "Carbohydrates"),
        ("fat", "Fat")
    ]
    for field_name, label in macro_fields:
        raw_val = data.get(field_name)
        if raw_val is not None and str(raw_val).strip() != "":
            try:
                val = float(raw_val)
                if val < 0:
                    return False, f"{label} cannot be negative.", {}
                if val > 1000:
                    return False, f"{label} must be reasonable (< 1,000g per item).", {}
                sanitized[field_name] = round(val, 1)
            except ValueError:
                return False, f"{label} must be a valid numeric value.", {}
        elif not is_update:
            sanitized[field_name] = 0.0

    # 6. Timing & Notes
    if "meal_time" in data:
        mt = data.get("meal_time")
        sanitized["meal_time"] = str(mt).strip() if mt else None
    elif not is_update:
        sanitized["meal_time"] = None

    if "notes" in data:
        n = data.get("notes")
        sanitized["notes"] = str(n).strip() if n else None
    elif not is_update:
        sanitized["notes"] = None

    return True, None, sanitized


# =========================================================================
# COACH DIET PLAN OPERATIONS
# =========================================================================

def create_diet_plan(coach_id: int, client_id: int, data: Dict[str, Any], db_session=None) -> Tuple[Optional[Any], Optional[str]]:
    """
    Create a new DietPlan for client_id under coach_id.
    Authoritatively verifies that client_id belongs to coach_id.
    """
    session = db_session or db.session

    # Verify client ownership
    client = session.query(Client).filter_by(id=client_id, coach_id=coach_id).first()
    if not client:
        return None, "Selected athlete not found or does not belong to your coaching roster."

    is_valid, err, clean_data = validate_diet_plan_input(data, is_update=False)
    if not is_valid:
        return None, err

    try:
        new_plan = DietPlan(
            coach_id=coach_id,    # Authoritative server-side assignment
            client_id=client_id,  # Authoritative verified client
            name=clean_data["name"],
            description=clean_data.get("description"),
            daily_calorie_target=clean_data.get("daily_calorie_target"),
            protein_target=clean_data.get("protein_target"),
            carbs_target=clean_data.get("carbs_target"),
            fat_target=clean_data.get("fat_target"),
            start_date=clean_data.get("start_date"),
            end_date=clean_data.get("end_date"),
            is_active=clean_data.get("is_active", True)
        )
        session.add(new_plan)
        session.commit()
        return new_plan, None
    except Exception as e:
        session.rollback()
        return None, f"Failed to create diet plan: {str(e)}"


def update_diet_plan(coach_id: int, plan_id: int, data: Dict[str, Any], db_session=None) -> Tuple[Optional[Any], Optional[str]]:
    """
    Update an existing DietPlan owned by coach_id.
    Refuses modification of coach_id or client_id.
    """
    session = db_session or db.session
    plan = session.query(DietPlan).filter_by(id=plan_id, coach_id=coach_id).first()
    if not plan:
        return None, "Diet plan not found or access denied."

    is_valid, err, clean_data = validate_diet_plan_input(data, is_update=True)
    if not is_valid:
        return None, err

    try:
        if "name" in clean_data:
            plan.name = clean_data["name"]
        if "description" in clean_data:
            plan.description = clean_data["description"]
        if "daily_calorie_target" in clean_data:
            plan.daily_calorie_target = clean_data["daily_calorie_target"]
        if "protein_target" in clean_data:
            plan.protein_target = clean_data["protein_target"]
        if "carbs_target" in clean_data:
            plan.carbs_target = clean_data["carbs_target"]
        if "fat_target" in clean_data:
            plan.fat_target = clean_data["fat_target"]
        if "start_date" in clean_data:
            plan.start_date = clean_data["start_date"]
        if "end_date" in clean_data:
            plan.end_date = clean_data["end_date"]
        if "is_active" in clean_data:
            plan.is_active = clean_data["is_active"]

        # Note: coach_id and client_id remain immutable
        session.commit()
        return plan, None
    except Exception as e:
        session.rollback()
        return None, f"Failed to update diet plan: {str(e)}"


def toggle_diet_plan_status(coach_id: int, plan_id: int, db_session=None) -> Tuple[Optional[Any], Optional[str]]:
    """Toggle a DietPlan's active status (deactivate or reactivate)."""
    session = db_session or db.session
    plan = session.query(DietPlan).filter_by(id=plan_id, coach_id=coach_id).first()
    if not plan:
        return None, "Diet plan not found or access denied."

    try:
        plan.is_active = not plan.is_active
        session.commit()
        return plan, None
    except Exception as e:
        session.rollback()
        return None, f"Failed to update plan status: {str(e)}"


def delete_diet_plan(coach_id: int, plan_id: int, db_session=None) -> Tuple[bool, Optional[str]]:
    """
    Permanently delete a DietPlan and its associated DietItems.
    Verifies that the plan belongs to the authenticated coach.
    """
    session = db_session or db.session
    plan = session.query(DietPlan).filter_by(id=plan_id, coach_id=coach_id).first()
    if not plan:
        return False, "Diet plan not found or access denied."

    try:
        session.delete(plan)
        session.commit()
        return True, None
    except Exception as e:
        session.rollback()
        return False, f"Failed to delete diet plan: {str(e)}"


# =========================================================================
# DIET ITEM OPERATIONS (CHILD OF DIET PLAN)
# =========================================================================

def add_diet_item(coach_id: int, plan_id: int, data: Dict[str, Any], db_session=None) -> Tuple[Optional[Any], Optional[str]]:
    """
    Add a food item to a DietPlan.
    Verifies that the parent DietPlan is owned by coach_id.
    """
    session = db_session or db.session
    plan = session.query(DietPlan).filter_by(id=plan_id, coach_id=coach_id).first()
    if not plan:
        return None, "Diet plan not found or access denied."

    is_valid, err, clean_data = validate_diet_item_input(data, is_update=False)
    if not is_valid:
        return None, err

    try:
        item = DietItem(
            diet_plan_id=plan.id,
            meal_name=clean_data["meal_name"],
            food_name=clean_data["food_name"],
            quantity=clean_data["quantity"],
            unit=clean_data["unit"],
            calories=clean_data.get("calories", 0),
            protein=clean_data.get("protein", 0.0),
            carbohydrates=clean_data.get("carbohydrates", 0.0),
            fat=clean_data.get("fat", 0.0),
            meal_time=clean_data.get("meal_time"),
            notes=clean_data.get("notes")
        )
        session.add(item)
        session.commit()
        return item, None
    except Exception as e:
        session.rollback()
        return None, f"Failed to add food item: {str(e)}"


def update_diet_item(coach_id: int, plan_id: int, item_id: int, data: Dict[str, Any], db_session=None) -> Tuple[Optional[Any], Optional[str]]:
    """
    Update a DietItem.
    Verifies that the parent DietPlan is owned by coach_id and the item belongs to that plan.
    """
    session = db_session or db.session
    plan = session.query(DietPlan).filter_by(id=plan_id, coach_id=coach_id).first()
    if not plan:
        return None, "Diet plan not found or access denied."

    item = session.query(DietItem).filter_by(id=item_id, diet_plan_id=plan.id).first()
    if not item:
        return None, "Food item not found or does not belong to this diet plan."

    is_valid, err, clean_data = validate_diet_item_input(data, is_update=True)
    if not is_valid:
        return None, err

    try:
        if "meal_name" in clean_data:
            item.meal_name = clean_data["meal_name"]
        if "food_name" in clean_data:
            item.food_name = clean_data["food_name"]
        if "quantity" in clean_data:
            item.quantity = clean_data["quantity"]
        if "unit" in clean_data:
            item.unit = clean_data["unit"]
        if "calories" in clean_data:
            item.calories = clean_data["calories"]
        if "protein" in clean_data:
            item.protein = clean_data["protein"]
        if "carbohydrates" in clean_data:
            item.carbohydrates = clean_data["carbohydrates"]
        if "fat" in clean_data:
            item.fat = clean_data["fat"]
        if "meal_time" in clean_data:
            item.meal_time = clean_data["meal_time"]
        if "notes" in clean_data:
            item.notes = clean_data["notes"]

        session.commit()
        return item, None
    except Exception as e:
        session.rollback()
        return None, f"Failed to update food item: {str(e)}"


def delete_diet_item(coach_id: int, plan_id: int, item_id: int, db_session=None) -> Tuple[bool, Optional[str]]:
    """
    Delete a DietItem.
    Verifies that the parent DietPlan is owned by coach_id and the item belongs to that plan.
    """
    session = db_session or db.session
    plan = session.query(DietPlan).filter_by(id=plan_id, coach_id=coach_id).first()
    if not plan:
        return False, "Diet plan not found or access denied."

    item = session.query(DietItem).filter_by(id=item_id, diet_plan_id=plan.id).first()
    if not item:
        return False, "Food item not found or does not belong to this diet plan."

    try:
        session.delete(item)
        session.commit()
        return True, None
    except Exception as e:
        session.rollback()
        return False, f"Failed to delete food item: {str(e)}"


# =========================================================================
# CALCULATIONS & PRESENTATION HELPERS
# =========================================================================

def compute_diet_plan_nutrition(plan: Any) -> Dict[str, Any]:
    """
    Calculate actual food totals and compare against coach-defined targets.
    Clearly distinguishes target values from calculated item totals.
    """
    items = plan.items if hasattr(plan, "items") and plan.items else []

    total_calories = sum(int(item.calories or 0) for item in items)
    total_protein = round(sum(float(item.protein or 0.0) for item in items), 1)
    total_carbs = round(sum(float(item.carbohydrates or 0.0) for item in items), 1)
    total_fat = round(sum(float(item.fat or 0.0) for item in items), 1)

    return {
        "targets": {
            "calories": plan.daily_calorie_target,
            "protein": plan.protein_target,
            "carbs": plan.carbs_target,
            "fat": plan.fat_target,
        },
        "actual_totals": {
            "calories": total_calories,
            "protein": total_protein,
            "carbs": total_carbs,
            "fat": total_fat,
        },
        "delta": {
            "calories": (total_calories - plan.daily_calorie_target) if plan.daily_calorie_target else None,
            "protein": round(total_protein - plan.protein_target, 1) if plan.protein_target else None,
            "carbs": round(total_carbs - plan.carbs_target, 1) if plan.carbs_target else None,
            "fat": round(total_fat - plan.fat_target, 1) if plan.fat_target else None,
        },
        "items_count": len(items)
    }


def group_diet_items_by_meal(items: List[Any]) -> OrderedDict:
    """
    Group DietItem records by meal_name preserving logical meal grouping.
    Returns an OrderedDict mapping meal_name -> list of items, with subtotal calories/macros per meal.
    """
    grouped = OrderedDict()
    if not items:
        return grouped

    for item in items:
        m_name = item.meal_name or "General Meals"
        if m_name not in grouped:
            grouped[m_name] = {
                "meal_name": m_name,
                "meal_time": item.meal_time,
                "items": [],
                "subtotal_calories": 0,
                "subtotal_protein": 0.0,
                "subtotal_carbs": 0.0,
                "subtotal_fat": 0.0,
            }
        grouped[m_name]["items"].append(item)
        grouped[m_name]["subtotal_calories"] += int(item.calories or 0)
        grouped[m_name]["subtotal_protein"] += float(item.protein or 0.0)
        grouped[m_name]["subtotal_carbs"] += float(item.carbohydrates or 0.0)
        grouped[m_name]["subtotal_fat"] += float(item.fat or 0.0)

    # Round subtotals
    for m in grouped.values():
        m["subtotal_protein"] = round(m["subtotal_protein"], 1)
        m["subtotal_carbs"] = round(m["subtotal_carbs"], 1)
        m["subtotal_fat"] = round(m["subtotal_fat"], 1)

    return grouped
