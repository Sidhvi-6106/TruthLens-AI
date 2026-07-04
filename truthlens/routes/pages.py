from flask import Blueprint, current_app, jsonify, render_template


pages_bp = Blueprint("pages", __name__)


@pages_bp.get("/")
def dashboard():
    return render_template("dashboard.html", project_title=current_app.config["PROJECT_TITLE"])


@pages_bp.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "project": current_app.config["PROJECT_TITLE"],
            "services": ["news", "verification", "deepfake", "assistant", "admin"],
        }
    )
