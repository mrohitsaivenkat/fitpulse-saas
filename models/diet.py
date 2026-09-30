"""
FitPulse SaaS - Diet Plan & Diet Item Models
Defines personalized nutritional prescriptions created by coaches for clients.
Multi-tenant security guarantee: diet_plans.coach_id strictly partitions ownership.
"""
from datetime import datetime, date
from sqlalchemy.sql import func
from models import db


class DietPlan(db.Model):
    """
    DietPlan entity assigned by a Coach to a specific Client.
    Contains target macros and daily calorie targets.
    """
    __tablename__ = "diet_plans"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Multi-Tenant Partition Key: Coach owns this plan
    coach_id = db.Column(
        db.Integer,
        db.ForeignKey("coaches.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Client Assignment Key
    client_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Plan Metadata & Goals
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Nutritional Targets
    daily_calorie_target = db.Column(db.Integer, nullable=True)   # in kcal
    protein_target = db.Column(db.Float, nullable=True)          # in grams
    carbs_target = db.Column(db.Float, nullable=True)            # in grams
    fat_target = db.Column(db.Float, nullable=True)              # in grams

    # Scheduling
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)

    # Audit Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    coach = db.relationship("Coach", back_populates="diet_plans")
    client = db.relationship("Client", back_populates="diet_plans")

    # Ordered meals in this plan
    items = db.relationship(
        "DietItem",
        back_populates="diet_plan",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select"
    )

    @property
    def total_planned_calories(self) -> int:
        """Compute sum of calories across all diet items in this plan."""
        return sum(item.calories or 0 for item in self.items)

    def to_dict(self, include_items: bool = False) -> dict:
        """Serialize diet plan to dictionary."""
        data = {
            "id": self.id,
            "coach_id": self.coach_id,
            "client_id": self.client_id,
            "name": self.name,
            "description": self.description,
            "daily_calorie_target": self.daily_calorie_target,
            "protein_target": self.protein_target,
            "carbs_target": self.carbs_target,
            "fat_target": self.fat_target,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_active": self.is_active,
            "items_count": len(self.items) if self.items else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
        return data

    def __repr__(self) -> str:
        return f"<DietPlan id={self.id} name='{self.name}' coach_id={self.coach_id} client_id={self.client_id}>"


class DietItem(db.Model):
    """
    Individual meal item inside a DietPlan (e.g., Breakfast Oats, Post-Workout Shake).
    """
    __tablename__ = "diet_items"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Diet Plan Foreign Key
    diet_plan_id = db.Column(
        db.Integer,
        db.ForeignKey("diet_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Meal Classification & Food Details
    meal_name = db.Column(db.String(100), nullable=False)  # Breakfast, Mid-Morning, Lunch, Snack, Pre-Workout, Post-Workout, Dinner
    food_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False)        # grams, ml, scoops, pieces, cups

    # Nutritional Breakdown
    calories = db.Column(db.Integer, nullable=True)        # kcal
    protein = db.Column(db.Float, nullable=True)           # grams
    carbohydrates = db.Column(db.Float, nullable=True)     # grams
    fat = db.Column(db.Float, nullable=True)               # grams

    # Timing & Notes
    meal_time = db.Column(db.String(50), nullable=True)    # e.g., "08:00 AM", "Post-Training"
    notes = db.Column(db.Text, nullable=True)

    # Audit Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    diet_plan = db.relationship("DietPlan", back_populates="items")

    def to_dict(self) -> dict:
        """Serialize diet item to dictionary."""
        return {
            "id": self.id,
            "diet_plan_id": self.diet_plan_id,
            "meal_name": self.meal_name,
            "food_name": self.food_name,
            "quantity": self.quantity,
            "unit": self.unit,
            "calories": self.calories,
            "protein": self.protein,
            "carbohydrates": self.carbohydrates,
            "fat": self.fat,
            "meal_time": self.meal_time,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<DietItem id={self.id} meal='{self.meal_name}' food='{self.food_name}' plan_id={self.diet_plan_id}>"
