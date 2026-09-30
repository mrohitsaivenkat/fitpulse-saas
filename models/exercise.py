"""
FitPulse SaaS - Exercise Model
Represents the shared, global exercise library across all workouts and tenants.
Exercises are not coach-specific, providing a curated standard database of movements.
"""
from datetime import datetime
from sqlalchemy.sql import func
from models import db


class Exercise(db.Model):
    """
    Exercise entity in the shared movement library.
    Can be linked to any WorkoutExercise across any Coach's WorkoutDay.
    """
    __tablename__ = "exercises"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Exercise Nomenclature & Categorization
    name = db.Column(db.String(150), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False, index=True)  # Strength, Cardio, Mobility, Flexibility, Core, Recovery
    muscle_group = db.Column(db.String(100), nullable=False, index=True)  # Chest, Back, Quads, Hamstrings, Shoulders, Arms, Core, Full Body
    equipment = db.Column(db.String(100), nullable=True)  # Barbell, Dumbbell, Cable, Machine, Bodyweight, Bands, Kettlebell
    difficulty = db.Column(db.String(50), nullable=False, default="Intermediate")  # Beginner, Intermediate, Advanced

    # Instructions & Coaching Form Notes
    instructions = db.Column(db.Text, nullable=True)
    precautions = db.Column(db.Text, nullable=True)

    # Media & Visual Cues
    video_url = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)

    # Status & Audit Timestamps
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    workout_exercises = db.relationship(
        "WorkoutExercise",
        back_populates="exercise",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def to_dict(self) -> dict:
        """Serialize exercise to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "muscle_group": self.muscle_group,
            "equipment": self.equipment,
            "difficulty": self.difficulty,
            "instructions": self.instructions,
            "precautions": self.precautions,
            "video_url": self.video_url,
            "image_url": self.image_url,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Exercise id={self.id} name='{self.name}' category='{self.category}' muscle_group='{self.muscle_group}'>"
