#!/usr/bin/env python
"""Run database migration to create access_log table."""
from app import app, db
from flask_migrate import Migrate, upgrade

# Initialize migrate (already in app.py but ensure here)
migrate = Migrate(app, db)

with app.app_context():
    try:
        upgrade()
        print("✓ Migration applied successfully")
    except Exception as e:
        print(f"✗ Migration error: {e}")
