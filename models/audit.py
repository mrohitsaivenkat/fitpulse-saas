"""
FitPulse SaaS - Audit Log Model
Provides immutable compliance and forensic tracking for all administrative and operational platform actions.
CRITICAL SECURITY REQUIREMENT:
NEVER store passwords, password hashes, tokens, keys, credentials, or payment secrets in audit descriptions.
"""
from datetime import datetime
from enum import Enum
import re
from sqlalchemy.sql import func
from models import db


class AuditAction(str, Enum):
    """Standardized action verbs for audit trail."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    SUBSCRIPTION_CHANGE = "SUBSCRIPTION_CHANGE"
    CLIENT_CREATED = "CLIENT_CREATED"
    DIET_UPDATED = "DIET_UPDATED"
    WORKOUT_UPDATED = "WORKOUT_UPDATED"
    TRANSFORMATION_PUBLISHED = "TRANSFORMATION_PUBLISHED"


# Regex patterns to detect and redact potential accidental secret exposure
SENSITIVE_PATTERNS = re.compile(
    r"\b(password|token|secret|api[_-]?key|bearer|hash|credit[_-]?card|cvv)\b\s*[:=]\s*(?:['\"][^'\"]*['\"]|\S+)",
    re.IGNORECASE
)


def sanitize_audit_text(text: str) -> str:
    """Sanitize description text by redacting accidental credentials/secrets."""
    if not text:
        return text
    return SENSITIVE_PATTERNS.sub(r"\1: [REDACTED]", text)


class AuditLog(db.Model):
    """
    Forensic audit entry recording who did what, when, and from where.
    Preserves audit history even if user accounts are subsequently deactivated.
    """
    __tablename__ = "audit_logs"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Actor Identity (nullable to preserve historical logs if user is deleted)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Action Metadata
    action = db.Column(db.String(50), nullable=False, index=True)
    entity_type = db.Column(db.String(50), nullable=True, index=True)
    entity_id = db.Column(db.Integer, nullable=True, index=True)

    # Human-Readable Description (Sanitized)
    description = db.Column(db.Text, nullable=False)

    # Client Request Metadata
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    # Timestamp
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationship
    user = db.relationship("User", back_populates="audit_logs")

    @classmethod
    def create_log(cls, action: str, description: str, user_id: int | None = None,
                   entity_type: str | None = None, entity_id: int | None = None,
                   ip_address: str | None = None, user_agent: str | None = None) -> "AuditLog":
        """Factory method that enforces secret sanitization before database persistence."""
        safe_description = sanitize_audit_text(description)
        return cls(
            action=action,
            description=safe_description,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def to_dict(self) -> dict:
        """Serialize audit log."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "description": self.description,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action='{self.action}' user_id={self.user_id} entity='{self.entity_type}:{self.entity_id}'>"
