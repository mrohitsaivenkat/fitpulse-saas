"""
FitPulse SaaS - Transformation and Transformation Consent Models
Defines showcase client case studies paired with explicit, legally auditable consent records.
Public display rule:
A transformation can be publicly displayed ONLY when:
transformation.is_public == True
AND an applicable consent record exists with:
consent_given == True
AND revoked_at IS NULL
"""
from datetime import datetime
from sqlalchemy.sql import func
from models import db


class Transformation(db.Model):
    """
    Client achievement transformation showcase.
    Belongs jointly to the Coach (tenant) and Client (individual).
    DEFAULT PRIVACY: is_public is FALSE by default.
    """
    __tablename__ = "transformations"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Multi-Tenant Partition Key: Coach who guided the transformation
    coach_id = db.Column(
        db.Integer,
        db.ForeignKey("coaches.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Client Association Key: Client whose physique is showcased
    client_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Narrative Content
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Visual References (File paths)
    before_photo = db.Column(db.String(255), nullable=True)
    after_photo = db.Column(db.String(255), nullable=True)

    # Timeline & Metrics Summary
    duration_text = db.Column(db.String(100), nullable=True)       # e.g., "16 Weeks", "6 Months"
    achievement_text = db.Column(db.Text, nullable=True)           # e.g., "-12kg Fat Loss, +5kg Muscle"

    # Public Visibility Control
    is_public = db.Column(db.Boolean, default=False, nullable=False, index=True)
    published_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Audit Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    coach = db.relationship("Coach", back_populates="transformations")
    client = db.relationship("Client", back_populates="transformations")
    consents = db.relationship(
        "TransformationConsent",
        back_populates="transformation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select"
    )

    @property
    def is_eligible_for_public_display(self) -> bool:
        """
        Enforce strict privacy boundary:
        Transformation can only be publicly visible if coach published it (is_public=True)
        AND client has actively granted consent which has not been revoked.
        """
        if not self.is_public:
            return False
        if not self.consents:
            return False
        # Check if there is at least one active, unrevoked consent
        return any(c.consent_given and c.revoked_at is None for c in self.consents)

    def to_dict(self, include_consent: bool = False) -> dict:
        """Serialize transformation entity to dictionary."""
        data = {
            "id": self.id,
            "coach_id": self.coach_id,
            "client_id": self.client_id,
            "title": self.title,
            "description": self.description,
            "before_photo": self.before_photo,
            "after_photo": self.after_photo,
            "duration_text": self.duration_text,
            "achievement_text": self.achievement_text,
            "is_public": self.is_public,
            "is_eligible_for_public_display": self.is_eligible_for_public_display,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_consent:
            data["consents"] = [c.to_dict() for c in self.consents]
        return data

    def __repr__(self) -> str:
        return f"<Transformation id={self.id} title='{self.title}' coach_id={self.coach_id} client_id={self.client_id} public={self.is_public}>"


class TransformationConsent(db.Model):
    """
    Explicit, timestamped legal consent granted by a Client to showcase their transformation.
    Allows clients to grant or revoke consent at any time.
    """
    __tablename__ = "transformation_consents"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Transformation Association Key
    transformation_id = db.Column(
        db.Integer,
        db.ForeignKey("transformations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Client Identity Key
    client_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Consent Grant State
    consent_given = db.Column(db.Boolean, default=False, nullable=False, index=True)
    consent_date = db.Column(db.DateTime(timezone=True), nullable=True)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Exact Legal Consent Language Agreed To
    consent_text = db.Column(db.Text, nullable=True)

    # Audit Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    transformation = db.relationship("Transformation", back_populates="consents")
    client = db.relationship("Client", back_populates="transformation_consents")

    def to_dict(self) -> dict:
        """Serialize consent record."""
        return {
            "id": self.id,
            "transformation_id": self.transformation_id,
            "client_id": self.client_id,
            "consent_given": self.consent_given,
            "consent_date": self.consent_date.isoformat() if self.consent_date else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "is_currently_valid": self.consent_given and self.revoked_at is None,
            "consent_text": self.consent_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<TransformationConsent id={self.id} trans_id={self.transformation_id} client_id={self.client_id} active={self.consent_given and self.revoked_at is None}>"
