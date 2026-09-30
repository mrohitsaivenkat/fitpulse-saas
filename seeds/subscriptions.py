"""
FitPulse SaaS - Initial Subscription Plans Seed Data
Provides foundational tier configurations for testing coach provisioning, quotas, and capabilities.
Note: Contains ONLY generic tier configurations. No fake coaches or fake payment records.
"""

INITIAL_SUBSCRIPTION_PLANS_SEED = [
    {
        "name": "Starter",
        "description": "Ideal for independent personal trainers launching their remote coaching business.",
        "price": 29.0,
        "billing_period": "MONTHLY",
        "max_clients": 15,
        "storage_limit": 5120,          # 5 GB in MB
        "analytics_enabled": False,
        "ml_enabled": False,
        "is_active": True,
    },
    {
        "name": "Professional",
        "description": "For established coaches scaling their roster with analytics and high-volume client management.",
        "price": 79.0,
        "billing_period": "MONTHLY",
        "max_clients": 50,
        "storage_limit": 25600,         # 25 GB in MB
        "analytics_enabled": True,
        "ml_enabled": False,
        "is_active": True,
    },
    {
        "name": "Enterprise Elite",
        "description": "Full-featured tier with dedicated storage, advanced analytics, and AI/ML capabilities.",
        "price": 149.0,
        "billing_period": "MONTHLY",
        "max_clients": 200,
        "storage_limit": 102400,        # 100 GB in MB
        "analytics_enabled": True,
        "ml_enabled": True,
        "is_active": True,
    },
]


def seed_subscription_plans(db_session, SubscriptionPlanModel):
    """
    Idempotent seeding helper: inserts default SaaS plans if not already present.
    """
    added_count = 0
    for item in INITIAL_SUBSCRIPTION_PLANS_SEED:
        existing = db_session.query(SubscriptionPlanModel).filter_by(name=item["name"]).first()
        if not existing:
            plan = SubscriptionPlanModel(**item)
            db_session.add(plan)
            added_count += 1
    if added_count > 0:
        db_session.commit()
    return added_count
