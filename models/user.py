"""
FitPulse SaaS - User Model
Defines the core User entity and UserRole enum for authentication and authorization.
"""
from datetime import datetime
from enum import Enum
from sqlalchemy.sql import func
from models import db


class UserRole(str, Enum):
    """Platform roles for Role-Based Access Control (RBAC)."""
    SUPER_ADMIN = "SUPER_ADMIN"
    COACH = "COACH"
    CLIENT = "CLIENT"


class User(db.Model):
    """
    Core User entity.
    All users (super admins, coaches, and clients) have a corresponding User record.
    Coaches and Clients have dedicated 1-to-1 extension profiles.
    """
    __tablename__ = "users"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Authentication & Identity
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=UserRole.CLIENT.value, index=True)

    # Personal Information
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(30), nullable=True)

    # Status Flags
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)

    # Audit Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # 1-to-1 Relationships for specialized roles
    coach = db.relationship(
        "Coach",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    client = db.relationship(
        "Client",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # Phase 2D Relationships: Notifications, Support & Auditing
    notifications = db.relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select"
    )
    support_tickets = db.relationship(
        "SupportTicket",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select"
    )
    audit_logs = db.relationship(
        "AuditLog",
        back_populates="user",
        lazy="select"
    )

    @property
    def full_name(self) -> str:
        """Return the user's formatted full name."""
        return f"{self.first_name} {self.last_name}".strip()

    # Flask-Login Interface Compatibility
    @property
    def is_authenticated(self) -> bool:
        """Return True if the user is authenticated."""
        return True

    @property
    def is_anonymous(self) -> bool:
        """Return False for real users."""
        return False

    def get_id(self) -> str:
        """Return unique string identifier for Flask-Login session storage."""
        return str(self.id)

    # Role Helpers for RBAC (Phase 3B)
    @property
    def is_super_admin(self) -> bool:
        """Return True if the user holds the platform SUPER_ADMIN role."""
        return self.role == UserRole.SUPER_ADMIN.value

    @property
    def is_coach(self) -> bool:
        """Return True if the user is a registered COACH."""
        return self.role == UserRole.COACH.value

    @property
    def is_client(self) -> bool:
        """Return True if the user is an enrolled CLIENT."""
        return self.role == UserRole.CLIENT.value

    def has_role(self, *roles) -> bool:
        """
        Authoritative server-side role check.
        Returns True if the user's role matches any of the supplied roles.
        """
        role_values = [r.value if isinstance(r, UserRole) else str(r).upper() for r in roles]
        return self.role.upper() in role_values

    # Secure Password Handling
    def set_password(self, password: str) -> None:
        """Generate and store a secure cryptographic hash of the password."""
        from services.auth_service import hash_password
        self.password_hash = hash_password(password)

    def check_password(self, password: str) -> bool:
        """Verify the candidate password against the stored cryptographic hash."""
        from services.auth_service import verify_password
        return verify_password(self.password_hash, password)

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Serialize user model to dictionary.
        Password hash is excluded by default for security.
        """
        data = {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "phone": self.phone,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }
        if include_sensitive:
            data["password_hash"] = self.password_hash
        return data

    def __repr__(self) -> str:
        return f"<User id={self.id} email='{self.email}' role='{self.role}'>"
