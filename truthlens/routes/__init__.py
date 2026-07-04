from truthlens.routes.admin import admin_bp
from truthlens.routes.auth import auth_bp
from truthlens.routes.assistant import assistant_bp
from truthlens.routes.community import community_bp
from truthlens.routes.deepfake import deepfake_bp
from truthlens.routes.news import news_bp
from truthlens.routes.pages import pages_bp
from truthlens.routes.verification import verification_bp


def register_blueprints(app):
    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(news_bp, url_prefix="/api/news")
    app.register_blueprint(verification_bp, url_prefix="/api/verification")
    app.register_blueprint(deepfake_bp, url_prefix="/api/deepfake")
    app.register_blueprint(assistant_bp, url_prefix="/api/assistant")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(community_bp, url_prefix="/api/community")
