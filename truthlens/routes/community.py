from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from truthlens.models.user import User
from truthlens.services.gamification_service import submit_report, get_leaderboard

community_bp = Blueprint("community", __name__)

@community_bp.post("/report")
@jwt_required()
def report_misinformation():
    email = get_jwt_identity()
    current_user = User.query.filter_by(email=email).first()
    if not current_user:
        return jsonify({"error": "User not found"}), 404

    data = request.json
    claim_text = data.get("claim_text")
    article_id = data.get("article_id")
    evidence_url = data.get("evidence_url")
    report_type = data.get("report_type", "misinformation")

    if not claim_text:
        return jsonify({"error": "Claim text is required"}), 400

    report = submit_report(
        user_id=current_user.id,
        claim_text=claim_text,
        article_id=article_id,
        evidence_url=evidence_url,
        report_type=report_type
    )
    return jsonify({"message": "Report submitted successfully", "report_id": report.id}), 201

@community_bp.get("/leaderboard")
def leaderboard():
    return jsonify({"items": get_leaderboard()})
