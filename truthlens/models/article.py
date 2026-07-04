from datetime import datetime

from truthlens.extensions import db


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(120), nullable=False)
    author = db.Column(db.String(120), nullable=True)
    category = db.Column(db.String(80), nullable=False, index=True)
    language = db.Column(db.String(32), nullable=False, default="English")
    url = db.Column(db.String(500), nullable=True)
    truthlens_score = db.Column(db.Integer, nullable=False, default=75)
    bias_label = db.Column(db.String(40), nullable=False, default="Center")
    ai_risk = db.Column(db.Integer, nullable=False, default=15)
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
