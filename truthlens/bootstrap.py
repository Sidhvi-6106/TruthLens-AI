from truthlens.extensions import db
from truthlens.models import Role


DEFAULT_ROLES = [
    ("User", "Reads news, saves articles, verifies claims and submits reports."),
    ("Moderator", "Reviews community reports, corrections and submitted evidence."),
    ("Admin", "Manages users, system health, API usage, audit logs and platform policy."),
]


def ensure_database_ready(app) -> None:
    with app.app_context():
        db.create_all()
        for name, description in DEFAULT_ROLES:
            if not Role.query.filter_by(name=name).first():
                db.session.add(Role(name=name, description=description))
        db.session.commit()
