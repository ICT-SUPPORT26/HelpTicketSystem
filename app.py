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
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "mysql+pymysql://root:@localhost:3306/helpticket_system")
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

login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Auto logout after inactivity: use a timedelta for the session lifetime and
# track last activity timestamp in the session to enforce inactivity logout.
# NOTE: we set a 3 minute inactivity timeout per user's request.
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=3)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}


@app.before_request
def enforce_session_timeout():
    # Only enforce inactivity timeout for authenticated users. We store a
    # `last_activity` ISO timestamp in the session and compare it to the
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
