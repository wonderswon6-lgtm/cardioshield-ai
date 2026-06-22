"""
config.py — Flask application configuration.
"""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", "deployment", ".env"))

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


class Config:
    SECRET_KEY  = os.environ.get("SECRET_KEY", "cardioshield-2024-secret")
    DEBUG       = False
    TESTING     = False

    # PostgreSQL
    DB_HOST     = os.environ.get("DB_HOST", "localhost")
    DB_PORT     = os.environ.get("DB_PORT", "5432")
    DB_NAME     = os.environ.get("DB_NAME", "cardioshield_db")
    DB_USER     = os.environ.get("DB_USER", "postgres")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "saanu0216")

    # Read from unified DATABASE_URL if available (standard for cloud platforms)
    db_url = os.environ.get("DATABASE_URL")
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = db_url or f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MODELS_DIR   = os.path.join(BASE_DIR, "saved_models")
    REPORTS_DIR  = os.path.join(BASE_DIR, "reports")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


_map = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
}

def get_config(env=None):
    return _map.get(env or os.environ.get("FLASK_ENV", "development"), DevelopmentConfig)
