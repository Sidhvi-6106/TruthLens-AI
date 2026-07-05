from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from truthlens.models.user import User, SavedArticle, ReadingHistory
from truthlens.models.article import Article
from truthlens.extensions import db
from truthlens.services.auth_service import (
    register_user,
    authenticate_user,
    setup_mfa_totp,
    confirm_mfa_totp,
    disable_mfa_totp,
    update_user_profile,
    get_user_profile_data
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    try:
        result = register_user(payload)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Registration failed. Please check deployment database configuration.", "detail": str(e)}), 500


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    try:
        result = authenticate_user(payload)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Login failed. Please check deployment database configuration.", "detail": str(e)}), 500


@auth_bp.get("/profile")
@jwt_required()
def profile():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    try:
        data = get_user_profile_data(user.id)
        return jsonify(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.put("/profile")
@jwt_required()
def edit_profile():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    payload = request.get_json(silent=True) or {}
    try:
        result = update_user_profile(user.id, payload)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.post("/otp/setup")
@jwt_required()
def otp_setup():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    try:
        result = setup_mfa_totp(user.id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.delete("/otp/setup")
@jwt_required()
def otp_setup_disable():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    try:
        disable_mfa_totp(user.id)
        return jsonify({"success": True, "message": "MFA disabled."})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.post("/otp/verify")
@jwt_required()
def otp_verify():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    payload = request.get_json(silent=True) or {}
    code = str(payload.get("mfa_code", "")).strip()
    if not code:
        return jsonify({"error": "MFA code is required."}), 400
    try:
        confirm_mfa_totp(user.id, code)
        return jsonify({"success": True, "message": "MFA verified and enabled."})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.get("/saved")
@jwt_required()
def list_saved():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    saved = SavedArticle.query.filter_by(user_id=user.id).all()
    # Map saved articles with their DB info if exists
    ids = [s.article_id for s in saved]
    articles_db = Article.query.filter(Article.id.in_(ids)).all()
    articles_map = {str(a.id): a for a in articles_db}
    
    items = []
    for s in saved:
        if str(s.article_id) in articles_map:
            a = articles_map[str(s.article_id)]
            items.append({
                "id": a.id,
                "title": a.title,
                "summary": a.summary,
                "source": a.source,
                "category": a.category,
                "score": a.truthlens_score
            })
        else:
            # Fallback if news item is not in local DB (e.g. from static mock list)
            items.append({
                "id": s.article_id,
                "title": f"Bookmarked Story #{s.article_id}",
                "summary": "External referenced article stored in reader library.",
                "source": "Aggregated RSS",
                "category": "Technology",
                "score": 85
            })
    return jsonify({"items": items})


@auth_bp.delete("/saved")
@jwt_required()
def delete_saved():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    article_id = request.args.get("article_id")
    if not article_id:
        return jsonify({"error": "article_id parameter required"}), 400
    saved = SavedArticle.query.filter_by(user_id=user.id, article_id=article_id).first()
    if saved:
        db.session.delete(saved)
        db.session.commit()
    return jsonify({"success": True, "message": "Bookmark removed."})


@auth_bp.get("/history")
@jwt_required()
def list_history():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    history = ReadingHistory.query.filter_by(user_id=user.id).order_by(ReadingHistory.read_at.desc()).limit(15).all()
    return jsonify({"items": [{"article_id": h.article_id, "read_at": h.read_at.isoformat()} for h in history]})
