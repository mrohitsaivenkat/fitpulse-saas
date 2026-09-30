"""
FitPulse SaaS - Coach Model (Tenant / Workspace Entity)
In the multi-tenant architecture, each Coach represents a distinct tenant/workspace.
All client records, workouts, diets, and data partition by coach_id.
"""
from datetime import datetime
from sqlalchemy.sql import func
from models import db


class Coach(db.Model):
    """
    Coach entity representing an independent fitness coaching business/tenant.
    Holds the coach's public profile, business branding, and multi-tenant client roster.
    """
    __tablename__ = "coaches"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # 1-to-1 Link to User Authentication Record
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # Coaching Business & Brand Identity
    business_name = db.Column(db.String(150), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    specialization = db.Column(db.String(150), nullable=True)  # e.g., Hypertrophy, Powerlifting, Fat Loss
    experience_years = db.Column(db.Integer, default=0, nullable=False)
    profile_image = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(150), nullable=True)

    # Online & Social Media Presence
    website = db.Column(db.String(255), nullable=True)
    instagram = db.Column(db.String(100), nullable=True)
    facebook = db.Column(db.String(100), nullable=True)
    youtube = db.Column(db.String(100), nullable=True)

    # Public Discovery Setting
    is_public = db.Column(db.Boolean, default=True, nullable=False, index=True)

    # Audit Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="coach")

    # Multi-Tenant Client Roster: 1 Coach has many Clients
    clients = db.relationship(
        "Client",
        back_populates="coach",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select"
    )

    # Multi-Tenant Prescriptions: Coach owns Diet Plans and Workout Plans
    diet_plans = db.relationship(
        "DietPlan",
        back_populates="coach",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select"
    )
    workout_plans = db.relationship(
        "WorkoutPlan",
        back_populates="coach",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select"
    )

    @property
    def total_clients_count(self) -> int:
        """Return the total number of enrolled clients in this coach's workspace."""
        return len(self.clients) if self.clients else 0

    @property
    def active_clients_count(self) -> int:
        """Return the number of currently active clients."""
        if not self.clients:
            return 0
        return sum(1 for c in self.clients if c.is_active)

    def to_dict(self) -> dict:
        """Serialize coach entity to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "business_name": self.business_name,
            "bio": self.bio,
            "specialization": self.specialization,
            "experience_years": self.experience_years,
            "profile_image": self.profile_image,
            "location": self.location,
            "website": self.website,
            "instagram": self.instagram,
            "facebook": self.facebook,
            "youtube": self.youtube,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Coach id={self.id} business='{self.business_name}' user_id={self.user_id}>"
