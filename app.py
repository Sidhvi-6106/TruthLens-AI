import os

from truthlens import create_app
from truthlens.extensions import db

app = create_app()

with app.app_context():
    try:
        db.create_all()
    except Exception as exc:
        app.logger.warning("Database initialization skipped: %s", exc)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
