"""
FitPulse SaaS - Database Models Package
Initializes Flask-SQLAlchemy and Flask-Migrate extensions.
Exports User, UserRole, Coach, and Client models.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extension instances
db = SQLAlchemy()
migrate = Migrate()

# Import models to ensure they register with SQLAlchemy metadata
from models.user import User, UserRole
from models.coach import Coach
from models.client import Client
from models.exercise import Exercise
from models.diet import DietPlan, DietItem
from models.workout import WorkoutPlan, WorkoutDay, WorkoutExercise

__all__ = [
    "db",
    "migrate",
    "User",
    "UserRole",
    "Coach",
    "Client",
    "Exercise",
    "DietPlan",
    "DietItem",
    "WorkoutPlan",
    "WorkoutDay",
    "WorkoutExercise",
]
