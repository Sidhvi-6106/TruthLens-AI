from truthlens.extensions import db
from truthlens.models.user import User
from truthlens.models.community import CommunityReport

def get_admin_metrics() -> dict:
    active_users = User.query.count()
    reports = CommunityReport.query.count()
    
    return {
        "active_users": active_users,
        "reports": reports,
        "ai_usage": 9300000, # Mocked for now
        "api_usage": {"news": 2400000, "verification": 980000, "deepfake": 184000}, # Mocked
        "fake_news_trends": ["Election misinformation", "Disaster alert rumors", "Stock market manipulation"],
        "deepfake_trends": ["Celebrity investment scams", "Synthetic speeches", "Lip-sync edits"],
        "system_health": "99.95%",
        "security": ["Rate limiting", "RBAC", "Audit logs", "Encryption", "Input sanitization", "XSS protection", "SQL injection protection"],
    }
