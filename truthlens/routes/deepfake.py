from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from truthlens.services.deepfake_service import detect_deepfake


deepfake_bp = Blueprint("deepfake", __name__)


@deepfake_bp.post("/analyze")
def analyze():
    if "media" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    media = request.files["media"]
    if not media.filename:
        return jsonify({"error": "Invalid file name"}), 400

    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(exist_ok=True)
    filename = f"{uuid4().hex}_{secure_filename(media.filename)}"
    path = upload_folder / filename
    media.save(path)

    return jsonify(detect_deepfake(str(path)))
