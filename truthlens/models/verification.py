from datetime import datetime

from truthlens.extensions import db


class VerificationReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey("article.id"), nullable=True)
    submitted_text = db.Column(db.Text, nullable=False)
    reliability_score = db.Column(db.Integer, nullable=False)
    label = db.Column(db.String(80), nullable=False)
    confidence = db.Column(db.Integer, nullable=False)
    extracted_claims = db.Column(db.JSON, nullable=False, default=list)
    evidence_sources = db.Column(db.JSON, nullable=False, default=list)
    contradictions = db.Column(db.JSON, nullable=False, default=list)
    supporting_sources = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
