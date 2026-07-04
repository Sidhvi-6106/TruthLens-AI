import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from truthlens import create_app
from truthlens.extensions import db
from truthlens.models import Role


DEFAULT_ROLES = [
    ("User", "Reads news, saves articles, verifies claims and submits reports."),
    ("Moderator", "Reviews community reports, corrections and submitted evidence."),
    ("Admin", "Manages users, system health, API usage, audit logs and platform policy."),
]


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        for name, description in DEFAULT_ROLES:
            if not Role.query.filter_by(name=name).first():
                db.session.add(Role(name=name, description=description))
        db.session.commit()
        print("TruthLens AI database initialized.")


if __name__ == "__main__":
    main()
