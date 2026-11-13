import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "labcontrol-dev-secret-key-change-in-production-2026")
    
    # Suporte a SQLite local e migração futura para PostgreSQL
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        db_path = INSTANCE_DIR / "labcontrol.db"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path.as_posix()}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Segurança de sessões
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 86400  # 24 horas


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
