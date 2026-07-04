from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from truthlens.extensions import db


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)
    description = db.Column(db.String(180), nullable=False, default="")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)
    oauth_provider = db.Column(db.String(32), nullable=True)
    oauth_id = db.Column(db.String(255), nullable=True)
    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_secret = db.Column(db.String(64), nullable=True)
    otp_secret = db.Column(db.String(64), nullable=True)
    trust_points = db.Column(db.Integer, default=0)
    avatar_url = db.Column(db.String(500), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    preferred_language = db.Column(db.String(32), default="English")
    login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    email_verified = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    role = db.relationship("Role", backref="users")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return bool(self.password_hash and check_password_hash(self.password_hash, password))

    def is_locked(self):
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role.name if self.role else "User",
            "mfa_enabled": self.mfa_enabled,
            "trust_points": self.trust_points,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "preferred_language": self.preferred_language,
            "email_verified": self.email_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SavedArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    article_id = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ReadingHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    article_id = db.Column(db.String(120), nullable=False)
    read_at = db.Column(db.DateTime, default=datetime.utcnow)
