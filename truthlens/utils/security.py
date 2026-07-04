import re
from pathlib import Path
import bleach
from truthlens.extensions import db
from truthlens.models.audit import AuditLog


def validate_password_strength(password: str) -> bool:
    """
    Requires:
    - Min 8 characters
    - At least 1 letter (uppercase or lowercase)
    - At least 1 digit
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Za-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """
    Checks if the filename has an extension that matches the allowed list.
    """
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in allowed_extensions


def sanitize_html(text: str) -> str:
    """
    Sanitizes HTML content to prevent XSS attacks using bleach.
    """
    if not text:
        return ""
    # Strip all HTML tags
    return bleach.clean(text, tags=[], attributes={}, strip=True)


def log_action(actor_id: int, action: str, target_type: str, target_id: str = None, metadata: dict = None):
    """
    Writes an audit entry directly to the database.
    """
    try:
        log = AuditLog(
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id is not None else None,
            event_metadata=metadata or {}
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # Fallback print if DB fails
        print(f"Failed to write audit log: {e}")
