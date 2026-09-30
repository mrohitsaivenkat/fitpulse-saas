"""
FitPulse SaaS - Notifications, Support Tickets, and Announcements Models
Enables multi-channel platform communication, user notifications, and coach-to-admin support ticketing.
"""
from datetime import datetime
from enum import Enum
from sqlalchemy.sql import func
from models import db


class NotificationType(str, Enum):
    """Event classification for user notifications."""
    SYSTEM = "SYSTEM"
    DIET = "DIET"
    WORKOUT = "WORKOUT"
    PROGRESS = "PROGRESS"
    SUBSCRIPTION = "SUBSCRIPTION"
    SUPPORT = "SUPPORT"
    ANNOUNCEMENT = "ANNOUNCEMENT"


class TicketPriority(str, Enum):
    """Urgency level of coach/client support requests."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class TicketStatus(str, Enum):
    """Lifecycle progression of a support ticket."""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class TargetRole(str, Enum):
    """Audience segmentation for platform-wide announcements."""
    ALL = "ALL"
    SUPER_ADMIN = "SUPER_ADMIN"
    COACH = "COACH"
    CLIENT = "CLIENT"


class Notification(db.Model):
    """
    User notification record (diet alerts, workout assignments, progress reminders, system notices).
    """
    __tablename__ = "notifications"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Recipient User Reference
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Content
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False, default=NotificationType.SYSTEM.value, index=True)

    # Read Status
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)

    # Audit Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationship
    user = db.relationship("User", back_populates="notifications")

    def to_dict(self) -> dict:
        """Serialize notification."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Notification id={self.id} user_id={self.user_id} type='{self.notification_type}' read={self.is_read}>"


class SupportTicket(db.Model):
    """
    Support ticket submitted by a Coach or Client to the platform administration.
    Preserves coach tenant context where applicable.
    """
    __tablename__ = "support_tickets"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Requester Identity
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Optional Coach Workspace Context (nullable if submitted by direct platform user)
    coach_id = db.Column(
        db.Integer,
        db.ForeignKey("coaches.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Ticket Subject & Inquiry Details
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)

    # Priority & Status
    priority = db.Column(db.String(20), nullable=False, default=TicketPriority.MEDIUM.value, index=True)
    status = db.Column(db.String(20), nullable=False, default=TicketStatus.OPEN.value, index=True)

    # Timestamps & Resolution Tracking
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    user = db.relationship("User", back_populates="support_tickets")
    coach = db.relationship("Coach", back_populates="support_tickets")

    def to_dict(self) -> dict:
        """Serialize support ticket."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "coach_id": self.coach_id,
            "subject": self.subject,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

    def __repr__(self) -> str:
        return f"<SupportTicket id={self.id} user_id={self.user_id} priority='{self.priority}' status='{self.status}'>"


class Announcement(db.Model):
    """
    Platform-wide broadcast announcement published by Super Admin.
    Can be targeted to specific roles (ALL, COACH, CLIENT, SUPER_ADMIN).
    """
    __tablename__ = "announcements"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Content
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)

    # Audience Segmentation & Visibility
    target_role = db.Column(db.String(30), nullable=False, default=TargetRole.ALL.value, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    published_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Audit Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self) -> dict:
        """Serialize announcement."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "target_role": self.target_role,
            "is_active": self.is_active,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Announcement id={self.id} title='{self.title}' target='{self.target_role}' active={self.is_active}>"
