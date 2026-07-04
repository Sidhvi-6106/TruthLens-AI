from datetime import datetime

from truthlens.extensions import db


class CommunityReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    article_id = db.Column(db.String(120), nullable=True)
    claim_text = db.Column(db.Text, nullable=False)
    evidence_url = db.Column(db.String(500), nullable=True)
    report_type = db.Column(db.String(40), default="misinformation")  # misinformation, correction, evidence
    status = db.Column(db.String(40), nullable=False, default="pending")  # pending, reviewed, resolved, rejected
    moderator_notes = db.Column(db.Text, nullable=True)
    upvotes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(10), default="🏆")
    points_required = db.Column(db.Integer, default=0)


class UserBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey("badge.id"), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
