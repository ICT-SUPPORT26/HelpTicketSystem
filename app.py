# app.py
import os
from dotenv import load_dotenv
load_dotenv()
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from extensions import db, login_manager, mail, jwt
from datetime import datetime, timedelta
from flask import session, redirect, url_for, flash
from flask_login import logout_user, current_user
import pytz

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
db_url = os.environ.get("DATABASE_URL")

if not db_url:
    # Fallback to local/defaults
    db_engine = os.environ.get("DB_ENGINE", os.environ.get("DB_TYPE", "mysql")).lower()
    db_user = os.environ.get("DB_USER", "root")
    db_password = os.environ.get("DB_PASSWORD", "")
    db_host = os.environ.get("DB_HOST", "127.0.0.1")
    db_port = os.environ.get("DB_PORT")
    db_name = os.environ.get("DB_NAME")

    if not db_name:
        db_name = "helpticket_system_pg" if db_engine in ("postgres", "postgresql") else "helpticket_system"

    if db_engine in ("postgres", "postgresql"):
        driver = "postgresql+psycopg2"
        db_port = db_port or "5432"

        # Render Postgres integration
        db_user = os.environ.get("RENDER_DB_USER", db_user)
        db_password = os.environ.get("RENDER_DB_PASSWORD", db_password)
        db_host = os.environ.get("RENDER_DB_HOST", db_host)
        db_name = os.environ.get("RENDER_DB_NAME", db_name)

        db_url = f"{driver}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require"
    else:
        driver = "mysql+pymysql"
        db_port = db_port or "3306"
        db_url = f"{driver}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Mask password when logging
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

# JWT Configuration
_jwt_secret = os.environ.get('SESSION_SECRET')
if not _jwt_secret:
    import warnings
    warnings.warn(
        "SESSION_SECRET environment variable is not set. "
        "Using an insecure development default — set SESSION_SECRET before deploying to production.",
        stacklevel=2,
    )
    _jwt_secret = 'dev-jwt-helpdesk-secret-CHANGE-BEFORE-DEPLOY'
app.config['JWT_SECRET_KEY'] = _jwt_secret
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=30)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=7)

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
jwt.init_app(app)
csrf = CSRFProtect(app)

# CORS for React frontend — restrict to localhost Vite dev server
_cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:5000').split(',')
CORS(app, resources={r'/api/v1/*': {'origins': _cors_origins, 'supports_credentials': True}})

# IMPORTANT: import models BEFORE create_all
import models

# Initialize access logging middleware
# Using queue-based approach for efficient, non-blocking logging
from access_logger_simple import AccessLoggerMiddleware
AccessLoggerMiddleware(app)

with app.app_context():
    db.create_all()


# --- Ensure default accounts exist ---
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Check if admin exists
    admin = User.query.filter_by(username="215030").first()
    if not admin:
        admin = User(
            username="215030",
            full_name="System Administrator",
            email="admin@helpticketsystem.com",
            password_hash=generate_password_hash("admin123"),  # default password
            role="admin",
            is_active=True,
            is_verified=True,
            is_approved=True
        )
        db.session.add(admin)
        db.session.commit()
        # logging.info("Default admin account created: username='215030', password='admin123'")
    #else:
     #   logging.info("Default admin already exists")

    # Check if intern exists
    intern = User.query.filter_by(username="dctraining").first()
    if not intern:
        intern = User(
            username="dctraining",
            full_name="Dctraining",
            email="intern@helpticketsystem.com",
            password_hash=generate_password_hash("Dctraining2023"),  # default password
            role="intern",
            is_active=True,
            is_verified=True,
            is_approved=True
        )
        db.session.add(intern)
        db.session.commit()
        logging.info("Default intern account created: username='dctraining', password='Dctraining2023'")
   # else:
        # logging.info("Default intern already exists")



login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Timezone conversion filter for templates
nairobi_tz = pytz.timezone('Africa/Nairobi')
utc_tz = pytz.UTC

@app.template_filter('to_nairobi')
def to_nairobi_time(dt):
    """Convert UTC datetime to Nairobi timezone (EAT, UTC+3)"""
    if dt is None:
        return None
    
    # If datetime is naive, assume it's UTC
    if dt.tzinfo is None:
        dt = utc_tz.localize(dt)
    else:
        # Convert to UTC first if it has timezone info
        dt = dt.astimezone(utc_tz)
    
    # Convert to Nairobi timezone
    nairobi_time = dt.astimezone(nairobi_tz)
    return nairobi_time

@app.template_filter('format_nairobi')
def format_nairobi_time(dt, fmt='%Y-%m-%d %H:%M:%S'):
    """Format datetime in Nairobi timezone"""
    if dt is None:
        return ''
    
    nairobi_time = app.jinja_env.filters['to_nairobi'](dt)
    return nairobi_time.strftime(fmt) if nairobi_time else ''

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# NOTE: we set a 3 minute inactivity timeout per user's request.
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=3)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# Inject commonly-used values into templates
@app.context_processor
def inject_now():
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
    if current_user.is_authenticated:
        now = datetime.utcnow()
        last = session.get('last_activity')
        if last:
            try:
                last_dt = datetime.fromisoformat(last)
            except Exception:
                last_dt = now

            if now - last_dt > app.permanent_session_lifetime:
                logout_user()
                session.pop('last_activity', None)
                flash("Session expired due to inactivity. Please log in again.", "warning")
                return redirect(url_for('login'))

        session['last_activity'] = now.isoformat()

@app.after_request
def add_no_cache_headers(response):
    """
    Prevent caching for authenticated pages so that after logout, 
    browser does not show old pages on refresh.
    """
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# Serve the React SPA build — intercept all non-API, non-static requests
import os as _os
from flask import send_from_directory as _send_from_directory

_REACT_DIST = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'frontend', 'dist')

@app.before_request
def _serve_react():
    from flask import request
    path = request.path
    # Let API, static files, and uploads pass through to Flask handlers
    if (path.startswith('/api/') or
            path.startswith('/static/') or
            path.startswith('/uploads/')):
        return None
    # If the React build exists, serve it
    if _os.path.isdir(_REACT_DIST):
        # Serve actual files (assets, favicon, etc.)
        candidate = _os.path.join(_REACT_DIST, path.lstrip('/'))
        if _os.path.isfile(candidate):
            return _send_from_directory(_REACT_DIST, path.lstrip('/'))
        # Fallback: serve index.html for all SPA routes
        return _send_from_directory(_REACT_DIST, 'index.html')
    return None

# Import routes so they attach to app (legacy Jinja2 — used only when React build is absent)
import routes

# Register API blueprint (JWT-protected, CSRF-exempt)
from api_routes import api_bp
csrf.exempt(api_bp)
app.register_blueprint(api_bp)

# Register CLI commands for testing
from cli_commands import cli as sms_cli
app.cli.add_command(sms_cli, name='sms')
