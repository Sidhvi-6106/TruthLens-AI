from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from truthlens.models.user import User
from truthlens.services.verification_service import detect_ai_content, detect_fake_news, verify_social_claim

verification_bp = Blueprint("verification", __name__)


@verification_bp.post("/article")
@jwt_required(optional=True)
def verify_article():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    email = get_jwt_identity()
    user_id = None
    if email:
        user = User.query.filter_by(email=email).first()
        if user:
            user_id = user.id

    return jsonify(detect_fake_news(text, user_id))


@verification_bp.post("/document")
@jwt_required(optional=True)
def verify_document():
    if "document" not in request.files:
        return jsonify({"error": "No document uploaded"}), 400
    doc = request.files["document"]
    if not doc.filename:
        return jsonify({"error": "Invalid document name"}), 400

    try:
        # Read text file content
        text = doc.read().decode("utf-8", errors="ignore").strip()
    except Exception as e:
        return jsonify({"error": f"Failed to read file: {e}"}), 400

    if not text:
        return jsonify({"error": "Document is empty"}), 400

    email = get_jwt_identity()
    user_id = None
    if email:
        user = User.query.filter_by(email=email).first()
        if user:
            user_id = user.id

    return jsonify(detect_fake_news(text, user_id))


@verification_bp.post("/ai-content")
def ai_content():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400
    return jsonify(detect_ai_content(text))


@verification_bp.post("/social-claim")
def social_claim():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    if not text:
        return jsonify({"error": "No claim provided"}), 400
    return jsonify(verify_social_claim(text))
