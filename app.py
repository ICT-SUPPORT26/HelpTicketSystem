# app.py
import os
import logging
from datetime import datetime, timedelta

from flask import Flask, session, redirect, url_for, flash
from flask_login import logout_user, current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

from flask_migrate import Migrate
from extensions import db, login_manager, mail
from config import DevelopmentConfig, ProductionConfig

# Load environment variables
load_dotenv()

# App setup
app = Flask(__name__)

env = os.environ.get("FLASK_ENV", "development").lower()
if env == "production":
    app.config.from_object(ProductionConfig)
else:
    app.config.from_object(DevelopmentConfig)

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Logging
logging.basicConfig(level=logging.INFO)
logging.info("Running in %s mode", env)
logging.info("Database: %s", app.config["SQLALCHEMY_DATABASE_URI"].split("@")[0] + "@***")

# Session timeout configuration (180 seconds of inactivity)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=180)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# Extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager.init_app(app)
mail.init_app(app)
csrf = CSRFProtect(app)

# Uploads
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Session config
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=3)
app.config["SESSION_REFRESH_EACH_REQUEST"] = True

import models  # noqa: E402

# Default accounts 
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User.query.filter_by(username="215030").first()
    if not admin:
        admin = User(
            username="215030", full_name="System Administrator", email="admin@helpticketsystem.com",
            password_hash=generate_password_hash("admin123"), role="admin", is_active=True, is_verified=True, is_approved=True,
        )
        db.session.add(admin)
        db.session.commit()
        logging.info("Default admin created")

    intern = User.query.filter_by(username="dctraining").first()
    if not intern:
        intern = User(
            username="dctraining", full_name="Dctraining",
            email="intern@helpticketsystem.com", password_hash=generate_password_hash("Dctraining2023"), 
            role="intern", is_active=True, is_verified=True, is_approved=True,
        )
        db.session.add(intern)
        db.session.commit()
        logging.info("Default intern created")


login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


<<<<<<< HEAD
=======
# NOTE: we set a 180s inactivity timeout per user's request.
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=180)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# Inject commonly-used values into templates
>>>>>>> 2b2960b6d0f09592acbb079b768fe160d07c507f
@app.context_processor
def inject_now():
    return {
        "now": datetime.utcnow,
        "TOAST_AUTOCLOSE_MS": int(os.environ.get("TOAST_AUTOCLOSE_MS", 5000)),
        "SESSION_EXPIRY_TOAST_CLASS": os.environ.get("SESSION_EXPIRY_TOAST_CLASS", "text-bg-warning"),
        "SESSION_EXPIRY_REDIRECT_MS": int(os.environ.get("SESSION_EXPIRY_REDIRECT_MS", 1500)),
    }

@app.before_request
def enforce_session_timeout():
    if current_user.is_authenticated:
        now = datetime.utcnow()
        last = session.get("last_activity")

        if last:
            try:
                last_dt = datetime.fromisoformat(last)
            except Exception:
                last_dt = now

            if now - last_dt > app.permanent_session_lifetime:
                logout_user()
                session.clear()
                flash("Session expired due to inactivity. Please log in again.", "warning")
                return redirect(url_for("login"))

        session["last_activity"] = now.isoformat()

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

import routes  # noqa: E402

from cli_commands import cli as sms_cli
app.cli.add_command(sms_cli, name="sms")
