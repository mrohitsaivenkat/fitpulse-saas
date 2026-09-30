"""
FitPulse SaaS - Subscription Plan and Coach Subscription Models
Provides multi-tenant subscription tiers and lifecycle history for independent coaches.
Configurable plan pricing, client caps, storage quotas, and feature flags.
"""
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy.sql import func
from models import db


class BillingPeriod(str, Enum):
    """Supported SaaS billing cycles."""
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class SubscriptionStatus(str, Enum):
    """Coach subscription lifecycle states."""
    TRIAL = "TRIAL"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    SUSPENDED = "SUSPENDED"
    PENDING = "PENDING"


class SubscriptionPlan(db.Model):
    """
    SaaS Tier definition (e.g. Starter, Professional, Enterprise).
    Source of truth for coach plan capabilities, limits, and pricing.
    """
    __tablename__ = "subscription_plans"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Tier Identity
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)

    # Pricing & Billing Cycle
    price = db.Column(db.Float, nullable=False, default=0.0)
    billing_period = db.Column(db.String(20), nullable=False, default=BillingPeriod.MONTHLY.value)

    # Capacity Limits & Quotas
    max_clients = db.Column(db.Integer, nullable=False, default=15)
    storage_limit = db.Column(db.Integer, nullable=False, default=5120)  # in Megabytes (5GB)

    # Feature Toggles
    analytics_enabled = db.Column(db.Boolean, default=False, nullable=False)
    ml_enabled = db.Column(db.Boolean, default=False, nullable=False)

    # State & Audit Timestamps
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships (Prevent cascade deletion of plans with active/historical subscriptions)
    subscriptions = db.relationship(
        "Subscription",
        back_populates="plan",
        passive_deletes=False,
        lazy="select"
    )

    def to_dict(self) -> dict:
        """Serialize plan details."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "billing_period": self.billing_period,
            "max_clients": self.max_clients,
            "storage_limit_mb": self.storage_limit,
            "analytics_enabled": self.analytics_enabled,
            "ml_enabled": self.ml_enabled,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<SubscriptionPlan id={self.id} name='{self.name}' price={self.price} billing={self.billing_period}>"


class Subscription(db.Model):
    """
    Coach subscription instance.
    Preserves full subscription history (trials, renewals, upgrades, cancellations).
    """
    __tablename__ = "subscriptions"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Multi-Tenant Coach Foreign Key
    coach_id = db.Column(
        db.Integer,
        db.ForeignKey("coaches.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Plan Tier Reference
    plan_id = db.Column(
        db.Integer,
        db.ForeignKey("subscription_plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Subscription Lifecycle State
    status = db.Column(db.String(20), nullable=False, default=SubscriptionStatus.TRIAL.value, index=True)

    # Period Dates
    start_date = db.Column(db.DateTime(timezone=True), nullable=False, default=func.now())
    end_date = db.Column(db.DateTime(timezone=True), nullable=True)
    trial_start = db.Column(db.DateTime(timezone=True), nullable=True)
    trial_end = db.Column(db.DateTime(timezone=True), nullable=True)

    # Renewal & External Gateway Reference (payment agnostic)
    auto_renew = db.Column(db.Boolean, default=True, nullable=False)
    external_subscription_id = db.Column(db.String(150), nullable=True, index=True)

    # Audit Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    coach = db.relationship("Coach", back_populates="subscriptions")
    plan = db.relationship("SubscriptionPlan", back_populates="subscriptions")

    @property
    def is_currently_active(self) -> bool:
        """Evaluate if the subscription grants platform access."""
        return self.status in (SubscriptionStatus.ACTIVE.value, SubscriptionStatus.TRIAL.value)

    def to_dict(self) -> dict:
        """Serialize subscription instance."""
        return {
            "id": self.id,
            "coach_id": self.coach_id,
            "plan_id": self.plan_id,
            "plan_name": self.plan.name if self.plan else None,
            "status": self.status,
            "is_active": self.is_currently_active,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "trial_start": self.trial_start.isoformat() if self.trial_start else None,
            "trial_end": self.trial_end.isoformat() if self.trial_end else None,
            "auto_renew": self.auto_renew,
            "external_subscription_id": self.external_subscription_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Subscription id={self.id} coach_id={self.coach_id} plan_id={self.plan_id} status='{self.status}'>"
