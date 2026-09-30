"""
FitPulse SaaS - Review Model
Authentic client reviews and ratings associated with verified Coach-Client relationships.
Multi-Tenant & Quality Control:
- coach_id and client_id link directly to verified platform entities.
- Reviews require approval (is_approved=True) and public visibility (is_public=True) before display.
- Rating is strictly validated with a database check constraint (1 to 5).
"""
from datetime import datetime
from sqlalchemy import CheckConstraint
from sqlalchemy.sql import func
from models import db


class Review(db.Model):
    """
    Client review of coaching service.
    Ratings are restricted to integers between 1 and 5.
    Defaults to is_public=False and is_approved=False for moderation safety.
    """
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
    )

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Multi-Tenant Partition Key: Coach who received the review
    coach_id = db.Column(
        db.Integer,
        db.ForeignKey("coaches.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Client Association Key: Client who authored the review
    client_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Review Content & Rating
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5
    title = db.Column(db.String(150), nullable=True)
    content = db.Column(db.Text, nullable=False)

    # Moderation & Visibility Flags
    is_public = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_approved = db.Column(db.Boolean, default=False, nullable=False, index=True)

    # Audit Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    coach = db.relationship("Coach", back_populates="reviews")
    client = db.relationship("Client", back_populates="reviews")

    @property
    def is_eligible_for_public_display(self) -> bool:
        """Review must be marked public and approved by moderation."""
        return self.is_public and self.is_approved

    def to_dict(self) -> dict:
        """Serialize review to dictionary."""
        return {
            "id": self.id,
            "coach_id": self.coach_id,
            "client_id": self.client_id,
            "rating": self.rating,
            "title": self.title,
            "content": self.content,
            "is_public": self.is_public,
            "is_approved": self.is_approved,
            "is_eligible_for_public_display": self.is_eligible_for_public_display,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Review id={self.id} coach_id={self.coach_id} client_id={self.client_id} rating={self.rating}>"
