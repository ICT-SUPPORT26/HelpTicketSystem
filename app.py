# app.py
import os
from flask import Flask, session, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import logout_user, current_user
from datetime import datetime, timedelta
from extensions import db, login_manager, mail

# ------------------------------
# Flask app setup
# ------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# ------------------------------
# Database configuration
# ------------------------------
# Dual-mode: Use DATABASE_URL from Render or fallback to local MySQL
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://root:@localhost:3306/helpticket_system"
)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

# ------------------------------
# Flask extensions
# ------------------------------
login_manager.init_app(app)
mail.init_app(app)
csrf = CSRFProtect(app)

login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# ------------------------------
# Uploads
# ------------------------------
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ------------------------------
# Mail configuration
# ------------------------------
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'helpticketsystem@outlook.com')

# ------------------------------
# Session timeout / inactivity logout
# ------------------------------
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=3)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

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

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}

# ------------------------------
# Routes and CLI
# ------------------------------
import routes
from cli_commands import cli as sms_cli
app.cli.add_command(sms_cli, name='sms')

# ------------------------------
# Production-safe DB creation
# ------------------------------
with app.app_context():
    try:
        db.engine.connect()  # Test DB connection first
        db.create_all()
        print("✅ Database connected and tables created successfully!")
    except Exception as e:
        print("❌ Database connection failed. Tables not created:", e)
