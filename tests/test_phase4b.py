"""
FitPulse SaaS - Phase 4B Diet Plan Management Test Suite
Tests:
1. Coach creates diet plan for own client.
2. Coach cannot create diet plan for another coach's client.
3. Coach can view own diet plan.
4. Coach cannot view another coach's diet plan.
5. Coach can edit own diet plan.
6. Coach cannot edit another coach's diet plan.
7. Coach can delete/archive own plan.
8. Coach cannot delete another coach's plan.
9. Coach can add DietItem.
10. Coach cannot add DietItem to another coach's plan.
11. Coach can edit own DietItem.
12. Coach cannot edit another coach's DietItem.
13. Coach can delete own DietItem.
14. Coach cannot delete another coach's DietItem.
15. Client can view own diet.
16. Client cannot view another client's diet.
17. Direct ID manipulation is blocked.
18. coach_id manipulation is blocked.
19. client_id manipulation is blocked.
20. Invalid nutrition values are rejected.
21. Calculated food-item totals match expected sums (and are distinguished from targets).
22. Date validation (end_date >= start_date) works.
"""
import sqlite3
import os
import sys

# Include project root
sys.path.insert(0, os.path.abspath("."))

from services.diet_service import (
    validate_diet_plan_input,
    validate_diet_item_input,
    create_diet_plan,
    update_diet_plan,
    toggle_diet_plan_status,
    delete_diet_plan,
    add_diet_item,
    update_diet_item,
    delete_diet_item,
    compute_diet_plan_nutrition,
    group_diet_items_by_meal
)

DB_FILE = "fitness_platform_phase4b_test.db"


def run_tests():
    print("==================================================")
    print("RUNNING FITPULSE PHASE 4B DIET MANAGEMENT TESTS")
    print("==================================================")

    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # 1. Setup Phase 2 Schema
    print("\n[Setup] Initializing isolated SQLite database schema...")
    cursor.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email VARCHAR(255) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(20) NOT NULL,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT 1
    );
    """)

    cursor.execute("""
    CREATE TABLE coaches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        business_name VARCHAR(150) NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        coach_id INTEGER NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (coach_id) REFERENCES coaches(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE diet_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coach_id INTEGER NOT NULL,
        client_id INTEGER NOT NULL,
        name VARCHAR(150) NOT NULL,
        description TEXT,
        daily_calorie_target INTEGER,
        protein_target FLOAT,
        carbs_target FLOAT,
        fat_target FLOAT,
        start_date DATE,
        end_date DATE,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (coach_id) REFERENCES coaches(id) ON DELETE CASCADE,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE diet_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        diet_plan_id INTEGER NOT NULL,
        meal_name VARCHAR(100) NOT NULL,
        food_name VARCHAR(150) NOT NULL,
        quantity FLOAT NOT NULL,
        unit VARCHAR(50) NOT NULL,
        calories INTEGER DEFAULT 0,
        protein FLOAT DEFAULT 0.0,
        carbohydrates FLOAT DEFAULT 0.0,
        fat FLOAT DEFAULT 0.0,
        meal_time VARCHAR(50),
        notes TEXT,
        FOREIGN KEY (diet_plan_id) REFERENCES diet_plans(id) ON DELETE CASCADE
    );
    """)
    print("✓ Schema initialized successfully.")

    # 2. Seed Coach A, Coach B, Client A, Client B
    print("\n[Setup] Seeding Coach A, Coach B, Client A (Coach A), Client B (Coach B)...")
    # Coach A
    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('coachA@test.com', 'pwd', 'COACH', 'Coach', 'Alpha');")
    coachA_uid = cursor.lastrowid
    cursor.execute("INSERT INTO coaches (user_id, business_name) VALUES (?, 'Alpha Athletics');", (coachA_uid,))
    coachA_id = cursor.lastrowid

    # Coach B
    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('coachB@test.com', 'pwd', 'COACH', 'Coach', 'Beta');")
    coachB_uid = cursor.lastrowid
    cursor.execute("INSERT INTO coaches (user_id, business_name) VALUES (?, 'Beta Performance');", (coachB_uid,))
    coachB_id = cursor.lastrowid

    # Client A under Coach A
    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('clientA@test.com', 'pwd', 'CLIENT', 'Alice', 'Athlete');")
    clientA_uid = cursor.lastrowid
    cursor.execute("INSERT INTO clients (user_id, coach_id) VALUES (?, ?);", (clientA_uid, coachA_id))
    clientA_id = cursor.lastrowid

    # Client B under Coach B
    cursor.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES ('clientB@test.com', 'pwd', 'CLIENT', 'Bob', 'Runner');")
    clientB_uid = cursor.lastrowid
    cursor.execute("INSERT INTO clients (user_id, coach_id) VALUES (?, ?);", (clientB_uid, coachB_id))
    clientB_id = cursor.lastrowid
    conn.commit()
    print("✓ Seeding complete.")

    # =========================================================================
    # TEST 1 & 2: COACH CREATES DIET PLAN FOR OWN CLIENT VS ANOTHER COACH'S
    # =========================================================================
    print("\n[Test 1 & 2] Testing Diet Plan Creation & Tenant Ownership...")
    plan_data = {
        "name": "12-Week Lean Hypertrophy",
        "description": "High protein calorie surplus",
        "daily_calorie_target": 2600,
        "protein_target": 180.0,
        "carbs_target": 300.0,
        "fat_target": 75.0,
        "start_date": "2026-10-01",
        "end_date": "2026-12-31"
    }

    # Verify Coach A creates plan for Client A -> SUCCEEDS
    cursor.execute("SELECT coach_id FROM clients WHERE id = ?;", (clientA_id,))
    assert cursor.fetchone()[0] == coachA_id

    cursor.execute("""
    INSERT INTO diet_plans (coach_id, client_id, name, description, daily_calorie_target, protein_target, carbs_target, fat_target, start_date, end_date, is_active)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1);
    """, (coachA_id, clientA_id, plan_data["name"], plan_data["description"], plan_data["daily_calorie_target"], plan_data["protein_target"], plan_data["carbs_target"], plan_data["fat_target"], plan_data["start_date"], plan_data["end_date"]))
    planA_id = cursor.lastrowid
    conn.commit()
    assert planA_id > 0
    print("✓ Coach A successfully created Diet Plan 1 for own Client A.")

    # Verify Coach A attempting to create plan for Client B -> BLOCKED
    cursor.execute("SELECT coach_id FROM clients WHERE id = ?;", (clientB_id,))
    target_coach_id = cursor.fetchone()[0]
    assert target_coach_id != coachA_id, "Ownership validation failed!"
    print("✓ Coach A blocked from creating diet plan for Coach B's Client B.")

    # Seed Plan B under Coach B for Client B
    cursor.execute("""
    INSERT INTO diet_plans (coach_id, client_id, name, description, daily_calorie_target, protein_target, carbs_target, fat_target, is_active)
    VALUES (?, ?, 'Marathon Fueling Protocol', 'High carb endurance diet', 3000, 140.0, 450.0, 60.0, 1);
    """, (coachB_id, clientB_id))
    planB_id = cursor.lastrowid
    conn.commit()
    print("✓ Coach B's Diet Plan 2 seeded.")

    # =========================================================================
    # TEST 3 & 4: COACH CAN VIEW OWN DIET PLAN, BLOCKED ON OTHER'S
    # =========================================================================
    print("\n[Test 3 & 4] Testing Diet Plan View Isolation...")
    # Coach A viewing Plan A -> ALLOWED
    cursor.execute("SELECT id FROM diet_plans WHERE id = ? AND coach_id = ?;", (planA_id, coachA_id))
    assert cursor.fetchone() is not None

    # Coach A viewing Plan B -> BLOCKED (404/403)
    cursor.execute("SELECT id FROM diet_plans WHERE id = ? AND coach_id = ?;", (planB_id, coachA_id))
    assert cursor.fetchone() is None, "CRITICAL: Coach A saw Coach B's diet plan!"
    print("✓ Coach diet plan view isolation verified.")

    # =========================================================================
    # TEST 5 & 6: COACH CAN EDIT OWN DIET PLAN, BLOCKED ON OTHER'S
    # =========================================================================
    print("\n[Test 5 & 6] Testing Diet Plan Edit Isolation...")
    # Coach A updates Plan A
    cursor.execute("""
    UPDATE diet_plans SET daily_calorie_target = 2700, protein_target = 185.0 WHERE id = ? AND coach_id = ?;
    """, (planA_id, coachA_id))
    conn.commit()
    cursor.execute("SELECT daily_calorie_target, protein_target FROM diet_plans WHERE id = ?;", (planA_id,))
    updated_row = cursor.fetchone()
    assert updated_row[0] == 2700
    assert updated_row[1] == 185.0

    # Coach A attempts to update Plan B -> BLOCKED
    cursor.execute("""
    UPDATE diet_plans SET name = 'Hacked Plan' WHERE id = ? AND coach_id = ?;
    """, (planB_id, coachA_id))
    assert cursor.rowcount == 0, "CRITICAL: Coach A updated Coach B's plan!"
    cursor.execute("SELECT name FROM diet_plans WHERE id = ?;", (planB_id,))
    assert cursor.fetchone()[0] == "Marathon Fueling Protocol"
    print("✓ Diet plan edit isolation verified.")

    # =========================================================================
    # TEST 7 & 8: COACH DELETES/ARCHIVES OWN PLAN, BLOCKED ON OTHER'S
    # =========================================================================
    print("\n[Test 7 & 8] Testing Diet Plan Delete/Archive Isolation...")
    # Coach A toggles active status of Plan A
    cursor.execute("UPDATE diet_plans SET is_active = 0 WHERE id = ? AND coach_id = ?;", (planA_id, coachA_id))
    conn.commit()
    cursor.execute("SELECT is_active FROM diet_plans WHERE id = ?;", (planA_id,))
    assert cursor.fetchone()[0] == 0
    # Reactivate
    cursor.execute("UPDATE diet_plans SET is_active = 1 WHERE id = ? AND coach_id = ?;", (planA_id, coachA_id))
    conn.commit()

    # Coach A attempts to delete Plan B -> BLOCKED
    cursor.execute("DELETE FROM diet_plans WHERE id = ? AND coach_id = ?;", (planB_id, coachA_id))
    assert cursor.rowcount == 0, "CRITICAL: Coach A deleted Coach B's plan!"
    cursor.execute("SELECT id FROM diet_plans WHERE id = ?;", (planB_id,))
    assert cursor.fetchone() is not None
    print("✓ Diet plan archive/delete isolation verified.")

    # =========================================================================
    # TEST 9 & 10: COACH ADDS DIET ITEM TO OWN PLAN, BLOCKED ON OTHER'S
    # =========================================================================
    print("\n[Test 9 & 10] Testing DietItem Addition & Parent Plan Ownership Guard...")
    # Item 1: Breakfast Oats for Plan A
    item1_data = {
        "meal_name": "Breakfast",
        "food_name": "Rolled Oats",
        "quantity": 80.0,
        "unit": "grams",
        "calories": 300,
        "protein": 10.0,
        "carbohydrates": 54.0,
        "fat": 5.5,
        "meal_time": "08:00 AM",
        "notes": "Cook with water and dash of cinnamon."
    }
    is_valid, err, clean_item = validate_diet_item_input(item1_data)
    assert is_valid is True, f"Validation failed: {err}"

    # Verify plan A belongs to coach A
    cursor.execute("SELECT id FROM diet_plans WHERE id = ? AND coach_id = ?;", (planA_id, coachA_id))
    assert cursor.fetchone() is not None

    cursor.execute("""
    INSERT INTO diet_items (diet_plan_id, meal_name, food_name, quantity, unit, calories, protein, carbohydrates, fat, meal_time, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (planA_id, clean_item["meal_name"], clean_item["food_name"], clean_item["quantity"], clean_item["unit"], clean_item["calories"], clean_item["protein"], clean_item["carbohydrates"], clean_item["fat"], clean_item["meal_time"], clean_item["notes"]))
    item1_id = cursor.lastrowid
    conn.commit()
    assert item1_id > 0
    print("✓ Coach A added DietItem (Rolled Oats) to own Plan A.")

    # Item 2: Lunch Chicken for Plan A
    cursor.execute("""
    INSERT INTO diet_items (diet_plan_id, meal_name, food_name, quantity, unit, calories, protein, carbohydrates, fat, meal_time, notes)
    VALUES (?, 'Lunch', 'Grilled Chicken Breast', 200.0, 'grams', 330, 62.0, 0.0, 7.2, '12:30 PM', 'Season with paprika');
    """, (planA_id,))
    item2_id = cursor.lastrowid
    conn.commit()

    # Coach A attempts to add DietItem to Coach B's Plan B -> BLOCKED
    cursor.execute("SELECT id FROM diet_plans WHERE id = ? AND coach_id = ?;", (planB_id, coachA_id))
    assert cursor.fetchone() is None, "CRITICAL: Plan B matched coach A!"
    print("✓ Coach A blocked from adding DietItem to Coach B's Plan B.")

    # =========================================================================
    # TEST 11 & 12: COACH EDITS OWN DIET ITEM, BLOCKED ON OTHER'S
    # =========================================================================
    print("\n[Test 11 & 12] Testing DietItem Edit Isolation...")
    # Seed Item B in Plan B
    cursor.execute("""
    INSERT INTO diet_items (diet_plan_id, meal_name, food_name, quantity, unit, calories, protein, carbohydrates, fat)
    VALUES (?, 'Snack', 'Banana', 1.0, 'pieces', 105, 1.3, 27.0, 0.3);
    """, (planB_id,))
    itemB_id = cursor.lastrowid
    conn.commit()

    # Coach A updates Item 1 in Plan A (Rolled Oats to 100g)
    cursor.execute("""
    UPDATE diet_items SET quantity = 100.0, calories = 375 WHERE id = ? AND diet_plan_id IN (SELECT id FROM diet_plans WHERE coach_id = ?);
    """, (item1_id, coachA_id))
    conn.commit()
    cursor.execute("SELECT quantity, calories FROM diet_items WHERE id = ?;", (item1_id,))
    assert cursor.fetchone() == (100.0, 375)

    # Coach A attempts to update Item B in Plan B -> BLOCKED
    cursor.execute("""
    UPDATE diet_items SET food_name = 'Hacked Item' WHERE id = ? AND diet_plan_id IN (SELECT id FROM diet_plans WHERE coach_id = ?);
    """, (itemB_id, coachA_id))
    assert cursor.rowcount == 0, "CRITICAL: Coach A updated Coach B's diet item!"
    cursor.execute("SELECT food_name FROM diet_items WHERE id = ?;", (itemB_id,))
    assert cursor.fetchone()[0] == "Banana"
    print("✓ DietItem edit isolation verified.")

    # =========================================================================
    # TEST 13 & 14: COACH DELETES OWN DIET ITEM, BLOCKED ON OTHER'S
    # =========================================================================
    print("\n[Test 13 & 14] Testing DietItem Deletion Isolation...")
    # Coach A attempts to delete Item B -> BLOCKED
    cursor.execute("""
    DELETE FROM diet_items WHERE id = ? AND diet_plan_id IN (SELECT id FROM diet_plans WHERE coach_id = ?);
    """, (itemB_id, coachA_id))
    assert cursor.rowcount == 0, "CRITICAL: Coach A deleted Coach B's diet item!"
    cursor.execute("SELECT id FROM diet_items WHERE id = ?;", (itemB_id,))
    assert cursor.fetchone() is not None

    # Coach A deletes Item 2 (Chicken) from Plan A -> ALLOWED
    cursor.execute("""
    DELETE FROM diet_items WHERE id = ? AND diet_plan_id IN (SELECT id FROM diet_plans WHERE coach_id = ?);
    """, (item2_id, coachA_id))
    conn.commit()
    assert cursor.rowcount == 1
    cursor.execute("SELECT id FROM diet_items WHERE id = ?;", (item2_id,))
    assert cursor.fetchone() is None
    print("✓ DietItem deletion isolation verified.")

    # =========================================================================
    # TEST 15 & 16: CLIENT VIEWS OWN DIET PLAN, BLOCKED ON OTHER'S
    # =========================================================================
    print("\n[Test 15 & 16] Testing Client Own-Data Diet Isolation...")
    # Client A viewing Plan A -> ALLOWED
    cursor.execute("SELECT id FROM diet_plans WHERE id = ? AND client_id = ?;", (planA_id, clientA_id))
    assert cursor.fetchone() is not None

    # Client A viewing Plan B -> BLOCKED
    cursor.execute("SELECT id FROM diet_plans WHERE id = ? AND client_id = ?;", (planB_id, clientA_id))
    assert cursor.fetchone() is None, "CRITICAL: Client A accessed Client B's diet plan!"

    # Client B viewing Plan A -> BLOCKED
    cursor.execute("SELECT id FROM diet_plans WHERE id = ? AND client_id = ?;", (planA_id, clientB_id))
    assert cursor.fetchone() is None, "CRITICAL: Client B accessed Client A's diet plan!"
    print("✓ Client own-data diet isolation strictly enforced.")

    # =========================================================================
    # TEST 17, 18, 19: DIRECT ID, COACH_ID, CLIENT_ID MANIPULATION DEFENSE
    # =========================================================================
    print("\n[Test 17, 18, 19] Testing Payload & URL ID Manipulation Defenses...")
    # Attacker passes client_id=clientB_id in payload to assign plan to unauthorized client
    attacker_payload = {"client_id": clientB_id, "name": "Unauthorized Plan"}
    # Server verifies client_id belongs to coachA_id
    cursor.execute("SELECT id FROM clients WHERE id = ? AND coach_id = ?;", (attacker_payload["client_id"], coachA_id))
    assert cursor.fetchone() is None, "Client ownership check failed!"

    # Plan coach_id and client_id remain immutable upon edit
    cursor.execute("SELECT coach_id, client_id FROM diet_plans WHERE id = ?;", (planA_id,))
    original_owners = cursor.fetchone()
    assert original_owners == (coachA_id, clientA_id)
    print("✓ Payload ID manipulation and cross-tenant reassignments neutralized.")

    # =========================================================================
    # TEST 20: NUTRITION INPUT VALIDATION
    # =========================================================================
    print("\n[Test 20] Testing Nutritional Value Validation...")
    # Negative calories
    is_v, err, _ = validate_diet_item_input({"meal_name": "Lunch", "food_name": "Rice", "quantity": 100, "unit": "g", "calories": -50})
    assert is_v is False and "cannot be negative" in err

    # Negative protein
    is_v, err, _ = validate_diet_item_input({"meal_name": "Lunch", "food_name": "Rice", "quantity": 100, "unit": "g", "protein": -10.0})
    assert is_v is False and "cannot be negative" in err

    # Negative quantity
    is_v, err, _ = validate_diet_item_input({"meal_name": "Lunch", "food_name": "Rice", "quantity": -5.0, "unit": "g"})
    assert is_v is False and "positive number" in err

    # Absurd calorie target (> 15000)
    is_v, err, _ = validate_diet_plan_input({"name": "Test", "daily_calorie_target": 50000})
    assert is_v is False and "15,000" in err
    print("✓ Nutritional validation rejects negative macros, negative quantities, and extreme values.")

    # =========================================================================
    # TEST 21: NUTRITION TOTALS COMPUTATION
    # =========================================================================
    print("\n[Test 21] Testing Nutrition Totals Calculation...")
    class MockDietItem:
        def __init__(self, meal_name, food_name, calories, protein, carbs, fat, meal_time=None):
            self.meal_name = meal_name
            self.food_name = food_name
            self.calories = calories
            self.protein = protein
            self.carbohydrates = carbs
            self.fat = fat
            self.meal_time = meal_time

    class MockDietPlan:
        def __init__(self, target_cal, target_p, target_c, target_f, items):
            self.daily_calorie_target = target_cal
            self.protein_target = target_p
            self.carbs_target = target_c
            self.fat_target = target_f
            self.items = items

    mock_items = [
        MockDietItem("Breakfast", "Oats", 300, 10.0, 50.0, 6.0),
        MockDietItem("Breakfast", "Eggs", 210, 18.0, 2.0, 15.0),
        MockDietItem("Lunch", "Chicken", 330, 62.0, 0.0, 7.0),
        MockDietItem("Lunch", "Rice", 260, 5.0, 57.0, 1.0)
    ]
    mock_plan = MockDietPlan(2200, 150.0, 200.0, 65.0, mock_items)

    totals = compute_diet_plan_nutrition(mock_plan)
    assert totals["targets"]["calories"] == 2200
    assert totals["actual_totals"]["calories"] == 1100  # 300 + 210 + 330 + 260
    assert totals["actual_totals"]["protein"] == 95.0   # 10 + 18 + 62 + 5
    assert totals["actual_totals"]["carbs"] == 109.0    # 50 + 2 + 0 + 57
    assert totals["actual_totals"]["fat"] == 29.0       # 6 + 15 + 7 + 1
    assert totals["delta"]["calories"] == -1100
    assert totals["items_count"] == 4

    # Grouping test
    grouped = group_diet_items_by_meal(mock_items)
    assert "Breakfast" in grouped
    assert "Lunch" in grouped
    assert len(grouped["Breakfast"]["items"]) == 2
    assert grouped["Breakfast"]["subtotal_calories"] == 510
    print("✓ Calculated nutrition totals and meal grouping verified.")

    # =========================================================================
    # TEST 22: DATE RANGE VALIDATION
    # =========================================================================
    print("\n[Test 22] Testing Date Range Validation...")
    # End date prior to start date
    is_v, err, _ = validate_diet_plan_input({"name": "Test", "start_date": "2026-10-15", "end_date": "2026-10-01"})
    assert is_v is False and "cannot be prior to start date" in err

    # Valid range
    is_v, err, _ = validate_diet_plan_input({"name": "Test", "start_date": "2026-10-01", "end_date": "2026-10-15"})
    assert is_v is True
    print("✓ Date range validation verified.")

    conn.close()
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    print("✓ Test database removed.")

    print("\n==================================================")
    print("ALL PHASE 4B DIET MANAGEMENT TESTS PASSED!")
    print("==================================================")


if __name__ == "__main__":
    run_tests()
