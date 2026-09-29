import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the application
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file if it exists
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "fitpulse-dev-secret-key-change-in-production-19283746")
    
    # Database Settings
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'fitpulse_dev.db'}")
    # Render and Heroku use 'postgres://', SQLAlchemy 1.4+ expects 'postgresql://'
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Configurations
    UPLOAD_FOLDER = BASE_DIR / os.getenv("UPLOAD_FOLDER", "static/uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", 16)) * 1024 * 1024  # 16 MB max
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    
    # Security and Session Settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 86400 * int(os.getenv("PERMANENT_SESSION_LIFETIME_DAYS", 7))


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration for Render / Cloud deployment."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    
    # Strict validation of secret key in production
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        assert os.getenv("SECRET_KEY"), "SECRET_KEY environment variable MUST be set in production!"


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
