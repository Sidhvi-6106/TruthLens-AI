from truthlens.extensions import db
from truthlens.models.community import CommunityReport, Badge, UserBadge
from truthlens.models.user import User

def submit_report(user_id, claim_text, article_id=None, evidence_url=None, report_type="misinformation"):
    report = CommunityReport(
        user_id=user_id,
        claim_text=claim_text,
        article_id=article_id,
        evidence_url=evidence_url,
        report_type=report_type,
        status="pending"
    )
    db.session.add(report)
    
    # Award points for submitting report
    if user_id:
        user = User.query.get(user_id)
        if user:
            if user.trust_points is None:
                user.trust_points = 0
            user.trust_points += 10
            
    db.session.commit()
    return report

def get_leaderboard():
    users = User.query.order_by(User.trust_points.desc().nulls_last()).limit(10).all()
    return [{"name": u.name, "points": u.trust_points or 0} for u in users]
