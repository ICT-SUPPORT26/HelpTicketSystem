import os

class BaseConfig:
    SECRET_KEY = os.environ.get("SESSION_SECRET", "default_secret_key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 50,              # Very large pool for development
        "max_overflow": 100,          # Allow significant overflow
        "pool_recycle": 300,          # Recycle connections every 5 minutes
        "pool_pre_ping": True,        # Test connections before using
        "pool_timeout": 60,           # Wait up to 60 seconds for connection
        "echo_pool": False,           # Set to True for debugging
    }


class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or "postgresql+psycopg2://postgres:password@localhost:5432/helpticket_system_pg"
    )
    DEBUG = True

class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    DEBUG = False
