# ICT Helpdesk System

A modern web-based helpdesk ticketing system for ICT support, built with Flask, SQLAlchemy, Flask-Login, Flask-Mail, and MySQL.

## Features
- User registration with email verification
- Secure login/logout
- Role-based dashboards (Admin, Intern, User)
- Ticket creation, assignment, and status tracking
- File attachments for tickets
- Comments (internal and public)
- Category management (Admin)
- User management (Admin)
- Dynamic dashboard statistics
- Responsive, modern UI (Bootstrap 5)
- Timezone-aware (Africa/Nairobi)

## Requirements
- Python 3.10+
- MySQL Server
- Flask, Flask-Login, Flask-Mail, Flask-WTF, SQLAlchemy, WTForms, pytz, and other dependencies (see below)

## Setup Instructions

1. **Clone the repository**
   ```sh
   git clone <your-repo-url>
   cd HelpTicketSystem
   ```

2. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```
   If `requirements.txt` is missing, install manually:
   ```sh
   pip install flask flask-login flask-mail flask-wtf sqlalchemy pymysql wtforms pytz
   ```

3. **Configure database**
   - Create a database named `helpticket_system` (or use your own database name).
   - You can provide a full SQLAlchemy URL via `DATABASE_URL`, for example:
     - MySQL: `mysql+pymysql://user:password@127.0.0.1:3306/helpticket_system`
     - PostgreSQL: `postgresql+psycopg2://user:password@127.0.0.1:5432/helpticket_system`
   - Or provide components (the app will construct the URL): `DB_ENGINE` (`mysql` or `postgres`), `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`.
     - If `DB_NAME` is not set, the app defaults to `helpticket_system` for MySQL and `helpticket_system_pg` for PostgreSQL.
   - Update the `SQLALCHEMY_DATABASE_URI` in `app.py` only if you need to hard-code a value.

4. **Set environment variables (optional, for mail)**
   - `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`

5. **Run the app**
   ```sh
   python app.py
   ```
   The app will auto-create tables and a default admin user (`admin`/`admin123`) if not present.

6. **Access the app**
   - Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Deployment
- For production, use a WSGI server like Waitress or Gunicorn.
- Example (Waitress):
  ```sh
  pip install waitress
  waitress-serve --port=5000 app:app
  ```

## Folder Structure
- `app.py` - Main Flask app and setup
- `routes.py` - All route logic
- `models.py` - SQLAlchemy models
- `forms.py` - WTForms forms
- `templates/` - Jinja2 HTML templates
- `static/` - CSS and JS
- `uploads/` - File uploads

## Default Admin
- Username: `admin`
- Password: `admin123`

## License
MIT License

---
For any issues, open an issue or pull request on GitHub.
