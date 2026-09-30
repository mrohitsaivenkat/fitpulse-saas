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
from models.progress import Progress, Measurement, ProgressPhoto, PhotoType
from models.transformation import Transformation, TransformationConsent
from models.review import Review
from models.subscription import SubscriptionPlan, Subscription, BillingPeriod, SubscriptionStatus
from models.communication import (
    Notification,
    NotificationType,
    SupportTicket,
    TicketPriority,
    TicketStatus,
    Announcement,
    TargetRole,
)
from models.audit import AuditLog, AuditAction

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
    "Progress",
    "Measurement",
    "ProgressPhoto",
    "PhotoType",
    "Transformation",
    "TransformationConsent",
    "Review",
    "SubscriptionPlan",
    "Subscription",
    "BillingPeriod",
    "SubscriptionStatus",
    "Notification",
    "NotificationType",
    "SupportTicket",
    "TicketPriority",
    "TicketStatus",
    "Announcement",
    "TargetRole",
    "AuditLog",
    "AuditAction",
]
