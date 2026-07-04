import os

from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


def _get_limiter_storage_uri():
    configured = os.getenv("RATELIMIT_STORAGE_URL") or os.getenv("REDIS_URL")
    if not configured:
        return "memory://"
    if configured.startswith(("redis://", "rediss://")):
        try:
            import redis  # noqa: F401
        except ImportError:
            return "memory://"
    return configured


db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "60 per hour"],
    storage_uri=_get_limiter_storage_uri(),
)
