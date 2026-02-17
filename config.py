import os

class BaseConfig:
    SECRET_KEY = os.environ.get("SESSION_SECRET", "default_secret_key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }


class DevelopmentConfig(BaseConfig):
    # Allow overriding via DATABASE_URL env var; otherwise build from parts
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASS = os.environ.get("DB_PASS", "Jace102020.")
    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    DB_PORT = os.environ.get("DB_PORT", "3307")
    DB_NAME = os.environ.get("DB_NAME", "helpticket_system")
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    DEBUG = True

    # If one is using XAMPP, Then onw would uncomment as follows:
    #class DevelopmentConfig(BaseConfig):
    # Allow overriding via DATABASE_URL env var; otherwise build from parts
    #DB_USER = os.environ.get("DB_USER", "root")
    #DB_PASS = os.environ.get("DB_PASS", "")  # empty string since no password
    #DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    #DB_PORT = os.environ.get("DB_PORT", "3306")  # default XAMPP MySQL port
    #DB_NAME = os.environ.get("DB_NAME", "helpticket_system")
    #SQLALCHEMY_DATABASE_URI = (
     #   os.environ.get("DATABASE_URL")
     #  or f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    #)
    #DEBUG = True

class ProductionConfig(BaseConfig):
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASS = os.environ.get("DB_PASS", "Jace102020.")
    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    DB_PORT = os.environ.get("DB_PORT", "3307")
    DB_NAME = os.environ.get("DB_NAME", "helpticket_system")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or (
        f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    DEBUG = False

     # If one is using XAMPP, Then onw would uncomment as follows:
    #class DevelopmentConfig(BaseConfig):
    # Allow overriding via DATABASE_URL env var; otherwise build from parts
    #DB_USER = os.environ.get("DB_USER", "root")
    #DB_PASS = os.environ.get("DB_PASS", "")  # empty string since no password
    #DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    #DB_PORT = os.environ.get("DB_PORT", "3306")  # default XAMPP MySQL port
    #DB_NAME = os.environ.get("DB_NAME", "helpticket_system")
    #SQLALCHEMY_DATABASE_URI = (
     #   os.environ.get("DATABASE_URL")
     #  or f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    #)
    #DEBUG = True
