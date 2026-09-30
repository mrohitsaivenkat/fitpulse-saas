"""
FitPulse SaaS - Media & Upload Security Service (Phase 3D)
Provides comprehensive file upload security and authenticated media streaming:
- Whitelist validation of extensions: png, jpg, jpeg, webp.
- Rejection of executable scripts (.php, .exe, .sh, .py, .html, .svg, .js).
- Path traversal defense: os.path.basename sanitation and rejection of .. characters.
- Cryptographically random, non-predictable UUID4 filenames.
- Authenticated streaming controller: Private athlete progress photos cannot be accessed
  without active session authentication and ownership verification (Client own-data or Coach roster).
"""
import os
import uuid
import mimetypes
from typing import Optional, Tuple
from functools import wraps

try:
    from flask import request, jsonify, send_from_directory, current_app
    _HAS_FLASK = True
except ImportError:
    _HAS_FLASK = False
    request = None
    jsonify = None
    send_from_directory = None
    current_app = None

from services.auth_decorators import get_authenticated_user

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
DANGEROUS_EXTENSIONS = {
    "exe", "sh", "bat", "cmd", "php", "py", "pl", "cgi", "jsp", "asp",
    "aspx", "html", "htm", "js", "svg", "vbs", "jar", "war", "phtml"
}
MAX_FILE_SIZE_BYTES = 16 * 1024 * 1024  # 16 MB


def validate_file_safety(filename: str, file_size: Optional[int] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate that filename has a safe, permitted extension, no path traversal characters,
    and does not exceed maximum allowable content size.
    """
    if not filename or not isinstance(filename, str):
        return False, "Invalid filename."

    # Path traversal check
    clean_name = os.path.basename(filename)
    if ".." in filename or clean_name != filename or "/" in filename or "\\" in filename:
        return False, "Path traversal sequence detected."

    # Extension check
    parts = clean_name.rsplit(".", 1)
    if len(parts) < 2:
        return False, "File must have an explicit extension."

    ext = parts[1].lower()
    if ext in DANGEROUS_EXTENSIONS:
        return False, f"Dangerous file type '{ext}' is strictly prohibited."

    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}."

    # Size check
    if file_size is not None and file_size > MAX_FILE_SIZE_BYTES:
        return False, f"File size exceeds maximum permitted limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."

    return True, None


def generate_secure_storage_filename(original_filename: str) -> str:
    """
    Generate a non-predictable, cryptographically random UUID4 filename
    preserving only the validated file extension.
    Completely eliminates client-controlled naming, collisions, and path traversal.
    """
    clean_name = os.path.basename(original_filename)
    ext = clean_name.rsplit(".", 1)[1].lower() if "." in clean_name else "jpg"
    return f"{uuid.uuid4().hex}.{ext}"


def stream_authenticated_photo(photo_id: int):
    """
    Authenticated media streaming controller.
    Ensures that private progress photos are served ONLY to:
    1. The client athlete who owns the photo.
    2. The authorized coach supervising that client.
    Rejects all unauthenticated users and third-party tenants with HTTP 404/403.
    """
    from models import db, ProgressPhoto, Progress, Client
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Authentication required to view media.", "status_code": 401}), 401

    photo = db.session.query(ProgressPhoto).filter_by(id=photo_id).first()
    if not photo:
        return jsonify({"error": "Media not found or access denied.", "status_code": 404}), 404

    # Resolve photo owner
    progress = db.session.query(Progress).filter_by(id=photo.progress_id).first()
    if not progress:
        return jsonify({"error": "Media not found or access denied.", "status_code": 404}), 404

    client = db.session.query(Client).filter_by(id=progress.client_id).first()
    if not client:
        return jsonify({"error": "Media not found or access denied.", "status_code": 404}), 404

    # Ownership checks:
    # 1. Athlete access
    is_authorized = False
    if user.role == "CLIENT" and user.client and user.client.id == client.id:
        is_authorized = True
    # 2. Coach access
    elif user.role == "COACH" and user.coach and user.coach.id == client.coach_id:
        is_authorized = True
    # 3. Super admin oversight
    elif user.role == "SUPER_ADMIN":
        is_authorized = True

    if not is_authorized:
        return jsonify({"error": "Media not found or access denied.", "status_code": 404}), 404

    # Stream file from private upload folder
    upload_folder = current_app.config.get("UPLOAD_FOLDER") if current_app else None
    if not upload_folder or not os.path.exists(upload_folder):
        return jsonify({"error": "Storage directory unavailable.", "status_code": 500}), 500

    filename = os.path.basename(photo.photo_url)
    return send_from_directory(upload_folder, filename)
