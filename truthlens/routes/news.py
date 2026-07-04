from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from truthlens.models.user import User, SavedArticle, ReadingHistory
from truthlens.extensions import db
from truthlens.services.news_service import (
    get_categories,
    get_recommended_articles,
    get_top_stories,
    search_articles,
    sync_news_articles
)

news_bp = Blueprint("news", __name__)


@news_bp.get("/top-stories")
def top_stories():
    refresh = request.args.get("refresh")
    if refresh:
        sync_news_articles()
    return jsonify({"items": get_top_stories()})


@news_bp.get("/categories")
def categories():
    return jsonify({"items": get_categories()})


@news_bp.get("/recommended")
def recommended():
    return jsonify({"items": get_recommended_articles()})


@news_bp.get("/search")
def search():
    query = request.args.get("q", "")
    return jsonify({"items": search_articles(query)})


@news_bp.post("/save")
@jwt_required()
def save_article():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    payload = request.get_json(silent=True) or {}
    article_id = str(payload.get("article_id", "")).strip()
    if not article_id:
        return jsonify({"error": "article_id parameter required"}), 400

    existing = SavedArticle.query.filter_by(user_id=user.id, article_id=article_id).first()
    if existing:
        return jsonify({"success": True, "message": "Article already bookmarked in your library."})

    bookmark = SavedArticle(user_id=user.id, article_id=article_id)
    db.session.add(bookmark)
    
    # Also write to reading log
    hist = ReadingHistory(user_id=user.id, article_id=article_id)
    db.session.add(hist)
    
    db.session.commit()
    return jsonify({"success": True, "message": "Article successfully bookmarked."})


@news_bp.post("/log-read")
@jwt_required()
def log_read():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    payload = request.get_json(silent=True) or {}
    article_id = str(payload.get("article_id", "")).strip()
    if not article_id:
        return jsonify({"error": "article_id parameter required"}), 400

    hist = ReadingHistory(user_id=user.id, article_id=article_id)
    db.session.add(hist)
    db.session.commit()
    return jsonify({"success": True})
