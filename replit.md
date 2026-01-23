# Help Ticket System

## Overview
A Flask-based help ticket management system for tracking and resolving support requests. Features user authentication, ticket creation/management, and SMS notifications.

## Project Structure
- `main.py` - Application entry point (runs Flask on 0.0.0.0:5000)
- `app.py` - Flask application configuration and initialization
- `models.py` - SQLAlchemy database models (User, Ticket, etc.)
- `routes.py` - Main application routes and views
- `routes_reports_addon.py` - Additional reporting routes
- `forms.py` - WTForms form definitions
- `extensions.py` - Flask extensions (db, login_manager, mail)
- `utils.py` - Utility functions
- `notification_utils.py` - Notification helpers
- `sms_service.py` - SMS integration service
- `background_tasks.py` - Background task processing
- `cli_commands.py` - Flask CLI commands
- `templates/` - Jinja2 HTML templates
- `static/` - Static assets (CSS, JS, images)
- `uploads/` - User uploaded files

## Tech Stack
- **Backend**: Python 3.11, Flask 3.x
- **Database**: PostgreSQL (via SQLAlchemy)
- **Auth**: Flask-Login
- **Forms**: Flask-WTF / WTForms
- **WSGI**: Gunicorn (production)

## Database
Uses PostgreSQL via the `DATABASE_URL` environment variable provided by Replit.

## Running the App
The app runs on port 5000 via the Flask development server:
```bash
python main.py
```

For production, use gunicorn:
```bash
gunicorn --bind 0.0.0.0:5000 app:app
```

## Default Accounts
- Admin: username=`215030`, password=`admin123`
- Intern: username=`dctraining`, password=`Dctraining2023`

## Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `SESSION_SECRET` - Flask session secret key
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD` - Email settings
- `MOVESMS_USERNAME`, `MOVESMS_APIKEY`, `MOVESMS_SENDER_ID` - SMS service config

## Recent Changes
- 2026-01-23: Implemented role-based ticket workflow:
  - Admin: Can assign technicians, set priority, category optional (unclassified by default)
  - Technician (intern): Cannot edit priority, must select category when resolving ticket
  - Category required when status = "Resolved" and locked after closure
  - Added category history logging
- 2026-01-23: Initial import and Replit environment setup
