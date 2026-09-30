"""
FitPulse SaaS - Application Factory
Initializes Flask, SQLAlchemy, Flask-Migrate, and registers blueprints.
"""
import os
from flask import Flask, jsonify, send_from_directory
from config import config
from models import db, migrate, User
from routes import public_bp
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.coach import coach_bp
from routes.client import client_bp

# Flask-Login initialization (with graceful fallback if not present)
try:
    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.login_view = "auth.login_view"
    login_manager.login_message = "Please sign in to access your coaching workspace."
    login_manager.login_message_category = "info"
except ImportError:
    login_manager = None


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
        static_url_path="/static",
        template_folder="templates"
    )
    app.config.from_object(config.get(config_name, config["default"]))

    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Initialize Authentication Extension
    if login_manager is not None:
        login_manager.init_app(app)

        @login_manager.user_loader
        def load_user(user_id):
            return db.session.query(User).filter_by(id=int(user_id)).first()

    # Ensure Upload Directories Exist
    upload_dir = app.config.get("UPLOAD_FOLDER")
    if upload_dir:
        os.makedirs(upload_dir, exist_ok=True)

    # Register Blueprints
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(coach_bp)
    app.register_blueprint(client_bp)

    # Initialize CSRF Protection
    from services.csrf_service import init_csrf_app
    init_csrf_app(app)

    # Authenticated Media Streaming Route (Prevents Direct Unauthenticated File Access)
    from services.media_service import stream_authenticated_photo
    @app.route("/api/v1/media/photos/<int:photo_id>", methods=["GET"])
    def authenticated_photo_stream(photo_id: int):
        """Streams private progress photo only after strict authentication and ownership checks."""
        return stream_authenticated_photo(photo_id)

    # Security Headers Hook
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content-Security-Policy (Allow local styles, Google Fonts, and Chart.js)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'self';"
        )
        response.headers["Content-Security-Policy"] = csp

        # Strict-Transport-Security in HTTPS / production environments
        if os.getenv("FLASK_ENV") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response

    # Global Error Handlers (Clean JSON / standard status - zero stack trace exposure)
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad Request", "status_code": 400}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"error": "Authentication required. Please log in.", "status_code": 401}), 401

    @app.errorhandler(403)
    def forbidden(error):
        from flask import render_template, request
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"error": "Forbidden - Access Denied", "status_code": 403}), 403
        try:
            from services.auth_decorators import get_authenticated_user
            return render_template("errors/403.html", user=get_authenticated_user()), 403
        except Exception:
            return jsonify({"error": "Forbidden - Access Denied", "status_code": 403}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource Not Found", "status_code": 404}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({"error": "Method Not Allowed", "status_code": 405}), 405

    @app.errorhandler(429)
    def too_many_requests(error):
        return jsonify({"error": "Too Many Requests. Please slow down.", "status_code": 429}), 429

    @app.errorhandler(500)
    def server_error(error):
        # Explicitly sanitize error output; zero database queries or traces exposed
        return jsonify({"error": "Internal Server Error", "status_code": 500}), 500

    return app


# Production / Gunicorn entry point
app = create_app(os.getenv("FLASK_ENV", "development"))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("FLASK_ENV", "development") == "development"
    app.run(host=host, port=port, debug=debug)
