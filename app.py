# app.py
import os
from dotenv import load_dotenv
load_dotenv()

import logging
from flask import Flask, session, redirect, url_for, flash
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_wtf.csrf import CSRFProtect
from flask_login import logout_user, current_user
from extensions import db, login_manager, mail
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# -----------------------
# DATABASE CONFIGURATION
# -----------------------
# Use DATABASE_URL if set (Render / Production)
# Otherwise fallback to local MySQL (XAMPP)
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://root:@localhost:3306/helpticket_system"
)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# -----------------------
# Uploads
# -----------------------
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# -----------------------
# MAIL CONFIGURATION
# -----------------------
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'helpticketsystem@outlook.com')

# -----------------------
# EXTENSIONS
# -----------------------
db.init_app(app)
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

# -----------------------
# SESSION / AUTO LOGOUT
# -----------------------
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=3)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}

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

# -----------------------
# ROUTES
# -----------------------
import routes

# -----------------------
# CLI Commands (Optional)
# -----------------------
from cli_commands import cli as sms_cli
app.cli.add_command(sms_cli, name='sms')

# -----------------------
# CREATE TABLES (ONCE)
# -----------------------
with app.app_context():
    try:
        db.create_all()
        logging.info("✅ Database tables created successfully.")
    except Exception as e:
        logging.error(f"❌ Database connection failed. Tables not created: {e}")
