import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    PROJECT_TITLE = "TruthLens AI - Next Generation News Intelligence, Fact Verification & Deepfake Detection Platform"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'truthlens_dev.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = Path(os.getenv("UPLOAD_FOLDER", BASE_DIR / "uploads"))
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB

    # Cache
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # News providers
    NEWS_PROVIDERS = ["NewsAPI", "GNews", "Mediastack", "Guardian API", "Reuters RSS", "BBC RSS", "NYTimes API"]
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
    GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
    MEDIASTACK_API_KEY = os.getenv("MEDIASTACK_API_KEY", "")
    GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY", "")
    NYTIMES_API_KEY = os.getenv("NYTIMES_API_KEY", "")

    # AI services
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GROK_API_KEY = os.getenv("GROK_API_KEY", "")

    # OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")

    # Feature flags
    AI_ENABLED = bool(os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY"))
    NEWS_LIVE = bool(os.getenv("NEWS_API_KEY") or os.getenv("GUARDIAN_API_KEY"))

    # Supported languages
    LANGUAGES = ["English", "Hindi", "Telugu", "Tamil", "Kannada", "Malayalam", "Marathi", "Bengali"]

    # Categories
    CATEGORIES = ["Technology", "Politics", "Sports", "Finance", "Business", "Entertainment", "Health", "Science", "International"]
