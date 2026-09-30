"""
FitPulse SaaS - Workout Models (Plan, Day, and Workout Exercise)
Constructs structured training routines assigned by Coaches to Clients.
Multi-tenant security guarantee: workout_plans.coach_id strictly partitions ownership.
"""
from datetime import datetime, date
from sqlalchemy.sql import func
from models import db


class WorkoutPlan(db.Model):
    """
    WorkoutPlan entity representing a mesocycle or routine assigned by a Coach to a Client.
    """
    __tablename__ = "workout_plans"

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

    # Plan Metadata
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Duration & Scheduling
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)

    # Audit Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    coach = db.relationship("Coach", back_populates="workout_plans")
    client = db.relationship("Client", back_populates="workout_plans")

    # Workout Days hierarchy
    days = db.relationship(
        "WorkoutDay",
        back_populates="workout_plan",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="WorkoutDay.day_number",
        lazy="select"
    )

    def to_dict(self, include_days: bool = False) -> dict:
        """Serialize workout plan to dictionary."""
        data = {
            "id": self.id,
            "coach_id": self.coach_id,
            "client_id": self.client_id,
            "name": self.name,
            "description": self.description,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_active": self.is_active,
            "days_count": len(self.days) if self.days else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_days:
            data["days"] = [day.to_dict(include_exercises=True) for day in self.days]
        return data

    def __repr__(self) -> str:
        return f"<WorkoutPlan id={self.id} name='{self.name}' coach_id={self.coach_id} client_id={self.client_id}>"


class WorkoutDay(db.Model):
    """
    WorkoutDay entity inside a WorkoutPlan (e.g., 'Day 1: Upper Body', 'Monday: Legs & Core').
    Does not assume a fixed 7-day calendar; supports any training split.
    """
    __tablename__ = "workout_days"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Workout Plan Link
    workout_plan_id = db.Column(
        db.Integer,
        db.ForeignKey("workout_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Day Identification
    day_name = db.Column(db.String(100), nullable=False)  # e.g., "Day 1", "Push Day", "Monday"
    day_number = db.Column(db.Integer, nullable=False, default=1)
    focus = db.Column(db.String(150), nullable=True)       # e.g., "Chest & Triceps Hypertrophy"
    notes = db.Column(db.Text, nullable=True)

    # Audit Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    workout_plan = db.relationship("WorkoutPlan", back_populates="days")

    # Exercises mapped to this day
    exercises = db.relationship(
        "WorkoutExercise",
        back_populates="workout_day",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="WorkoutExercise.order_index",
        lazy="select"
    )

    def to_dict(self, include_exercises: bool = False) -> dict:
        """Serialize workout day to dictionary."""
        data = {
            "id": self.id,
            "workout_plan_id": self.workout_plan_id,
            "day_name": self.day_name,
            "day_number": self.day_number,
            "focus": self.focus,
            "notes": self.notes,
            "exercises_count": len(self.exercises) if self.exercises else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_exercises:
            data["exercises"] = [ex.to_dict() for ex in self.exercises]
        return data

    def __repr__(self) -> str:
        return f"<WorkoutDay id={self.id} name='{self.day_name}' plan_id={self.workout_plan_id}>"


class WorkoutExercise(db.Model):
    """
    Junction entity specifying a movement from the shared Exercise library
    performed in a specific WorkoutDay with specific volume/intensity parameters.
    """
    __tablename__ = "workout_exercises"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Workout Day Link
    workout_day_id = db.Column(
        db.Integer,
        db.ForeignKey("workout_days.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Shared Exercise Link
    exercise_id = db.Column(
        db.Integer,
        db.ForeignKey("exercises.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Prescription Parameters
    sets = db.Column(db.Integer, nullable=False, default=3)
    reps = db.Column(db.String(50), nullable=True)          # e.g., "8-12", "5x5", "AMRAP"
    duration = db.Column(db.Integer, nullable=True)         # Seconds (for isometric holds, planks, cardio)
    rest_seconds = db.Column(db.Integer, nullable=True, default=90)
    order_index = db.Column(db.Integer, nullable=False, default=1)
    notes = db.Column(db.Text, nullable=True)               # e.g., "2-second pause at bottom"

    # Audit Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    workout_day = db.relationship("WorkoutDay", back_populates="exercises")
    exercise = db.relationship("Exercise", back_populates="workout_exercises")

    def to_dict(self) -> dict:
        """Serialize workout exercise to dictionary."""
        return {
            "id": self.id,
            "workout_day_id": self.workout_day_id,
            "exercise_id": self.exercise_id,
            "exercise_name": self.exercise.name if self.exercise else None,
            "sets": self.sets,
            "reps": self.reps,
            "duration": self.duration,
            "rest_seconds": self.rest_seconds,
            "order_index": self.order_index,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<WorkoutExercise id={self.id} day_id={self.workout_day_id} exercise_id={self.exercise_id} order={self.order_index}>"
