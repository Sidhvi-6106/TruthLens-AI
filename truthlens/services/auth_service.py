from datetime import datetime, timedelta
import pyotp
from flask_jwt_extended import create_access_token
from truthlens.extensions import db
from truthlens.models.user import User, Role, SavedArticle, ReadingHistory
from truthlens.models.community import Badge, UserBadge
from truthlens.utils.security import validate_password_strength, log_action, sanitize_html

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 10


def register_user(payload: dict) -> dict:
    """
    Registers a new user in the database, verifying password strength and role logic.
    """
    name = sanitize_html(str(payload.get("name", "")).strip())
    email = sanitize_html(str(payload.get("email", "")).strip().lower())
    password = str(payload.get("password", ""))
    role_name = payload.get("role", "User")

    if not name or not email or not password:
        raise ValueError("Name, email, and password are required.")

    if not validate_password_strength(password):
        raise ValueError("Password must be at least 8 characters long and contain both letters and numbers.")

    if User.query.filter_by(email=email).first():
        raise ValueError("An account with this email address already exists.")

    role = _get_or_create_role(role_name)

    user = User(
        name=name,
        email=email,
        role_id=role.id,
        trust_points=0
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    log_action(user.id, "register", "user", user.id, {"email": email, "role": role.name})

    return {
        "success": True,
        "message": f"User {email} successfully registered under role {role.name}."
    }


def authenticate_user(payload: dict) -> dict:
    """
    Authenticates email credentials, manages locked lockouts and MFA requirements.
    """
    email = sanitize_html(str(payload.get("email", "")).strip().lower())
    password = str(payload.get("password", ""))
    otp_code = str(payload.get("otp", "")).strip()
    mfa_code = str(payload.get("mfa_code", "")).strip()

    user = User.query.filter_by(email=email).first()
    if not user:
        raise ValueError("Invalid email or password.")

    # Account Lockout Check
    if user.is_locked():
        remaining = user.locked_until - datetime.utcnow()
        minutes = max(1, int(remaining.total_seconds() / 60))
        raise ValueError(f"Account locked. Try again in {minutes} minutes.")

    # Check Password
    if not user.check_password(password):
        user.login_attempts += 1
        if user.login_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
            user.login_attempts = 0
            db.session.commit()
            log_action(user.id, "account_lockout", "user", user.id, {"email": email})
            raise ValueError(f"Too many failed login attempts. Account locked for {LOCKOUT_MINUTES} minutes.")
        db.session.commit()
        raise ValueError("Invalid email or password.")

    # Check Email OTP (Demonstration email trigger)
    # If login doesn't supply OTP and user is not verified, require it
    if not user.email_verified:
        if not otp_code:
            # Generate OTP secret if missing
            if not user.otp_secret:
                user.otp_secret = pyotp.random_base32()[:6] # simple string OTP
                db.session.commit()
            # In production this emails the OTP secret. For dev demo, we verify a code.
            # We return token required flag
            return {"otp_required": True, "message": "Email OTP verification required."}
        else:
            # Mock check: allow 123456 or matching stored value
            if otp_code != "123456" and otp_code != user.otp_secret:
                raise ValueError("Invalid verification OTP code.")
            user.email_verified = True
            user.otp_secret = None
            db.session.commit()

    # Check MFA TOTP
    if user.mfa_enabled:
        if not mfa_code:
            return {"mfa_required": True, "message": "Multi-factor authentication required."}
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(mfa_code):
            raise ValueError("Invalid Multi-factor authenticator code.")

    # Reset attempts on successful authentication
    user.login_attempts = 0
    user.last_login = datetime.utcnow()
    # Award daily login points
    user.trust_points += 5
    db.session.commit()

    log_action(user.id, "login", "user", user.id, {"mfa_active": user.mfa_enabled})

    # Auto award "First Step" badge if user has no badges
    award_default_badges(user)

    token = create_access_token(identity=user.email)
    return {
        "access_token": token,
        "user": user.to_dict()
    }


def _get_or_create_role(role_name: str) -> Role:
    allowed = {"User", "Moderator", "Admin"}
    normalized = role_name if role_name in allowed else "User"
    role = Role.query.filter_by(name=normalized).first()
    if role:
        return role

    role = Role.query.filter_by(name="User").first()
    if role:
        return role

    role = Role(name="User", description="Reads news, saves articles, verifies claims and submits reports.")
    db.session.add(role)
    db.session.commit()
    return role


def setup_mfa_totp(user_id: int) -> dict:
    """
    Generates TOTP secret configuration for user.
    """
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found.")
    
    secret = pyotp.random_base32()
    user.mfa_secret = secret
    db.session.commit()

    return {"secret": secret}


def confirm_mfa_totp(user_id: int, code: str):
    """
    Verifies code and enables MFA protection.
    """
    user = User.query.get(user_id)
    if not user or not user.mfa_secret:
        raise ValueError("MFA configuration details missing.")
    
    totp = pyotp.TOTP(user.mfa_secret)
    if not totp.verify(code):
        raise ValueError("Invalid confirmation code.")
    
    user.mfa_enabled = True
    db.session.commit()
    log_action(user.id, "enable_mfa", "user", user.id)


def disable_mfa_totp(user_id: int):
    """
    Disables MFA protection.
    """
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found.")
    
    user.mfa_enabled = False
    user.mfa_secret = None
    db.session.commit()
    log_action(user.id, "disable_mfa", "user", user.id)


def update_user_profile(user_id: int, payload: dict) -> dict:
    """
    Updates basic user parameters.
    """
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found.")

    bio = payload.get("bio")
    avatar_url = payload.get("avatar_url")
    lang = payload.get("preferred_language")

    if bio is not None:
        user.bio = sanitize_html(str(bio).strip())
    if avatar_url is not None:
        user.avatar_url = sanitize_html(str(avatar_url).strip())
    if lang is not None:
        user.preferred_language = sanitize_html(str(lang).strip())

    db.session.commit()
    log_action(user.id, "update_profile", "user", user.id)
    return {"user": user.to_dict()}


def get_user_profile_data(user_id: int) -> dict:
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found.")
    
    saved = SavedArticle.query.filter_by(user_id=user.id).all()
    history = ReadingHistory.query.filter_by(user_id=user.id).order_by(ReadingHistory.read_at.desc()).limit(10).all()
    badges = UserBadge.query.filter_by(user_id=user.id).all()

    # Map articles info from cache/top lists if needed
    return {
        "user": user.to_dict(),
        "saved_articles": [{"id": s.article_id, "created_at": s.created_at.isoformat()} for s in saved],
        "reading_history": [{"id": h.id, "article_id": h.article_id, "read_at": h.read_at.isoformat()} for h in history],
        "badges": [{"name": ub.badge.name, "description": ub.badge.description, "icon": ub.badge.icon} for ub in badges]
    }


def award_default_badges(user: User):
    """
    Seeds and awards default badges on logins.
    """
    # Ensure badges exist in DB
    badges_defs = [
      ("First Step", "Logged in to the TruthLens platform.", "🌱"),
      ("Verifier Pro", "Performed claims verification scans.", "🛡️"),
      ("Deepfake Specialist", "Analyzed media files for manipulation.", "🔍")
    ]
    for name, desc, icon in badges_defs:
        if not Badge.query.filter_by(name=name).first():
            db.session.add(Badge(name=name, description=desc, icon=icon))
    db.session.commit()

    # Award first login badge
    badge = Badge.query.filter_by(name="First Step").first()
    if badge and not UserBadge.query.filter_by(user_id=user.id, badge_id=badge.id).first():
        db.session.add(UserBadge(user_id=user.id, badge_id=badge.id))
        user.trust_points += 10
        db.session.commit()
