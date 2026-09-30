"""
FitPulse SaaS - Progress, Measurements, and Progress Photo Models
Encapsulates private biometric tracking, anatomical circumference records, and visual progress photos.
Multi-tenant & Privacy: Strictly private client data scoped to Client -> Coach hierarchy.
"""
from datetime import datetime, date
from enum import Enum
from sqlalchemy.sql import func
from models import db


class PhotoType(str, Enum):
    """Standard physiological orientation for progress photography."""
    FRONT = "FRONT"
    SIDE = "SIDE"
    BACK = "BACK"
    OTHER = "OTHER"


class Progress(db.Model):
    """
    Biometric progress entry logged over time (weight, body fat %, muscle mass, key circumferences).
    Strictly private to the client and their authorized coach.
    """
    __tablename__ = "progress"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Client Association Key
    client_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Date of entry
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)

    # Biometric Metrics
    weight = db.Column(db.Float, nullable=True)                  # in kg
    body_fat_percentage = db.Column(db.Float, nullable=True)     # e.g., 14.5%
    muscle_mass = db.Column(db.Float, nullable=True)             # in kg

    # Circumference Metrics (in cm)
    waist = db.Column(db.Float, nullable=True)
    chest = db.Column(db.Float, nullable=True)
    arms = db.Column(db.Float, nullable=True)
    thighs = db.Column(db.Float, nullable=True)
    hips = db.Column(db.Float, nullable=True)

    # Notes & Qualitative Context
    notes = db.Column(db.Text, nullable=True)

    # Audit Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    client = db.relationship("Client", back_populates="progress_records")

    def to_dict(self) -> dict:
        """Serialize progress record to dictionary."""
        return {
            "id": self.id,
            "client_id": self.client_id,
            "date": self.date.isoformat() if self.date else None,
            "weight": self.weight,
            "body_fat_percentage": self.body_fat_percentage,
            "muscle_mass": self.muscle_mass,
            "waist": self.waist,
            "chest": self.chest,
            "arms": self.arms,
            "thighs": self.thighs,
            "hips": self.hips,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Progress id={self.id} client_id={self.client_id} date={self.date} weight={self.weight}>"


class Measurement(db.Model):
    """
    Comprehensive anatomical measurement record for fine-grained body composition tracking.
    Private client data.
    """
    __tablename__ = "measurements"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Client Association Key
    client_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Date of Measurement
    measurement_date = db.Column(db.Date, nullable=False, default=date.today, index=True)

    # Primary Biometrics
    weight = db.Column(db.Float, nullable=True)
    body_fat_percentage = db.Column(db.Float, nullable=True)

    # Granular Circumferences (in cm)
    neck = db.Column(db.Float, nullable=True)
    shoulders = db.Column(db.Float, nullable=True)
    chest = db.Column(db.Float, nullable=True)
    waist = db.Column(db.Float, nullable=True)
    abdomen = db.Column(db.Float, nullable=True)
    hips = db.Column(db.Float, nullable=True)
    left_arm = db.Column(db.Float, nullable=True)
    right_arm = db.Column(db.Float, nullable=True)
    left_thigh = db.Column(db.Float, nullable=True)
    right_thigh = db.Column(db.Float, nullable=True)

    # Notes
    notes = db.Column(db.Text, nullable=True)

    # Audit Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    client = db.relationship("Client", back_populates="measurements")

    def to_dict(self) -> dict:
        """Serialize measurement record to dictionary."""
        return {
            "id": self.id,
            "client_id": self.client_id,
            "measurement_date": self.measurement_date.isoformat() if self.measurement_date else None,
            "weight": self.weight,
            "body_fat_percentage": self.body_fat_percentage,
            "neck": self.neck,
            "shoulders": self.shoulders,
            "chest": self.chest,
            "waist": self.waist,
            "abdomen": self.abdomen,
            "hips": self.hips,
            "left_arm": self.left_arm,
            "right_arm": self.right_arm,
            "left_thigh": self.left_thigh,
            "right_thigh": self.right_thigh,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Measurement id={self.id} client_id={self.client_id} date={self.measurement_date}>"


class ProgressPhoto(db.Model):
    """
    Visual physique tracking photo.
    STRICT PRIVACY GUARANTEE: is_private is TRUE by default.
    Only stores secure relative file path references (no binary blobs in database).
    """
    __tablename__ = "progress_photos"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Client Association Key
    client_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Photo Metadata
    photo_type = db.Column(db.String(20), nullable=False, default=PhotoType.FRONT.value)  # FRONT, SIDE, BACK, OTHER
    file_path = db.Column(db.String(255), nullable=False)                                # Secure storage reference path
    captured_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    notes = db.Column(db.Text, nullable=True)

    # Privacy Enforcement Flag
    is_private = db.Column(db.Boolean, default=True, nullable=False, index=True)

    # Audit Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    client = db.relationship("Client", back_populates="progress_photos")

    def to_dict(self) -> dict:
        """Serialize photo record to dictionary without exposing filesystem internals."""
        return {
            "id": self.id,
            "client_id": self.client_id,
            "photo_type": self.photo_type,
            "file_path": self.file_path,
            "captured_at": self.captured_at.isoformat() if self.captured_at else None,
            "notes": self.notes,
            "is_private": self.is_private,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<ProgressPhoto id={self.id} client_id={self.client_id} type='{self.photo_type}' private={self.is_private}>"
