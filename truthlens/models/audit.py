from datetime import datetime

from truthlens.extensions import db


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    action = db.Column(db.String(120), nullable=False)
    target_type = db.Column(db.String(80), nullable=False)
    target_id = db.Column(db.String(80), nullable=True)
    event_metadata = db.Column("metadata", db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
