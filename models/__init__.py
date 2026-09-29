"""
FitPulse Database Models Initialization
In Phase 1, this initializes SQLAlchemy and Flask-Migrate extensions.
Full multi-tenant schemas will be defined in Phase 2.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
