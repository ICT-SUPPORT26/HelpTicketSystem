# app.py
import os
from dotenv import load_dotenv
load_dotenv()
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_wtf.csrf import CSRFProtect
from extensions import db, login_manager, mail
from datetime import datetime, timedelta
from flask import session, redirect, url_for, flash
from flask_login import logout_user, current_user


# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
# The app can use a full DATABASE_URL or individual DB_* variables to build one.
# Supported DB_ENGINE/DB_TYPE values: "mysql" (default) or "postgres"/"postgresql".
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    db_engine = os.environ.get("DB_ENGINE", os.environ.get("DB_TYPE", "mysql")).lower()
    db_user = os.environ.get("DB_USER", "root")
    db_password = os.environ.get("DB_PASSWORD", "")
    db_host = os.environ.get("DB_HOST", "127.0.0.1")
    db_port = os.environ.get("DB_PORT")
    db_name = os.environ.get("DB_NAME")

    # If DB_NAME is not explicitly set, choose a sensible default based on engine
    if not db_name:
        db_name = "helpticket_system_pg" if db_engine in ("postgres", "postgresql") else "helpticket_system"

    if db_engine in ("postgres", "postgresql"):
        driver = "postgresql+psycopg2"
        db_port = db_port or "5432"
    else:
        driver = "mysql+pymysql"
        db_port = db_port or "3306"

    # Build URL (empty password is allowed; will result in 'user:@host')
    db_url = f"{driver}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Mask password when logging the selected DB URL
def _mask_password_from_url(url: str) -> str:
    try:
        if "@" in url:
            left, right = url.split("@", 1)
            if ":" in left:
                user, _ = left.split(":", 1)
                return f"{user}:***@{right}"
    except Exception:
        pass
    return url

logging.info("Using database: %s", _mask_password_from_url(db_url))
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Uploads
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Mail
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'helpticketsystem@outlook.com')

# Extensions
db.init_app(app)
login_manager.init_app(app)
mail.init_app(app)
csrf = CSRFProtect(app)

# IMPORTANT: import models BEFORE create_all
import models  

with app.app_context():
    db.create_all()


login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# NOTE: we set a 3 minute inactivity timeout per user's request.
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=3)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# Inject commonly-used values into templates
@app.context_processor
def inject_now():
    # Toast and session-expiry configuration (configurable via env vars)
    app.config.setdefault('TOAST_AUTOCLOSE_MS', int(os.environ.get('TOAST_AUTOCLOSE_MS', 5000)))
    app.config.setdefault('SESSION_EXPIRY_TOAST_CLASS', os.environ.get('SESSION_EXPIRY_TOAST_CLASS', 'text-bg-warning'))
    app.config.setdefault('SESSION_EXPIRY_REDIRECT_MS', int(os.environ.get('SESSION_EXPIRY_REDIRECT_MS', 1500)))

    return {
        'now': datetime.utcnow,
        'TOAST_AUTOCLOSE_MS': app.config['TOAST_AUTOCLOSE_MS'],
        'SESSION_EXPIRY_TOAST_CLASS': app.config['SESSION_EXPIRY_TOAST_CLASS'],
        'SESSION_EXPIRY_REDIRECT_MS': app.config['SESSION_EXPIRY_REDIRECT_MS'],
    }


@app.before_request
def enforce_session_timeout():
    # configured `PERMANENT_SESSION_LIFETIME` to determine expiry.
    if current_user.is_authenticated:
        now = datetime.utcnow()
        last = session.get('last_activity')
        if last:
            try:
                last_dt = datetime.fromisoformat(last)
            except Exception:
                last_dt = now

            if now - last_dt > app.permanent_session_lifetime:
                # expire session
                logout_user()
                session.pop('last_activity', None)
                flash("Session expired due to inactivity. Please log in again.", "warning")
                return redirect(url_for('login'))

        # Update last_activity timestamp for every authenticated request
        session['last_activity'] = now.isoformat()

# Import routes so they attach to app
import routes

# Register CLI commands for testing
from cli_commands import cli as sms_cli
app.cli.add_command(sms_cli, name='sms')
