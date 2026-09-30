"""
FitPulse SaaS - Application Factory
Initializes Flask, SQLAlchemy, Flask-Migrate, and registers blueprints.
"""
import os
from flask import Flask, jsonify, send_from_directory
from config import config
from models import db, migrate
from routes import public_bp


def create_app(config_name=None):
    """
    Application Factory for FitPulse SaaS.
    Allows easy switching between development, testing, and production.
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(
        __name__,
        static_folder="static",
        static_url_path="/static"
    )
    app.config.from_object(config.get(config_name, config["default"]))

    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Ensure Upload Directories Exist
    upload_dir = app.config.get("UPLOAD_FOLDER")
    if upload_dir:
        os.makedirs(upload_dir, exist_ok=True)

    # Register Blueprints
    app.register_blueprint(public_bp)

    # Security Headers Hook
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    # Global Error Handlers (Clean JSON / standard status)
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad Request", "status_code": 400}), 400

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({"error": "Forbidden - Access Denied", "status_code": 403}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource Not Found", "status_code": 404}), 404

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({"error": "Internal Server Error", "status_code": 500}), 500

    return app


# Production / Gunicorn entry point
app = create_app(os.getenv("FLASK_ENV", "development"))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("FLASK_ENV", "development") == "development"
    app.run(host=host, port=port, debug=debug)
