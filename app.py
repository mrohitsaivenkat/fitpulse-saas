import os
from flask import Flask, render_template, jsonify
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

    app = Flask(__name__)
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

    # Global Error Handlers (No stack traces in production)
    @app.errorhandler(400)
    def bad_request(error):
        return render_template("errors/400.html", error=error), 400

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html", error=error), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html", error=error), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("errors/500.html", error=error), 500

    return app


# Production / Gunicorn entry point
app = create_app(os.getenv("FLASK_ENV", "development"))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("FLASK_ENV", "development") == "development"
    app.run(host=host, port=port, debug=debug)
