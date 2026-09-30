"""
FitPulse SaaS - Client Model (Tenant-Scoped Member Entity)
Every Client belongs to exactly one Coach workspace (enforced by coach_id foreign key).
The coach_id column is strictly indexed to guarantee tenant isolation and performant partition queries.
"""
from datetime import datetime, date
from sqlalchemy.sql import func
from models import db


class Client(db.Model):
    """
    Client profile entity representing a trainee/athlete assigned to a specific Coach.
    Tenant isolation guarantee: All client access is verified against coach_id.
    """
    __tablename__ = "clients"

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

    # Multi-Tenant Partition Key: Every client belongs to exactly one Coach
    coach_id = db.Column(
        db.Integer,
        db.ForeignKey("coaches.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Physical & Biometric Baseline
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=True)          # e.g., Male, Female, Other, Prefer not to say
    height = db.Column(db.Float, nullable=True)               # Stored in centimeters (cm)
    current_weight = db.Column(db.Float, nullable=True)       # Stored in kilograms (kg)

    # Fitness Profile & Goals
    goal = db.Column(db.String(200), nullable=True)           # e.g., Hypertrophy, 10kg Fat Loss, Marathon Prep
    activity_level = db.Column(db.String(50), nullable=True)  # Sedentary, Lightly Active, Moderately Active, Very Active
    notes = db.Column(db.Text, nullable=True)                 # Coach's private notes regarding client

    # Client Status & Onboarding
    joined_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)

    # Audit Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="client")
    coach = db.relationship("Coach", back_populates="clients")

    # Client Prescriptions (Scoped to this client & coach)
    diet_plans = db.relationship(
        "DietPlan",
        back_populates="client",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select"
    )
    workout_plans = db.relationship(
        "WorkoutPlan",
        back_populates="client",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select"
    )

    # Phase 2C Tracking: Biometrics, Measurements & Photos
    progress_records = db.relationship(
        "Progress",
        back_populates="client",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select"
    )
    measurements = db.relationship(
        "Measurement",
        back_populates="client",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select"
    )
    progress_photos = db.relationship(
        "ProgressPhoto",
        back_populates="client",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select"
    )

    # Phase 2C Social Proof & Consent
    transformations = db.relationship(
        "Transformation",
        back_populates="client",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select"
    )
    transformation_consents = db.relationship(
        "TransformationConsent",
        back_populates="client",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select"
    )
    reviews = db.relationship(
        "Review",
        back_populates="client",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select"
    )

    @property
    def age(self) -> int | None:
        """Calculate the client's current age from date_of_birth."""
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    def to_dict(self) -> dict:
        """Serialize client entity to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "coach_id": self.coach_id,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "age": self.age,
            "gender": self.gender,
            "height": self.height,
            "current_weight": self.current_weight,
            "goal": self.goal,
            "activity_level": self.activity_level,
            "notes": self.notes,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Client id={self.id} user_id={self.user_id} coach_id={self.coach_id}>"
